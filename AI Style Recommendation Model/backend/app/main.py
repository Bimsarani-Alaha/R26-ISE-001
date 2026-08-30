from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api.requirements import router as requirements_router
from .api.recommendations import router as recommendations_router
from .api.stylist import router as stylist_router
from .services.product_service import product_service
from .services.qwen_service import qwen_service
from .config import IMAGES_DIR, QWEN_MODEL

app = FastAPI(
    title="AI Fashion Recommendation System",
    description="Occasion-aware fashion recommendation using Qwen3-VL:8B",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requirements_router)
app.include_router(recommendations_router)
app.include_router(stylist_router)

if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")


@app.on_event("startup")
async def startup_event():
    try:
        product_service.load_dataset()
        print(f"Loaded {len(product_service.df)} products")
    except Exception as e:
        print(f"ERROR loading dataset: {e}")
    connected = await qwen_service.check_connection()
    print(f"Ollama connected: {connected}")


@app.get("/")
async def root():
    return {"message": "AI Fashion Recommendation System", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    product_service._ensure_loaded()
    model_available = await qwen_service.check_connection()
    return {
        "status": "healthy" if model_available else "degraded",
        "model_available": model_available,
        "ollama_connected": model_available,
        "model_name": QWEN_MODEL,
        "products_loaded": product_service.df is not None,
        "product_count": len(product_service.df) if product_service.df is not None else 0,
    }


@app.get("/api/genders")
async def get_genders():
    return {"genders": product_service.get_unique_genders()}


@app.get("/api/occasions")
async def get_occasions():
    return {"occasions": product_service.get_unique_occasions()}
