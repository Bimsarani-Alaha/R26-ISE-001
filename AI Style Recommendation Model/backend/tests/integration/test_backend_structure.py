"""Contract tests for the new backend boundaries; no live inference required."""
import asyncio
import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_unique_package_and_legacy_entrypoint():
    canonical = importlib.import_module("style_recommendation.main")
    legacy = importlib.import_module("app.main")
    assert canonical.app is legacy.app


def test_settings_paths_ignore_cwd(tmp_path, monkeypatch):
    from style_recommendation.core.config import load_settings
    before = load_settings()
    monkeypatch.chdir(tmp_path)
    after = load_settings()
    assert after.dataset_path == before.dataset_path
    assert after.images_dir.name == "Images"
    monkeypatch.setenv("RESULTS_DIR", "custom/results")
    assert load_settings().results_dir == before.base_dir / "custom/results"
    monkeypatch.setenv("RESULTS_DIR", str(tmp_path))
    assert load_settings().results_dir == tmp_path
    monkeypatch.setenv("STYLE_BASE_DIR", "deployment")
    relative_base = load_settings().base_dir
    monkeypatch.chdir(tmp_path.parent)
    assert load_settings().base_dir == relative_base


def test_schema_normalizes_and_rejects_blank_inputs():
    from pydantic import ValidationError
    from style_recommendation.schemas.models import RecommendationRequest, StylistRequest
    request = RecommendationRequest(gender=" Women ", size=" m ", requirements=" red shirt ")
    assert (request.gender, request.size, request.requirements) == ("Women", "M", "red shirt")
    for field in ("gender", "size", "requirements"):
        data = dict(gender="Women", size="M", requirements="shirt")
        data[field] = " "
        with pytest.raises(ValidationError):
            RecommendationRequest(**data)
    with pytest.raises(ValidationError):
        RecommendationRequest(gender="Women", size="invalid", requirements="shirt")
    with pytest.raises(ValidationError):
        StylistRequest(gender="Women", size="M", requirements="shirt", product_id=" ")


def test_result_repository_collision_and_path_safety(tmp_path):
    from style_recommendation.repositories.result_repository import ResultRepository
    from style_recommendation.schemas.models import RecommendationRequest, RecommendationResponse
    repository = ResultRepository(tmp_path)
    request = RecommendationRequest(gender="../../evil\\name", size="M", requirements="shirt")
    response = RecommendationResponse(recommendations=[], total_candidates=0)
    with ThreadPoolExecutor(max_workers=4) as executor:
        paths = list(executor.map(lambda _: repository.save(request, response), range(12)))
    assert len(set(paths)) == 12
    assert all(path.parent == tmp_path for path in paths)
    assert json.loads(paths[0].read_text(encoding="utf-8"))["request"]["gender"] == request.gender


def test_artifact_migration_preserves_and_refuses_overwrite(tmp_path):
    from scripts.migrate_artifacts import migrate_artifacts
    source, target = tmp_path / "source", tmp_path / "target"
    (source / "onnx").mkdir(parents=True)
    (source / "onnx/model.onnx").write_bytes(b"ignored weights")
    migrate_artifacts(source, target)
    assert (target / "onnx/model.onnx").read_bytes() == b"ignored weights"
    assert not source.exists()
    source.mkdir()
    with pytest.raises(FileExistsError):
        migrate_artifacts(source, target)
    assert source.exists()


def resources(tmp_path, *, fail_catalog=False):
    from style_recommendation.core.config import load_settings
    from style_recommendation.core.resources import Resources
    settings = replace(load_settings(), results_dir=tmp_path, images_dir=tmp_path,
                       ranker_enabled=False, fashionclip_enabled=False)
    result = Resources(settings)
    row = dict(product_id="P1", gender="Women", available_sizes=["M"], price=1000,
               article_type="Shirt", base_colour="Red", occasion="Office", style="Formal",
               category="Topwear", material="Cotton", pattern="Solid", sleeve_type="Long",
               neck_type="Collar", description="", image_path="Images/P1.jpg")
    result.catalog.df = pd.DataFrame([row])
    async def extract(_):
        return {"article_types": ["Shirt"], "preferred_colors": ["Red"], "occasion": "Office"}
    async def connected():
        return True
    result.qwen.analyze_requirements = extract
    result.qwen.check_connection = connected
    if fail_catalog:
        result.catalog.df = None
        def fail():
            raise ValueError("catalog missing")
        result.catalog.load_dataset = fail
    return result


