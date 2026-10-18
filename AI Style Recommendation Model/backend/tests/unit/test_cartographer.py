import pandas as pd
import pytest

from style_recommendation.schemas.models import RequirementResponse
from test_support import make_ranking as RankingService


def rows():
    return pd.DataFrame([
        dict(product_id=str(i), article_type="Shirt", base_colour="Red" if i < 7 else "Blue",
             occasion="Office", style="Formal", material="Cotton", price=1000,
             description="", gender="Women", available_sizes=["M"])
        for i in range(9)
    ])


def test_rerank_preserves_all_results_groups_and_match_scores(monkeypatch):
    from test_support import cartographer_service

    monkeypatch.setattr(cartographer_service, "score", lambda query, products: [float(p.product_id) for p in products])
    service = RankingService()
    req = RequirementResponse(article_types=["Shirt"], preferred_colors=["Red"])
    baseline, _ = service.calculate_groups(rows(), req, "M")
    exact, alternatives = service.calculate_groups(rows(), req, "M", query="red shirt for office")
    assert [p.product_id for p in exact] == ["6", "5", "4", "3", "2", "1", "0"]
    assert [p.product_id for p in alternatives] == ["8", "7"]
    assert exact[0].match_score == baseline[0].match_score
    assert exact[0].reranker_score == 6.0
    assert all(p.unmatched_requirements == ["colour"] for p in alternatives)


def test_unavailable_ranker_preserves_existing_results(monkeypatch):
    from test_support import cartographer_service

    monkeypatch.setattr(cartographer_service, "score", lambda *args: None)
    service = RankingService()
    req = RequirementResponse(article_types=["Shirt"])
    assert service.calculate_groups(rows(), req, "M", query="shirt") == service.calculate_groups(rows(), req, "M")


def test_missing_model_falls_back_without_downloading(tmp_path, caplog):
    from style_recommendation.inference.cartographer_service import CartographerService

    service = CartographerService(model_path=tmp_path, enabled=True)
    products = RankingService().calculate_groups(rows(), RequirementResponse(), "M")[0]
    assert service.score("shirt", products) is None
    assert "fallback" in caplog.text.lower()


@pytest.mark.parametrize("scores", [[float("nan")], [float("inf")], []])
def test_invalid_model_output_falls_back(monkeypatch, scores):
    from style_recommendation.inference.cartographer_service import CartographerService

    service = CartographerService(enabled=True)
    monkeypatch.setattr(service, "_predict", lambda *args: scores)
    products = RankingService().calculate_groups(rows().head(1), RequirementResponse(), "M")[0]
    assert service.score("shirt", products) is None


def test_product_text_uses_attributes_and_omits_unknowns():
    from style_recommendation.inference.cartographer_service import CartographerService

    products = RankingService().calculate_groups(rows().head(1), RequirementResponse(), "M")[0]
    text = CartographerService.product_text(products[0])
    assert all(word in text for word in ["Red", "Cotton", "Shirt", "Office"])
    assert "nan" not in text and "None" not in text


def test_disabled_ranker_does_not_run_inference(monkeypatch):
    from style_recommendation.inference.cartographer_service import CartographerService

    service = CartographerService(enabled=False)
    def unexpected(*args):
        pytest.fail("Disabled ranker attempted inference")
    monkeypatch.setattr(service, "_predict", unexpected)
    products = RankingService().calculate_groups(rows().head(1), RequirementResponse(), "M")[0]
    assert service.score("shirt", products) is None


def test_endpoint_uses_original_query_for_ranking(monkeypatch):
    import asyncio
    from test_support import api
    from style_recommendation.schemas.models import RecommendationRequest
    from test_support import cartographer_service

    async def extract(_):
        return {"article_types": ["Shirt"], "preferred_colors": ["Red"]}
    query = "red shirt for an office presentation"
    monkeypatch.setattr(api.qwen_service, "analyze_requirements", extract)
    monkeypatch.setattr(api.product_service, "get_all_products", rows)
    monkeypatch.setattr(api, "_export_results_to_json", lambda *args: None)
    monkeypatch.setattr(cartographer_service, "score", lambda q, products:
                        [float(p.product_id) if q == query else 0.0 for p in products])
    response = asyncio.run(api.get_recommendations(RecommendationRequest(
        gender="Women", size="M", requirements=query)))
    assert response.recommendations[0].product_id == "6"
    assert response.recommendations[0].reranker_score == 6.0
