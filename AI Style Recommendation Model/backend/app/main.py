from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

# --- Prefixed aliases for standalone mode ---
# When running via `python -m uvicorn app.main:app` (without the unified gateway),
# the frontend still queries /fashion-recommendation/api/* (see client/src/app/lib/aiStyleApi.ts).
# Register the same routers under the /fashion-recommendation prefix so both
#   /api/*  and  /fashion-recommendation/api/*  work regardless of how the backend is launched.
# Note: include_router with a prefix concatenates with the router's own prefix.
try:
    app.include_router(requirements_router, prefix="/fashion-recommendation")
    app.include_router(recommendations_router, prefix="/fashion-recommendation")
    app.include_router(stylist_router, prefix="/fashion-recommendation")
except Exception as _e:
    # If FastAPI complains about duplicate operation IDs, the original routes still work
    print(f"Warning: could not register prefixed alias routers: {_e}")

# --- Image serving with placeholder fallback ---
# Dataset expects Images/P*.jpg/png at IMAGES_DIR, but repo gitignores `images/` (see .gitignore)
# so folder is often empty → 404. Serve placeholder for missing files so client always gets an image.
# Use explicit routes instead of StaticFiles so we can fallback.
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
# Ensure placeholder exists (copied from client/public/sizeHome.jpg on first run if needed)
_placeholder = IMAGES_DIR / "placeholder.jpg"
if not _placeholder.exists():
    # Try to copy from client public as placeholder, else create empty
    import shutil

    _client_placeholder = Path(__file__).resolve().parents[3] / "client" / "public" / "sizeHome.jpg"
    if _client_placeholder.exists():
        try:
            shutil.copy(str(_client_placeholder), str(_placeholder))
        except Exception:
            pass


def _serve_image_file(filename: str):
    # Clean path like "Images/P507.jpg" or "P507.jpg"
    cleaned = filename.replace("Images/", "").replace("images/", "").lstrip("/\\")
    # Prevent path traversal
    target = (IMAGES_DIR / cleaned).resolve()
    try:
        # Ensure target is inside IMAGES_DIR
        target.relative_to(IMAGES_DIR.resolve())
    except Exception:
        target = _placeholder
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    if _placeholder.exists():
        return FileResponse(str(_placeholder))
    # Fallback 404 if even placeholder missing
    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/images/{filename:path}")
async def serve_image(filename: str):
    return _serve_image_file(filename)


@app.get("/fashion-recommendation/images/{filename:path}")
async def serve_image_prefixed(filename: str):
    return _serve_image_file(filename)


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


async def _health_payload():
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


@app.get("/api/health")
async def health():
    return await _health_payload()


# Alias for unified-gateway prefix: when running standalone, client still fetches /fashion-recommendation/api/health
@app.get("/fashion-recommendation/api/health")
async def health_prefixed():
    return await _health_payload()


@app.get("/api/genders")
async def get_genders():
    return {"genders": product_service.get_unique_genders()}


@app.get("/fashion-recommendation/api/genders")
async def get_genders_prefixed():
    return {"genders": product_service.get_unique_genders()}


@app.get("/api/occasions")
async def get_occasions():
    return {"occasions": product_service.get_unique_occasions()}


@app.get("/fashion-recommendation/api/occasions")
async def get_occasions_prefixed():
    return {"occasions": product_service.get_unique_occasions()}
