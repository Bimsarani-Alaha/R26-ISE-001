import asyncio
import base64
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from ultralytics import YOLO
from ColourAnalyzer.app import app as coloranalyzer_app
from cvdMatcher.main import app as cvdmatcher_app


logger = logging.getLogger(__name__)

# MongoDB connection setup
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI") or ""
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE") or "fashion_stylist"
MONGODB_ALLOW_INSECURE_TLS = os.getenv("MONGODB_ALLOW_INSECURE_TLS", "false").lower() in {"1", "true", "yes", "on"}

client = None
db = None
users_collection = None
system_saves_collection = None

if MONGODB_URI:
    mongo_kwargs = {"serverSelectionTimeoutMS": 5000}
    if MONGODB_ALLOW_INSECURE_TLS:
        mongo_kwargs["tlsAllowInvalidCertificates"] = True

    try:
        client = MongoClient(MONGODB_URI, **mongo_kwargs)
        client.admin.command("ping")
        db = client[MONGODB_DATABASE]
        users_collection = db["users"]
        system_saves_collection = db["system_saves"]
        logger.info("MongoDB connection successful.")
    except Exception as exc:
        logger.warning("MongoDB unavailable; continuing without a live connection: %s", exc)
        client = None
        db = None
        users_collection = None
        system_saves_collection = None


# Ensure the sizePredictionEngine folder is importable by this server module.
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir / "sizePredictionEngine"))

from health_tips import HealthTipsConfigurationError, generate_health_tips
from sizeAnalyzer import get_size_label

REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "styleRecommendationEngine"))
sys.path.insert(0, os.path.join(REPO_ROOT, "AI Style Recommendation Model", "backend"))

from src.api.app import app as styleanalyzer_app  # noqa: E402
from app.main import app as fashion_recommendation_app  # noqa: E402


app = FastAPI(
    title="Size Prediction API",
    description="Upload an image and get annotated pose measurements.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/coloranalyzer", coloranalyzer_app)
app.mount("/styleanalyzer", styleanalyzer_app)
app.mount("/cvdmatcher", cvdmatcher_app)
app.mount("/fashion-recommendation", fashion_recommendation_app)


class HealthTipsRequest(BaseModel):
    shoulder_width: float = Field(gt=0)
    hip_size: float = Field(gt=0)
    height: float = Field(gt=0)
    gender: str = "unspecified"
    clothing_size: str = "unspecified"


HEALTH_TIPS_CACHE_SECONDS = float(os.getenv("HEALTH_TIPS_CACHE_SECONDS", "900"))
health_tips_cache: dict[tuple[float, float, float, str, str], tuple[float, str]] = {}
health_tips_request_lock = asyncio.Lock()


class UserRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    age: int | None = None
    password: str | None = None
    requirements: str | None = None
    occasion: str | None = None
    gender: str | None = None
    colorPreference: str | None = None
    prediction: dict | None = None
    recommendations: list[dict] | None = None
    bodyMeasurements: dict | None = None
    metadata: dict | None = None

#register the /api/register endpoint to save system data to MongoDB
@app.post("/api/register")
async def save_system(payload: UserRequest) -> dict:
    if users_collection is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable. Please check the MongoDB connection and try again.",
        )

    document = payload.model_dump(exclude_none=True)
    document["savedAt"] = datetime.now(timezone.utc).isoformat()

    try:
        result = users_collection.insert_one(document)
    except PyMongoError as error:
        logger.exception("Failed to save system payload to MongoDB")
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable right now. The server could not save the registration data.",
        ) from error
    except Exception as error:
        logger.exception("Unexpected error while saving registration payload")
        raise HTTPException(
            status_code=500,
            detail="Unable to save the system data.",
        ) from error

    return {
        "success": True,
        "message": "System data saved successfully.",
        "id": str(result.inserted_id),
    }


