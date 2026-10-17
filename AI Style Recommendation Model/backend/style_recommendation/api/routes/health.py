from fastapi import APIRouter, Depends
from ..dependencies import get_resources

router = APIRouter(prefix="/api", tags=["health"])


async def health_payload(resources):
    available = await resources.qwen.check_connection()
    rankers = {"fashionclip": resources.fashionclip.status(),
               "cartographer": resources.cartographer.status()}
    loaded = resources.catalog.df is not None
    healthy = available and loaded and "unavailable" not in rankers.values()
    return {
        "status": "healthy" if healthy else "degraded", "model_available": available,
        "ollama_connected": available, "model_name": resources.settings.qwen_model,
        "stylist_model_name": resources.settings.qwen_stylist_model, "rankers": rankers,
        "products_loaded": loaded,
        "product_count": len(resources.catalog.df) if loaded else 0,
    }


@router.get("/health")
async def health(resources=Depends(get_resources)):
    return await health_payload(resources)
