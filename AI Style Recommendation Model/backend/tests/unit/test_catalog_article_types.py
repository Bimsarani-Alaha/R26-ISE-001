import pandas as pd

from style_recommendation.schemas.models import RequirementResponse
from test_support import ProductService
from test_support import ranking_service
from test_support import recommendation_service


def test_generic_top_is_normalized_only_when_description_identifies_a_shirt():
    service = ProductService()
    df = pd.DataFrame([
        {"article_type": "Top", "description": "Red long sleeve button front shirt with chest pocket"},
        {"article_type": "Top", "description": "Black short sleeve t-shirt"},
        {"article_type": "Top", "description": "Grey shirt jacket with chest pockets"},
        {"article_type": "Top", "description": "White sleeveless top"},
        {"article_type": "Dress", "description": "Red shirt dress"},
    ])
    service._normalize_article_types(df)
    assert df["article_type"].tolist() == ["Shirt", "Top", "Top", "Top", "Dress"]


def test_real_catalog_red_office_shirt_is_an_exact_match():
    service = ProductService()
    df = service.load_dataset()
    req = RequirementResponse(preferred_colors=["Red"], article_types=["Shirt"], occasion=["Office"])
    candidates = recommendation_service.generate_candidates(df, "Male", "M", req)
    exact, alternatives = ranking_service.calculate_groups(candidates, req, "M")
    assert "P313" in {p.product_id for p in exact}
    assert all(p.colour_match in {"exact", "shade"} and p.article_type == "Shirt" for p in exact)
    assert exact[0].base_colour == "Red"
    assert "P313" not in {p.product_id for p in alternatives}
