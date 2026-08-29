from fastapi import APIRouter, HTTPException
from ..schemas.models import RequirementRequest, RequirementResponse
from ..services.qwen_service import qwen_service

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.post("/analyze", response_model=RequirementResponse)
async def analyze_requirements(request: RequirementRequest):
    if not request.requirements.strip():
        raise HTTPException(status_code=400, detail="Requirements text is required")

    result = await qwen_service.analyze_requirements(request.requirements)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    occasion = result.get("occasion")
    if occasion is None:
        occasion = None
    elif isinstance(occasion, str):
        occasion = [occasion] if occasion.strip() else None
    elif isinstance(occasion, list):
        occasion = [o for o in occasion if o.strip()] if occasion else None

    return RequirementResponse(
        occasion=occasion,
        preferred_colors=result.get("preferred_colors", []),
        article_types=result.get("article_types", []),
        style_preferences=result.get("style_preferences", []),
        materials=result.get("materials", []),
        patterns=result.get("patterns", []),
        sleeve_types=result.get("sleeve_types", []),
        neck_types=result.get("neck_types", []),
        other_requirements=result.get("other_requirements", []),
        price_preference=result.get("price_preference"),
    )
