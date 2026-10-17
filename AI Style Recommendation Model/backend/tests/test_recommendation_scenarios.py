import pandas as pd
import pytest

from app.schemas.models import RequirementResponse
from app.services.ranking_service import ranking_service
from app.services.recommendation_service import recommendation_service


def product(pid, colour="Blue", occasion="Wedding", article="Dress"):
    return dict(product_id=pid, article_type=article, base_colour=colour,
                occasion=occasion, gender="Women", available_sizes=["M"], price=1000,
                style="", description="")


def rank(rows, **preferences):
    req = RequirementResponse(**preferences)
    candidates = recommendation_service.generate_candidates(pd.DataFrame(rows), "Women", "M", req)
    return ranking_service.calculate_groups(candidates, req, "M")


def test_occasion_type_colour_only_relaxes_colour():
    primary, similar = rank([
        product("red", "Red"), product("pink", "Pink"),
        product("party", "Red", "Party"), product("shirt", "Red", article="Shirt"),
        product("unknown-type", "Red", article=None), product("unknown-occasion", "Red", None),
    ], article_types=["Dress"], preferred_colors=["Red"], occasion=["Wedding"])
    assert [p.product_id for p in primary] == ["red"]
    assert [p.product_id for p in similar] == ["pink"]


def test_missing_colour_keeps_every_available_colour():
    colours = ["Red", "Blue", "Green", "Pink", "Black", "White", "Purple"]
    primary, similar = rank([product(c, c) for c in colours] + [product("wrong", occasion="Party")],
                            article_types=["Dress"], occasion=["Wedding"])
    assert {p.base_colour for p in primary} == set(colours)
    assert len({p.match_score for p in primary}) == 1
    assert similar == []


def test_missing_occasion_keeps_every_category_beyond_old_top_five_limit():
    rows = [product(f"wedding-{i}") for i in range(7)]
    rows += [product(o, occasion=o) for o in ["Party", "Casual", "Formal"]]
    primary, _ = rank(rows, article_types=["Dress"], preferred_colors=["Blue"])
    assert len(primary) == 10
    assert {p.occasion for p in primary} == {"Wedding", "Party", "Casual", "Formal"}


@pytest.mark.parametrize("shade", ["Light Blue", "Dark Blue", "Navy Blue", "Sky Blue", "Royal Blue", "Navy"])
def test_blue_shades_are_primary_but_unrelated_colours_are_separate(shade):
    primary, similar = rank([product("shade", shade), product("exact"), product("red", "Red")],
                            article_types=["Dress"], preferred_colors=["Blue"])
    assert [p.product_id for p in primary] == ["exact", "shade"]
    assert primary[1].colour_match == "shade"
    assert [p.product_id for p in similar] == ["red"]


@pytest.mark.parametrize("ranker", ["fashionclip_service", "cartographer_service"])
def test_ai_scores_cannot_promote_shades_above_exact_colours(monkeypatch, ranker):
    import app.services.ranking_service as module
    monkeypatch.setattr(module.fashionclip_service, "score", lambda *args: None)
    monkeypatch.setattr(module.cartographer_service, "score", lambda *args: None)
    monkeypatch.setattr(getattr(module, ranker), "score",
                        lambda q, ps: [100 if p.base_colour != "Blue" else -1 for p in ps])
    req = RequirementResponse(article_types=["Dress"], preferred_colors=["Blue"])
    primary, _ = ranking_service.calculate_groups(
        pd.DataFrame([product("shade", "Navy Blue"), product("exact")]), req, "M", "blue dress")
    assert [p.product_id for p in primary] == ["exact", "shade"]


def test_specific_shade_is_not_broadened_to_other_shades():
    primary, similar = rank([product("navy", "Navy"), product("sky", "Sky Blue"), product("blue")],
                            article_types=["Dress"], preferred_colors=["Navy Blue"])
    assert [p.product_id for p in primary] == ["navy"]
    assert {p.product_id for p in similar} == {"sky", "blue"}


def test_aliases_and_multiple_occasion_values_are_supported():
    primary, _ = rank([product("pants", "Grey", "Casual; Formal", "Trousers")],
                      article_types=["Pants"], preferred_colors=["Gray"], occasion=["Office"])
    assert [p.product_id for p in primary] == ["pants"]


