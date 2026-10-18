from fastapi import APIRouter, Depends
from ...schemas.models import StylistRequest, StylistResponse
from ..dependencies import get_stylist_service

router = APIRouter(prefix="/api/stylist", tags=["stylist"])


@router.post("", response_model=StylistResponse)
async def generate_stylist_tips(request: StylistRequest, service=Depends(get_stylist_service)):
    return await service.generate(request)
