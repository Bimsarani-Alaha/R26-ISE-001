import asyncio
import io

import pandas as pd
import pytest
from rich.console import Console

from style_recommendation.schemas.models import RecommendationRequest, RequirementResponse
from test_support import ranking_service
from test_support import recommendation_service


def record(**changes):
    row = dict(product_id="P-test", gender="Women", available_sizes=["M"],
               price=1000, article_type="Shirt", base_colour="Red", occasion="Office",
               style="Formal", material="Cotton", pattern="Striped",
               sleeve_type="Full Sleeve", neck_type="Collar Neck", description="")
    return {**row, **changes}


def rank(row, **preferences):
    return ranking_service.calculate_groups(
        pd.DataFrame([row]), RequirementResponse(**preferences), "M")


@pytest.mark.parametrize("field,column,label,wanted,actual", [
    ("materials", "material", "material", "Cotton", "Cotton Blend"),
    ("patterns", "pattern", "pattern", "Striped", "Solid"),
    ("sleeve_types", "sleeve_type", "sleeve type", "Full Sleeve", "Short Sleeve"),
    ("neck_types", "neck_type", "neckline", "Collar Neck", "Round Neck"),
    ("style_preferences", "style", "style", "Formal", "Semi-Formal"),
])
def test_known_attribute_difference_prevents_exact(field, column, label, wanted, actual):
    exact, alternatives = rank(record(**{column: actual}),
                               article_types=["Shirt"], **{field: [wanted]})
    assert exact == []
    assert alternatives[0].unmatched_requirements == [label]
    assert alternatives[0].unverified_requirements == []


@pytest.mark.parametrize("value", [None, float("nan"), "", "  ", "Unknown", "N/A"])
def test_missing_material_is_unverified_not_a_known_difference(value):
    exact, alternatives = rank(record(material=value), article_types=["Shirt"], materials=["Cotton"])
    assert exact == []
    assert alternatives[0].unmatched_requirements == []
    assert alternatives[0].unverified_requirements == ["material"]
    assert "Not verified: material" in alternatives[0].explanation


def test_free_text_needs_are_unverified_even_if_description_repeats_them():
    exact, alternatives = rank(record(description="machine washable"),
                               article_types=["Shirt"], other_requirements=["machine washable"])
    assert exact == []
    assert alternatives[0].unverified_requirements == ["machine washable"]


def test_options_aliases_and_unspecified_fields_remain_supported():
    exact, _ = rank(record(base_colour="Grey", material="Silk", pattern=None),
                    preferred_colors=["gray"], materials=["Cotton", "silk"])
    assert len(exact) == 1
    assert exact[0].unverified_requirements == []


def test_all_attributes_satisfied_is_exact():
    exact, alternatives = rank(record(), preferred_colors=["Red"], article_types=["Shirt"],
                               occasion=["Office"], style_preferences=["Formal"], materials=["Cotton"],
                               patterns=["Striped"], sleeve_types=["Full Sleeve"], neck_types=["Collar Neck"])
    assert len(exact) == 1
    assert alternatives == []


def test_both_evidence_lists_are_returned_without_relaxing_eligibility():
    req = RequirementResponse(article_types=["Shirt"], materials=["Cotton"],
                              other_requirements=["machine washable"], price_preference={"max": 1200})
    rows = [record(material="Polyester"), record(product_id="expensive", price=2000),
            record(product_id="size", available_sizes=["S"]), record(product_id="gender", gender="Men")]
    candidates = recommendation_service.generate_candidates(pd.DataFrame(rows), "Women", "M", req)
    exact, alternatives = ranking_service.calculate_groups(candidates, req, "M")
    assert exact == []
    assert [p.product_id for p in alternatives] == ["P-test"]
    assert alternatives[0].unmatched_requirements == ["material"]
    assert alternatives[0].unverified_requirements == ["machine washable"]


def test_endpoint_and_export_preserve_unverified_evidence(monkeypatch, tmp_path):
    from test_support import api
    from style_recommendation.services.terminal_progress import PipelineProgress
    displays = []
    def progress(label, total_stages):
        display = PipelineProgress(label, total_stages, console=Console(file=io.StringIO()))
        displays.append(display)
        return display
    monkeypatch.setattr(api, "PipelineProgress", progress)
    async def extract(_):
        return {"article_types": ["Shirt"], "materials": ["Cotton"],
                "other_requirements": ["machine washable"]}
    monkeypatch.setattr(api.qwen_service, "analyze_requirements", extract)
    monkeypatch.setattr(api.product_service, "get_all_products", lambda: pd.DataFrame([record(material=None)]))
    captured = []
    monkeypatch.setattr(api, "_export_results_to_json", lambda response, *args: captured.append(response.model_dump()))
    try:
        response = asyncio.run(api.get_recommendations(RecommendationRequest(
            gender="Women", size="M", requirements="cotton shirt that is machine washable")))
    finally:
        for display in displays:
            display.close()
    assert response.recommendations == []
    assert response.alternatives[0].unverified_requirements == ["material", "machine washable"]
    assert captured[0]["alternatives"][0]["unverified_requirements"] == ["material", "machine washable"]
