import numpy as np
import pandas as pd
import pytest
from PIL import Image

from app.schemas.models import RequirementResponse
from app.services.ranking_service import RankingService


def products():
    return pd.DataFrame([
        dict(product_id=str(i), article_type="Shirt", base_colour="Red" if i < 7 else "Blue",
             occasion="Office", style="Formal", price=1000, image_path=f"Images/{i}.png")
        for i in range(9)
    ])


def test_visual_ranking_selects_before_top_five_and_keeps_metadata_groups(monkeypatch):
    from app.services.fashionclip_service import fashionclip_service
    from app.services.cartographer_service import cartographer_service

    monkeypatch.setattr(fashionclip_service, "score", lambda q, ps: [int(p.product_id) / 10 for p in ps])
    monkeypatch.setattr(cartographer_service, "score", lambda *args: pytest.fail("Visual ranking available"))
    req = RequirementResponse(article_types=["Shirt"], preferred_colors=["Red"])
    exact, alternatives = RankingService().calculate_groups(products(), req, "M", "red office shirt")
    assert [p.product_id for p in exact] == ["6", "5", "4", "3", "2"]
    assert [p.product_id for p in alternatives] == ["8", "7"]
    assert exact[0].visual_score == pytest.approx(0.6)
    assert exact[0].reranker_score is None
    assert alternatives[0].unmatched_requirements == ["colour"]


def test_missing_image_scores_do_not_outweigh_negative_visual_scores(monkeypatch):
    from app.services.fashionclip_service import fashionclip_service

    monkeypatch.setattr(fashionclip_service, "score", lambda q, ps: [None, -0.2, -0.1])
    exact, _ = RankingService().calculate_groups(products().head(3), RequirementResponse(), "M", "shirt")
    assert [p.product_id for p in exact] == ["2", "1", "0"]


def test_visual_failure_falls_back_to_cartographer(monkeypatch):
    from app.services.fashionclip_service import fashionclip_service
    from app.services.cartographer_service import cartographer_service

    monkeypatch.setattr(fashionclip_service, "score", lambda *args: None)
    monkeypatch.setattr(cartographer_service, "score", lambda q, ps: [0.1, 0.9])
    exact, _ = RankingService().calculate_groups(products().head(2), RequirementResponse(), "M", "shirt")
    assert exact[0].product_id == "1"
    assert exact[0].visual_score is None
    assert exact[0].reranker_score == 0.9


def test_local_images_scored_and_cached_across_service_instances(tmp_path, monkeypatch):
    from app.services.fashionclip_service import FashionClipService

    image_dir = tmp_path / "images"
    image_dir.mkdir()
    Image.new("RGB", (10, 10), "red").save(image_dir / "0.png")
    (image_dir / "1.png").write_text("not an image")
    ps = RankingService().calculate_groups(products().head(3), RequirementResponse(), "M")[0]
    service = FashionClipService(image_dir=image_dir, cache_dir=tmp_path / "cache", enabled=True)
    monkeypatch.setattr(service, "_load", lambda: None)
    monkeypatch.setattr(service, "_encode_text", lambda q: np.array([1.0, 0.0]))
    calls = []
    def encode(images):
        calls.append(len(images))
        return np.array([[1.0, 0.0] for _ in images])
    monkeypatch.setattr(service, "_encode_images", encode)
    assert service.score("red shirt", ps) == [1.0, None, None]
    assert service.score("red shirt", ps) == [1.0, None, None]
    assert calls == [1]
    # A fresh process/service should use the disk cache as well.
    other = FashionClipService(image_dir=image_dir, cache_dir=tmp_path / "cache", enabled=True)
    monkeypatch.setattr(other, "_load", lambda: None)
    monkeypatch.setattr(other, "_encode_text", lambda q: np.array([1.0, 0.0]))
    monkeypatch.setattr(other, "_encode_images", lambda _: pytest.fail("Cache was not reused"))
    assert other.score("red shirt", ps) == [1.0, None, None]
    Image.new("RGB", (20, 20), "blue").save(image_dir / "0.png")
    assert service.score("shirt", ps) == [1.0, None, None]
    assert calls == [1, 1]


def test_paths_outside_image_directory_are_not_read(tmp_path):
    from app.services.fashionclip_service import FashionClipService

    service = FashionClipService(image_dir=tmp_path / "images", enabled=True)
    assert service.resolve_image("../private.png") is None
    assert service.resolve_image(str(tmp_path / "private.png")) is None
    assert service.resolve_image("https://example.com/photo.jpg") is None


def test_missing_model_returns_fallback(tmp_path, caplog):
    from app.services.fashionclip_service import FashionClipService

    Image.new("RGB", (10, 10)).save(tmp_path / "0.png")
    service = FashionClipService(model_path=tmp_path / "model", image_dir=tmp_path, enabled=True)
    ps = RankingService().calculate_groups(products().head(1), RequirementResponse(), "M")[0]
    assert service.score("shirt", ps) is None
    assert "fallback" in caplog.text.lower()


def test_visual_ranking_never_reintroduces_filtered_products(monkeypatch):
    from app.services.fashionclip_service import fashionclip_service
    from app.services.recommendation_service import recommendation_service

    frame = products().head(4)
    frame["gender"] = ["Women", "Men", "Women", "Women"]
    frame["available_sizes"] = [["M"], ["M"], ["S"], ["M"]]
    frame["price"] = [1000, 1000, 1000, 5000]
    req = RequirementResponse(article_types=["Shirt"], price_preference={"max": 1200})
    filtered = recommendation_service.generate_candidates(frame, "Women", "M", req)
    monkeypatch.setattr(fashionclip_service, "score", lambda q, ps: [0.5 for _ in ps])
    exact, alternatives = RankingService().calculate_groups(filtered, req, "M", "shirt under 1200")
    assert [p.product_id for p in exact] == ["0"]
    assert alternatives == []


def test_endpoint_passes_original_text_to_visual_ranking(monkeypatch):
    import asyncio
    from app.api import recommendations as api
    from app.schemas.models import RecommendationRequest
    from app.services.fashionclip_service import fashionclip_service

    query = "red shirt with a subtle office look"
    async def extract(_):
        return {"article_types": ["Shirt"], "preferred_colors": ["Red"]}
    frame = products()
    frame["gender"] = "Women"
    frame["available_sizes"] = [["M"] for _ in range(len(frame))]
    monkeypatch.setattr(api.qwen_service, "analyze_requirements", extract)
    monkeypatch.setattr(api.product_service, "get_all_products", lambda: frame)
    monkeypatch.setattr(api, "_export_results_to_json", lambda *args: None)
    monkeypatch.setattr(fashionclip_service, "score", lambda q, ps:
                        [int(p.product_id) / 10 if q == query else 0 for p in ps])
    response = asyncio.run(api.get_recommendations(RecommendationRequest(
        gender="Women", size="M", requirements=query)))
    assert response.recommendations[0].product_id == "6"
    assert response.recommendations[0].visual_score == pytest.approx(0.6)


def test_worker_eof_returns_fallback(tmp_path, monkeypatch):
    from app.services.fashionclip_service import FashionClipService

    Image.new("RGB", (10, 10)).save(tmp_path / "0.png")
    service = FashionClipService(image_dir=tmp_path, enabled=True)
    monkeypatch.setattr(service, "_load", lambda: None)
    def crash(_):
        raise EOFError("worker stopped")
    monkeypatch.setattr(service, "_encode_text", crash)
    ps = RankingService().calculate_groups(products().head(1), RequirementResponse(), "M")[0]
    assert service.score("shirt", ps) is None
    assert service.score("shirt", ps) is None
