from fastapi import APIRouter
from .routes import recommendations, requirements, stylist, catalog, health, images


def build_router():
    router = APIRouter()
    for module in (recommendations, requirements, stylist, catalog, health, images):
        router.include_router(module.router)
    return router