def test_no_eligible_type_or_occasion_does_not_fall_back():
    primary, similar = rank([product("wrong-type", article="Shirt"), product("wrong-occasion", occasion="Party")],
                            article_types=["Dress"], occasion=["Wedding"])
    assert primary == similar == []


def test_compound_occasions_match_each_explicit_category():
    primary, _ = rank([product("both", occasion="Party and Wedding")],
                      article_types=["Dress"], occasion=["Wedding"])
    assert [p.product_id for p in primary] == ["both"]


def test_unknown_occasion_placeholder_is_not_split_into_categories():
    assert recommendation_service.occasion_values("N/A") == set()


def test_generic_lehenga_includes_catalogue_variants_but_not_other_types():
    primary, similar = rank([
        product("yellow", "Yellow", article="Lehenga Choli Set"),
        product("choli", "Yellow", article="Lehenga Choli"),
        product("set", "Yellow", article="Lehenga Set"),
        product("pink", "Pink", article="Lehenga"),
        product("unrelated", "Yellow", article="Sharara Set"),
    ], article_types=["Lehenga"], preferred_colors=["Yellow"])
    assert {p.product_id for p in primary} == {"yellow", "choli", "set"}
    assert all(not p.unmatched_requirements for p in primary)
    assert [p.product_id for p in similar] == ["pink"]


def test_specific_lehenga_variant_is_not_broadened_to_every_lehenga():
    primary, similar = rank([
        product("skirt", "Yellow", article="Lehenga Skirt"),
        product("set", "Yellow", article="Lehenga Choli Set"),
    ], article_types=["Lehenga Skirt"], preferred_colors=["Yellow"])
    assert [p.product_id for p in primary] == ["skirt"]
    assert similar == []


@pytest.mark.parametrize("size", ["S", "M", "L", "XL"])
def test_real_catalog_yellow_lehenga_is_primary(size):
    from app.services.product_service import product_service
    req = RequirementResponse(article_types=["Lehenga"], preferred_colors=["Yellow"])
    candidates = recommendation_service.generate_candidates(product_service.get_all_products(), "Female", size, req)
    primary, similar = ranking_service.calculate_groups(candidates, req, size)
    assert "P728" in {p.product_id for p in primary}
    assert all(p.colour_match in {"exact", "shade"} for p in primary)
    assert "P963" in {p.product_id for p in similar}


@pytest.mark.parametrize("colour", ["Blue and Green", "Black Blue", "Red Blue Plaid", "Grey-Blue"])
def test_multicolour_items_are_not_treated_as_blue_shades(colour):
    primary, similar = rank([product("multi", colour)], article_types=["Dress"], preferred_colors=["Blue"])
    assert primary == []
    assert [p.product_id for p in similar] == ["multi"]


@pytest.mark.parametrize("occasion", [None, [], [" "], ""])
def test_endpoint_preserves_missing_occasion_as_null(monkeypatch, occasion):
    import asyncio
    import io
    from rich.console import Console
    from app.api import recommendations as api
    from app.schemas.models import RecommendationRequest
    from app.services.terminal_progress import PipelineProgress

    async def extract(_):
        return {"article_types": ["Dress"], "preferred_colors": ["Blue"], "occasion": occasion}

    displays = []
    def progress(label, total_stages):
        display = PipelineProgress(label, total_stages, console=Console(file=io.StringIO()))
        displays.append(display)
        return display

    monkeypatch.setattr(api, "PipelineProgress", progress)
    monkeypatch.setattr(api.qwen_service, "analyze_requirements", extract)
    monkeypatch.setattr(api.product_service, "get_all_products", lambda: pd.DataFrame([
        product("wedding"), product("party", occasion="Party"), product("shade", "Navy Blue"),
        product("red", "Red"), product("shirt", article="Shirt"),
    ]))
    monkeypatch.setattr(api, "_export_results_to_json", lambda *args: None)
    try:
        response = asyncio.run(api.get_recommendations(RecommendationRequest(
            gender="Women", size="M", requirements="blue dress")))
    finally:
        for display in displays:
            display.close()
    assert response.occasion_used is None
    assert [p.product_id for p in response.recommendations] == ["wedding", "party", "shade"]
    assert [p.product_id for p in response.alternatives] == ["red"]
    assert response.total_candidates == 4
