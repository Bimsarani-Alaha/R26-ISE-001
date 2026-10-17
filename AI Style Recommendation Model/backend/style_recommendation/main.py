"""FastAPI composition and compatibility aliases."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .api.router import build_router
from .core.errors import InferenceError, ProductNotFoundError
from .core.lifespan import lifespan
from .core.resources import Resources


def create_app(settings=None, resources=None):
    application = FastAPI(
        title="AI Fashion Recommendation System",
        description="Occasion-aware fashion recommendation using Qwen3-VL:8B",
        version="1.0.0", lifespan=lifespan)
    application.state.resources = resources if resources is not None else Resources(settings)
    application.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                               allow_methods=["*"], allow_headers=["*"])
    router = build_router()
    application.include_router(router)
    application.include_router(router, prefix="/fashion-recommendation", include_in_schema=False)

    @application.get("/")
    async def root():
        return {"message": "AI Fashion Recommendation System", "version": "1.0.0"}

    @application.exception_handler(InferenceError)
    async def inference_error(request: Request, error: InferenceError):
        return JSONResponse(status_code=500, content={"detail": str(error)})

    @application.exception_handler(ProductNotFoundError)
    async def product_not_found(request: Request, error: ProductNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    return application


app = create_app()
