import asyncio
import io

import pandas as pd
import pytest
from rich.console import Console

from style_recommendation.schemas.models import RecommendationRequest, RequirementResponse
from test_support import ranking_service
from test_support import recommendation_service


def product(pid, colour="Red", article="Shirt", occasion="Office", **extra):
    return dict(product_id=pid, base_colour=colour, article_type=article,
                occasion=occasion, gender="Women", available_sizes=["M"],
                price=1000, style="Formal", description="", **extra)


def groups(rows, **preferences):
    return ranking_service.calculate_groups(pd.DataFrame(rows), RequirementResponse(**preferences), "M")


@pytest.mark.parametrize("occasion", ["Office", "office wear", "workwear", "work", "office meeting"])
def test_office_requests_include_formal_and_smart_casual(occasion):
    rows = [product("formal", occasion="Formal"),
            product("smart", occasion="Casual/Smart Casual"),
            product("casual", occasion="Casual"), product("party", occasion="Party")]
    req = RequirementResponse(article_types=["Shirt"], occasion=[occasion])
    candidates = recommendation_service.generate_candidates(pd.DataFrame(rows), "Women", "M", req)
    exact, alternatives = ranking_service.calculate_groups(candidates, req, "M")
    assert {p.product_id for p in exact} == {"formal", "smart"}
    assert alternatives == []
    assert all(not p.unmatched_requirements for p in exact)
    assert ranking_service._score_occasion("Casual/Smart Casual", [occasion]) == 1.0


@pytest.mark.parametrize("occasion, expected", [("Formal", {"formal"}), ("Smart Casual", {"smart"})])
def test_explicit_dress_codes_remain_specific(occasion, expected):
    exact, alternatives = groups([
        product("formal", occasion="Formal"),
        product("smart", occasion="Casual/Smart Casual"),
        product("casual", occasion="Casual"),
    ], occasion=[occasion])
    assert {p.product_id for p in exact} == expected
    assert alternatives == []


def test_red_office_shirts_are_separate_from_partial_matches():
    exact, alternatives = groups([
        product("exact"), product("blue", colour="Blue"),
        product("party", occasion="Party"), product("top", article="Top"),
        product("tshirt", article="T-Shirt"), product("sweatshirt", article="Sweatshirt"),
    ], preferred_colors=["Red"], article_types=["Shirt"], occasion=["office wear"])
    assert [p.product_id for p in exact] == ["exact"]
    by_id = {p.product_id: p for p in alternatives}
    assert by_id["blue"].unmatched_requirements == ["colour"]
    assert set(by_id) == {"blue"}
    assert all(p.match_category == "alternative" for p in alternatives)
    assert exact[0].match_category == "exact"


def test_colour_only_exact_matches_are_not_dropped_by_score_threshold():
    exact, alternatives = groups([product("red"), product("blue", colour="Blue")], preferred_colors=["Red"])
    assert [p.product_id for p in exact] == ["red"]
    assert alternatives == []


def test_related_colour_shades_are_primary_matches():
    exact, alternatives = groups([product("navy", colour="Navy Blue")], preferred_colors=["Blue"])
    assert [p.product_id for p in exact] == ["navy"]
    assert exact[0].colour_match == "shade"
    assert alternatives == []


def test_all_matching_colours_are_returned_in_separate_groups():
    rows = [product(f"blue-{i}", colour="Blue") for i in range(8)] + [product("red")]
    exact, alternatives = groups(rows, preferred_colors=["Red"], article_types=["Shirt"], occasion=["Office"])
    assert [p.product_id for p in exact] == ["red"]
    assert len(alternatives) == 8
    assert not ({p.product_id for p in exact} & {p.product_id for p in alternatives})


def test_missing_attributes_do_not_count_as_exact_matches():
    exact, alternatives = groups([product("missing", colour=float("nan"))],
                                preferred_colors=["Red"], article_types=["Shirt"])
    assert exact == []
    assert alternatives[0].unmatched_requirements == []
    assert alternatives[0].unverified_requirements == ["colour"]


def test_unspecified_fields_do_not_restrict_results_and_aliases_are_normalized():
    exact, _ = groups([product("trousers", colour="Grey", article="Trousers", occasion="Formal, Casual")],
                      preferred_colors=["gray"], article_types=["Pants"], occasion=["Office"])
    assert [p.product_id for p in exact] == ["trousers"]
    exact, _ = groups([product("one"), product("two", colour="Blue")], article_types=["Shirt"])
    assert {p.product_id for p in exact} == {"one", "two"}


def test_both_groups_preserve_gender_size_and_budget_constraints():
    rows = [product("ok"), product("too-expensive"), product("wrong-size"), product("wrong-gender")]
    rows[1]["price"] = 2000
    rows[2]["available_sizes"] = ["S"]
    rows[3]["gender"] = "Men"
    req = RequirementResponse(preferred_colors=["Red"], price_preference={"max": 1200})
    candidates = recommendation_service.generate_candidates(pd.DataFrame(rows), "Women", "M", req)
    exact, alternatives = ranking_service.calculate_groups(candidates, req, "M")
    assert [p.product_id for p in exact] == ["ok"]
    assert alternatives == []


@pytest.mark.parametrize("price, expected_exact", [(1000, ["exact"]), (2000, [])])
def test_endpoint_returns_separate_groups_without_relaxing_budget(monkeypatch, price, expected_exact):
    from test_support import api
    from style_recommendation.services.terminal_progress import PipelineProgress

    displays = []

    def progress(label, total_stages):
        display = PipelineProgress(label, total_stages, console=Console(file=io.StringIO()))
        displays.append(display)
        return display

    monkeypatch.setattr(api, "PipelineProgress", progress)

    async def extract(_):
        return {"preferred_colors": ["Red"], "article_types": ["Shirt"], "occasion": ["Office"],
                "price_preference": {"max": 1200}}

    rows = [product("exact"), product("blue", colour="Blue")]
    for row in rows:
        row["price"] = price
    monkeypatch.setattr(api.qwen_service, "analyze_requirements", extract)
    monkeypatch.setattr(api.product_service, "get_all_products", lambda: pd.DataFrame(rows))
    monkeypatch.setattr(api, "_export_results_to_json", lambda *args: None)
    response = asyncio.run(api.get_recommendations(RecommendationRequest(
        gender="Women", size="M", requirements="red shirt for office under 1200")))
    for display in displays:
        display.close()
    assert [p.product_id for p in response.recommendations] == expected_exact
    assert [p.product_id for p in response.alternatives] == (["blue"] if expected_exact else [])
    if not expected_exact:
        assert response.total_candidates == 0