@pytest.mark.parametrize("prefix", ["", "/fashion-recommendation"])
def test_api_contract_and_validation(tmp_path, prefix):
    from style_recommendation.main import create_app
    result = resources(tmp_path)
    app = create_app(resources=result)
    with TestClient(app) as client:
        response = client.post(prefix + "/api/recommendations", json={
            "gender": " Women ", "size": " m ", "requirements": "red shirt"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["recommendations"][0]["product_id"] == "P1"
        assert data["alternatives"] == []
        assert data["occasion_used"] == ["Office"]
        assert client.get(prefix + "/api/genders").json() == {"genders": ["Women"]}
        assert client.get(prefix + "/api/health").json()["status"] == "healthy"
        invalid = client.post(prefix + "/api/recommendations", json={
            "gender": "Women", "size": "bad", "requirements": "shirt"})
        assert invalid.status_code == 422
        missing = client.post(prefix + "/api/stylist", json={
            "gender": "Women", "size": "M", "requirements": "shirt", "product_id": "missing"})
        assert missing.status_code == 404


def test_failed_catalog_reports_degraded_and_worker_closed(tmp_path):
    from style_recommendation.main import create_app
    result = resources(tmp_path, fail_catalog=True)
    closed = []
    result.fashionclip.close = lambda: closed.append(True)
    with TestClient(create_app(resources=result)) as client:
        health = client.get("/api/health").json()
        assert health["status"] == "degraded"
        assert health["products_loaded"] is False
    assert closed == [True]


def test_dependency_override(tmp_path):
    from style_recommendation.main import create_app
    from style_recommendation.api.dependencies import get_recommendation_pipeline
    from style_recommendation.schemas.models import RecommendationResponse
    app = create_app(resources=resources(tmp_path))
    async def recommend(request):
        return RecommendationResponse(recommendations=[], total_candidates=23)
    app.dependency_overrides[get_recommendation_pipeline] = lambda: SimpleNamespace(recommend=recommend)
    with TestClient(app) as client:
        response = client.post("/api/recommendations", json={
            "gender": "Women", "size": "M", "requirements": "shirt"})
        assert response.json()["total_candidates"] == 23


def test_images_fallback_and_containment(tmp_path):
    from style_recommendation.main import create_app
    (tmp_path / "P1.jpg").write_bytes(b"product")
    app = create_app(resources=resources(tmp_path))
    with TestClient(app) as client:
        assert client.get("/images/P1.jpg").content == b"product"
        assert client.get("/images/missing.jpg").status_code == 404
        (tmp_path / "placeholder.jpg").write_bytes(b"placeholder")
        assert client.get("/images/missing.jpg").content == b"placeholder"
        for path in ("..%2Foutside.jpg", "C:%5Coutside.jpg", "..%5Coutside.jpg"):
            assert client.get("/images/" + path).status_code == 404


def test_mounted_lifecycle_preserves_parent_and_aliases(tmp_path):
    from contextlib import asynccontextmanager
    from style_recommendation.core.lifespan import mounted_style_lifespan
    from style_recommendation.main import create_app
    events = []
    @asynccontextmanager
    async def parent_lifespan(app):
        events.append("parent start")
        yield
        events.append("parent close")
    result = resources(tmp_path)
    result.fashionclip.close = lambda: events.append("worker close")
    child = create_app(resources=result)
    parent = FastAPI(lifespan=parent_lifespan)
    parent.router.lifespan_context = mounted_style_lifespan(parent.router.lifespan_context, child)
    parent.mount("/fashion-recommendation", child)
    parent.mount("/styleanalyzer", child)
    with TestClient(parent) as client:
        for prefix in ("/fashion-recommendation", "/styleanalyzer"):
            assert client.get(prefix + "/api/health").json()["product_count"] == 1
    assert events == ["parent start", "worker close", "parent close"]


def test_resource_instances_are_isolated(tmp_path):
    from style_recommendation.main import create_app
    first, second = create_app(), create_app()
    assert first.state.resources is not second.state.resources
    assert first.state.resources.catalog is not second.state.resources.catalog
    assert first.state.resources.fashionclip is not second.state.resources.fashionclip
    first.state.resources.catalog.occasion_mapping = {"office": "Formal"}
    second.state.resources.catalog.occasion_mapping = {"office": "Casual"}
    assert first.state.resources.candidates.occasion_values("office") == {"formal"}
    assert second.state.resources.candidates.occasion_values("office") == {"casual"}


def test_import_does_not_initialize_external_resources(monkeypatch):
    from style_recommendation import main
    import httpx
    import subprocess
    def forbidden(*args, **kwargs):
        pytest.fail("Application import initialized an external resource")
    monkeypatch.setattr(pd, "read_csv", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "get", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "post", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    original = Path.read_text
    def read(path, *args, **kwargs):
        if path.suffix == ".txt":
            forbidden()
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read)
    spec = importlib.util.spec_from_file_location("style_recommendation._import_check", main.__file__)
    spec.loader.exec_module(importlib.util.module_from_spec(spec))


def test_cleanup_runs_after_startup_failure(tmp_path):
    from style_recommendation.main import create_app
    result = resources(tmp_path)
    closed = []
    async def fail():
        raise RuntimeError("startup failure")
    result.start = fail
    result.fashionclip.close = lambda: closed.append(True)
    with pytest.raises(RuntimeError, match="startup failure"):
        with TestClient(create_app(resources=result)):
            pass
    assert closed == [True]


@pytest.mark.parametrize("value,expected", [(None, None), ([], None), ([" "], None),
                                         ("", None), (" Office ", ["Office"])])
def test_shared_requirement_normalization(tmp_path, value, expected):
    result = resources(tmp_path)
    async def extract(_):
        return {"occasion": value}
    result.qwen.analyze_requirements = extract
    assert asyncio.run(result.requirements.analyze("shirt")).occasion == expected


@pytest.mark.parametrize("output", [["invalid"], {"occasion": 123}, {"materials": None},
                                  {"error": "model unavailable"}])
def test_model_failures_are_explicit(tmp_path, output):
    from style_recommendation.core.errors import InferenceError
    result = resources(tmp_path)
    async def extract(_):
        return output
    result.qwen.analyze_requirements = extract
    with pytest.raises(InferenceError):
        asyncio.run(result.requirements.analyze("shirt"))


def test_export_failure_does_not_lose_recommendations(tmp_path):
    from style_recommendation.schemas.models import RecommendationRequest
    result = resources(tmp_path)
    def fail(*args):
        raise OSError("read-only export storage")
    result.results.save = fail
    response = asyncio.run(result.pipeline.recommend(RecommendationRequest(
        gender="Women", size="M", requirements="red shirt")))
    assert response.recommendations[0].product_id == "P1"


def test_stylist_formats_advice_and_forwards_product(tmp_path):
    from style_recommendation.schemas.models import StylistRequest
    result = resources(tmp_path)
    captured = {}
    async def generate(**kwargs):
        captured.update(kwargs)
        return {"summary": " Office look ", "accessories": [{"item": "Watch", "color": "Gold", "reason": "Formal"}],
                "footwear": " Loafers ", "layering": {"outerwear": "Blazer"}}
    result.qwen.generate_styling_tips = generate
    advice = asyncio.run(result.stylist.generate(StylistRequest(
        gender="Women", size="M", requirements="red shirt", product_id="P1")))
    assert advice.summary == "Office look"
    assert advice.accessories == ["Watch (Gold) — Formal"]
    assert advice.footwear == ["Loafers"]
    assert advice.layering == ["Blazer"]
    assert captured["product_metadata"]["image_path"] == "Images/P1.jpg"
    assert captured["occasion"] == "Office"


def test_packaged_prompts_and_gateway_import():
    from importlib.resources import files
    for name in ("requirement_prompt.txt", "stylist_prompt.txt", "vision_score_prompt.txt"):
        assert files("style_recommendation").joinpath("prompts", name).read_text(encoding="utf-8")
    gateway = next(parent / "server/server.py" for parent in Path(__file__).resolve().parents
                   if (parent / "server/server.py").is_file())
    assert "from style_recommendation.main import app" in gateway.read_text(encoding="utf-8")


def test_app_schema_has_unique_operation_ids():
    from style_recommendation.main import create_app
    schema = create_app().openapi()
    assert not any(path.startswith("/fashion-recommendation") for path in schema["paths"])
    ids = [operation["operationId"] for path in schema["paths"].values()
           for operation in path.values()]
    assert len(ids) == len(set(ids))


def test_stylist_unexpected_failure_preserves_json_error_response(tmp_path):
    from style_recommendation.main import create_app
    result = resources(tmp_path)
    async def fail(**kwargs):
        raise OSError("product image could not be read")
    result.qwen.generate_styling_tips = fail
    with TestClient(create_app(resources=result), raise_server_exceptions=False) as client:
        response = client.post("/api/stylist", json={
            "gender": "Women", "size": "M", "requirements": "shirt", "product_id": "P1"})
        assert response.status_code == 500
        assert response.json() == {"detail": "product image could not be read"}
