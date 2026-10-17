from fastapi import APIRouter, Depends
from ...schemas.models import RequirementRequest, RequirementResponse
from ..dependencies import get_requirement_service

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.post("/analyze", response_model=RequirementResponse)
async def analyze_requirements(request: RequirementRequest, service=Depends(get_requirement_service)):
    return await service.analyze(request.requirements)