@app.post("/api/health-tips")
async def health_tips(request: HealthTipsRequest) -> dict[str, str]:
    cache_key = (
        request.shoulder_width,
        request.hip_size,
        request.height,
        request.gender,
        request.clothing_size,
    )

    async with health_tips_request_lock:
        cached = health_tips_cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return {"guidance": cached[1]}

        try:
            guidance = await generate_health_tips(
                shoulder_width=request.shoulder_width,
                hip_size=request.hip_size,
                height=request.height,
                gender=request.gender,
                clothing_size=request.clothing_size,
            )
        except HealthTipsConfigurationError as error:
            logger.error("Health tips service configuration error: %s", error)
            raise HTTPException(status_code=503, detail="The guidance service is not configured.") from error
        except Exception as error:
            logger.exception("Health tips service request failed")
            if "ollama" in str(error).lower() or "localhost:11434" in str(error).lower():
                raise HTTPException(
                    status_code=503,
                    detail="The local Ollama guidance service is unavailable. Please start the qwen2.5:3b model in Ollama.",
                ) from error
            raise HTTPException(status_code=502, detail="The guidance service is unavailable.") from error

        if not guidance:
            logger.error("Health tips service returned an empty response")
            raise HTTPException(status_code=502, detail="The guidance service returned an empty response.")

        health_tips_cache[cache_key] = (time.monotonic() + HEALTH_TIPS_CACHE_SECONDS, guidance)

    return {"guidance": guidance}

def resolve_model_path(base_dir: str | None = None) -> str:
    base_dir = os.path.abspath(base_dir or os.path.dirname(os.path.dirname(__file__)))

    candidates = [
        os.path.join(base_dir, "sizePredictionEngine", "Y26sizeEnginev6.0.pt"),
        os.path.join(base_dir, "SizePredictionEngine", "Y26sizeEnginev6.0.pt"),
        os.path.join(base_dir, "server", "sizePredictionEngine", "Y26sizeEnginev6.0.pt"),
        os.path.join(base_dir, "server", "SizePredictionEngine", "Y26sizeEnginev6.0.pt"),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return candidates[0]


MODEL_PATH = resolve_model_path()
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

model = YOLO(MODEL_PATH)


def read_image_bytes(data: bytes) -> np.ndarray:
    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image file")
    return image


def build_measurements(keypoints_array: np.ndarray, real_height: float, gender: str = "women") -> list[dict]:
    measurements = []

    for person in keypoints_array:
        if person.shape != (17, 2):
            continue

        def get_distance(p1: np.ndarray, p2: np.ndarray) -> float:
            return float(np.linalg.norm(p1 - p2))

        left_shoulder = person[5]
        right_shoulder = person[6]
        left_hip = person[11]
        right_hip = person[12]
        left_eye = person[1]
        right_eye = person[2]
        left_ankle = person[15]
        right_ankle = person[16]

        shoulder_width = get_distance(left_shoulder, right_shoulder)
        hip_width = get_distance(left_hip, right_hip)

        eye_mid = (left_eye + right_eye) / 2
        foot_mid = (left_ankle + right_ankle) / 2

        height = get_distance(eye_mid, foot_mid)

        shoulder_ratio = shoulder_width / height if height != 0 else 0.0
        hip_ratio = hip_width / height if height != 0 else 0.0

        # -----------------------------
        # Convert pixels to centimeters
        # -----------------------------
        if height != 0:
            cm_per_pixel = real_height / height
            shoulder_cm = shoulder_width * cm_per_pixel
            hip_cm = hip_width * cm_per_pixel
        else:
            shoulder_cm = 0.0
            hip_cm = 0.0

        size_label = get_size_label(shoulder_cm, hip_cm, gender)

        measurements.append(
            {
                "shoulder_width": shoulder_width,
                "hip_width": hip_width,
                "height": height,
                "shoulder_ratio": shoulder_ratio,
                "hip_ratio": hip_ratio,
                "shoulder_cm": shoulder_cm,
                "hip_cm": hip_cm,
                "size": size_label,
            }
        )

    return measurements


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    height: float = Form(...),
    gender: str = Form("women")
) -> dict:

    content = await file.read()

    try:
        image = read_image_bytes(content)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image file")

    result = model(image, conf=0.8)[0]

    annotated_image = result.plot()

    measurements = []

    if result.keypoints is not None:
        keypoints = result.keypoints.xy.cpu().numpy()
        measurements = build_measurements(keypoints, height, gender)

    _, encoded = cv2.imencode(".jpg", annotated_image)
    image_base64 = base64.b64encode(encoded.tobytes()).decode("utf-8")

    return {
        "annotated_image": f"data:image/jpeg;base64,{image_base64}",
        "measurements": measurements,
        "detections": len(result.boxes) if hasattr(result, "boxes") else 0,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)