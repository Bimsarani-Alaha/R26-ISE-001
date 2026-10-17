"""Offline import, validation, serialization, and HTTP checks in any interpreter."""
import asyncio
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from pydantic import ValidationError
from style_recommendation.main import create_app
from style_recommendation.api.dependencies import get_recommendation_pipeline
from style_recommendation.schemas.models import RecommendationRequest, RecommendationResponse
from style_recommendation.repositories.result_repository import ResultRepository
from style_recommendation.services.requirement_service import RequirementService


async def extract(text):
    return {"occasion": " Office ", "preferred_colors": ["Red"]}


async def recommend(request):
    return RecommendationResponse(recommendations=[], total_candidates=0)


def main():
    request = RecommendationRequest(gender=" Women ", size=" m ", requirements=" shirt ")
    assert (request.gender, request.size, request.requirements) == ("Women", "M", "shirt")
    assert "model_config" not in request.model_dump()
    assert "model_config" not in request.schema()["properties"]
    for field in ("gender", "size", "requirements"):
        data = dict(gender="Women", size="M", requirements="shirt")
        data[field] = " "
        try:
            RecommendationRequest(**data)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"Blank {field} accepted")
    preferences = asyncio.run(RequirementService(SimpleNamespace(analyze_requirements=extract)).analyze("shirt"))
    assert preferences.occasion == ["Office"]
    response = RecommendationResponse(recommendations=[], total_candidates=0)
    with tempfile.TemporaryDirectory() as directory:
        exported = ResultRepository(Path(directory)).save(request, response)
        assert exported.is_file()
    app = create_app()
    app.dependency_overrides[get_recommendation_pipeline] = lambda: SimpleNamespace(recommend=recommend)
    # No lifespan needed here: dependencies are overridden, avoiding live models.
    client = TestClient(app)
    for prefix in ("", "/fashion-recommendation"):
        result = client.post(prefix + "/api/recommendations", json=request.model_dump())
        assert result.status_code == 200, result.text
        assert result.json() == response.model_dump()
        invalid = client.post(prefix + "/api/recommendations", json={
            "gender": "Women", "size": "bad", "requirements": "shirt"})
        assert invalid.status_code == 422
    assert app.openapi()["paths"]
    print("Serving interpreter: import, schemas, extraction, export, HTTP contracts verified")


if __name__ == "__main__":
    main()
