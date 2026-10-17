from fastapi import APIRouter, Depends
from ..dependencies import get_catalog

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/genders")
def get_genders(catalog=Depends(get_catalog)):
    return {"genders": catalog.get_unique_genders()}


@router.get("/occasions")
def get_occasions(catalog=Depends(get_catalog)):
    return {"occasions": catalog.get_unique_occasions()}
