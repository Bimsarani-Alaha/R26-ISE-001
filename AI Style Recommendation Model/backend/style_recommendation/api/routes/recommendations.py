from fastapi import APIRouter, Depends
from ...schemas.models import RecommendationRequest, RecommendationResponse
from ..dependencies import get_recommendation_pipeline

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest, pipeline=Depends(get_recommendation_pipeline)):
    return await pipeline.recommend(request)
