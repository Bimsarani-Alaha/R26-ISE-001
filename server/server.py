import asyncio
import base64
import logging
import os
import sys
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import cv2
import joblib
import numpy as np
import pandas as pd
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

STYLE_RECOMMENDATION_BACKEND = (
    base_dir / "AI Style Recommendation Model" / "backend"
)
if not STYLE_RECOMMENDATION_BACKEND.is_dir():
    raise FileNotFoundError(
        f"Style recommendation backend not found: {STYLE_RECOMMENDATION_BACKEND}"
    )
sys.path.insert(0, str(STYLE_RECOMMENDATION_BACKEND))

from app.main import app as styleanalyzer_app  # noqa: E402


app = FastAPI(
    title="Size Prediction API",
    description="Predict clothing size from a camera capture or uploaded photo without requiring height.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/coloranalyzer", coloranalyzer_app)
app.mount("/fashion-recommendation", styleanalyzer_app)
app.mount("/styleanalyzer", styleanalyzer_app)
app.mount("/cvdmatcher", cvdmatcher_app)

DEFAULT_CAMERA_DISTANCE_M = 2.0
ASSUMED_VERTICAL_FOV_DEGREES = 60.0
EYE_TO_ANKLE_HEIGHT_RATIO = 0.93
ESTIMATED_HEIGHT_CALIBRATION_OFFSET_CM = 23.3


class HealthTipsRequest(BaseModel):
    clothing_size: str = Field(min_length=1, max_length=20)


HEALTH_TIPS_CACHE_SECONDS = float(os.getenv("HEALTH_TIPS_CACHE_SECONDS", "900"))
health_tips_cache: dict[str, tuple[float, str]] = {}
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
    cache_key = request.clothing_size.strip()
    if not cache_key:
        raise HTTPException(status_code=422, detail="A predicted clothing size is required.")

    async with health_tips_request_lock:
        cached = health_tips_cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return {"guidance": cached[1]}

        try:
            guidance = await generate_health_tips(cache_key)
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

LINEAR_SIZE_MODEL_PATH = os.path.join(base_dir, "sizePredictionEngine", "linear_size_model.pkl")


@lru_cache(maxsize=1)
def load_linear_size_model() -> tuple[Any, dict[int, str]]:
    if not os.path.exists(LINEAR_SIZE_MODEL_PATH):
        logger.error("Linear size model file not found: %s", LINEAR_SIZE_MODEL_PATH)
        raise HTTPException(status_code=503, detail="Automatic size prediction is not configured.")

    try:
        artifact: Any = joblib.load(LINEAR_SIZE_MODEL_PATH)
    except Exception as error:
        logger.exception("Failed to load the linear size model")
        raise HTTPException(status_code=503, detail="Automatic size prediction model could not be loaded.") from error

    if not isinstance(artifact, dict):
        raise ValueError("Linear size model artifact must be a dictionary")

    size_model = artifact.get("model")
    size_mapping = artifact.get("number_to_size")
    if size_model is None or not isinstance(size_mapping, dict):
        raise ValueError("Linear size model artifact must contain a model and number_to_size mapping")

    return size_model, size_mapping


def read_image_bytes(data: bytes) -> np.ndarray:
    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image file")
    return image


def extract_pixel_measurements(keypoints_array: np.ndarray) -> list[dict[str, float]]:
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

        measurements.append(
            {
                "shoulder_width": shoulder_width,
                "hip_width": hip_width,
                "height": height,
                "shoulder_ratio": shoulder_ratio,
                "hip_ratio": hip_ratio,
            }
        )

    return measurements


def build_measurements(keypoints_array: np.ndarray, real_height: float, gender: str = "women") -> list[dict]:
    measurements = []

    for measurement in extract_pixel_measurements(keypoints_array):
        height = measurement["height"]
        if height != 0:
            cm_per_pixel = real_height / height
            shoulder_cm = measurement["shoulder_width"] * cm_per_pixel
            hip_cm = measurement["hip_width"] * cm_per_pixel
        else:
            shoulder_cm = 0.0
            hip_cm = 0.0

        size_label = get_size_label(shoulder_cm, hip_cm, gender)
        measurements.append(
            {
                **measurement,
                "shoulder_cm": shoulder_cm,
                "hip_cm": hip_cm,
                "size": size_label,
            }
        )

    return measurements


def build_automatic_predictions(
    keypoints_array: np.ndarray,
    gender: str,
    real_height: float | None = None,
    frame_height: int | None = None,
) -> list[dict[str, float | str | bool]]:
    measurements = extract_pixel_measurements(keypoints_array)
    if not measurements:
        return []

    model_gender = "m" if gender.strip().lower().startswith("m") else "f"
    size_model, size_mapping = load_linear_size_model() 
    predictions = []

    for measurement in measurements:
        features = pd.DataFrame(
            [
                {
                    "pixel_height": measurement["height"],
                    "pixel_shoulder": measurement["shoulder_width"],
                    "pixel_hip": measurement["hip_width"],
                    "gender": model_gender,
                }
            ],
            columns=["pixel_height", "pixel_shoulder", "pixel_hip", "gender"],
        )
        size_number = int(np.clip(np.rint(size_model.predict(features)[0]), 0, 7))
        size_label = size_mapping.get(size_number)
        if size_label is None:
            raise ValueError(f"Linear size model returned an unknown size code: {size_number}")
        prediction: dict[str, float | str | bool] = {
            "size": size_label,
            "height_px": measurement["height"],
            "shoulder_width_px": measurement["shoulder_width"],
            "hip_width_px": measurement["hip_width"],
        }
        if real_height is not None and measurement["height"] > 0:
            cm_per_pixel = real_height / measurement["height"]
            estimated_height_cm = real_height
            height_is_estimated = False
        elif frame_height and frame_height > 0 and measurement["height"] > 0:
            frame_height_cm = (
                2
                * DEFAULT_CAMERA_DISTANCE_M
                * 100
                * np.tan(np.radians(ASSUMED_VERTICAL_FOV_DEGREES / 2))
            )
            cm_per_pixel = frame_height_cm / frame_height
            estimated_height_cm = (
                measurement["height"]
                * cm_per_pixel
                / EYE_TO_ANKLE_HEIGHT_RATIO
            ) + ESTIMATED_HEIGHT_CALIBRATION_OFFSET_CM
            cm_per_pixel = (
                estimated_height_cm
                * EYE_TO_ANKLE_HEIGHT_RATIO
                / measurement["height"]
            )
            height_is_estimated = True
        else:
            predictions.append(prediction)
            continue

        prediction.update(
            {
                "height_cm": estimated_height_cm,
                "height_m": estimated_height_cm / 100,
                "height_is_estimated": height_is_estimated,
                "shoulder_cm": measurement["shoulder_width"] * cm_per_pixel,
                "hip_cm": measurement["hip_width"] * cm_per_pixel,
            }
        )
        predictions.append(prediction)

    return predictions


POSE_KEYPOINT_CONFIDENCE_THRESHOLD = 0.45
POSE_BOX_CONFIDENCE_THRESHOLD = 0.5
MIN_PERSON_FRAME_HEIGHT_RATIO = 0.35
MAX_PERSON_FRAME_HEIGHT_RATIO = 0.88


# Frame-height bands are a framing heuristic, not a calibrated distance measurement.
def evaluate_pose_readiness(
    boxes: np.ndarray,
    box_confidences: np.ndarray,
    keypoints: np.ndarray,
    keypoint_confidences: np.ndarray | None,
    frame_width: int,
    frame_height: int,
) -> dict[str, Any]:
    if len(boxes) == 0 or len(box_confidences) == 0:
        return {
            "ready": False,
            "message": "Step into view so the camera can detect your full body.",
            "reason": "no_person",
            "box": None,
            "frame_width": frame_width,
            "frame_height": frame_height,
        }

    person_index = int(np.argmax(box_confidences))
    x1, y1, x2, y2 = boxes[person_index].astype(float).tolist()
    box_confidence = float(box_confidences[person_index])
    normalized_box = [
        max(0.0, min(1.0, x1 / frame_width)),
        max(0.0, min(1.0, y1 / frame_height)),
        max(0.0, min(1.0, x2 / frame_width)),
        max(0.0, min(1.0, y2 / frame_height)),
    ]

    def result(ready: bool, message: str, reason: str | None) -> dict[str, Any]:
        return {
            "ready": ready,
            "message": message,
            "reason": reason,
            "box": normalized_box,
            "frame_width": frame_width,
            "frame_height": frame_height,
            "detection_confidence": box_confidence,
        }

    if box_confidence < POSE_BOX_CONFIDENCE_THRESHOLD:
        return result(False, "Hold still while the camera checks your pose.", "low_confidence")
    if person_index >= len(keypoints):
        return result(False, "Hold still while the camera checks your pose.", "low_confidence")
    if keypoint_confidences is None or person_index >= len(keypoint_confidences):
        return result(False, "Pose confidence is too low. Face the camera and try again.", "low_confidence")

    person_keypoints = keypoints[person_index]
    person_confidences = keypoint_confidences[person_index]
    if len(person_keypoints) < 17 or len(person_confidences) < 17:
        return result(False, "Pose confidence is too low. Face the camera and try again.", "low_confidence")

    frame_edges = np.array([frame_width, frame_height], dtype=float)
    in_frame = np.all(person_keypoints >= 0) and np.all(person_keypoints < frame_edges)

    head_indices = (0, 1, 2, 3, 4)
    required_body_indices = (5, 6, 11, 12, 13, 14, 15, 16)
    head_visible = any(
        person_confidences[index] >= POSE_KEYPOINT_CONFIDENCE_THRESHOLD
        for index in head_indices
    )
    body_visible = all(
        person_confidences[index] >= POSE_KEYPOINT_CONFIDENCE_THRESHOLD
        for index in required_body_indices
    )

    if not head_visible or not body_visible:
        return result(
            False,
            "Pose confidence is too low. Face the camera and keep your head, shoulders, hips, knees, and feet visible.",
            "low_confidence",
        )

    if not in_frame:
        return result(
            False,
            "Make sure your head, shoulders, hips, knees, and feet are fully visible.",
            "partial",
        )

    body_indices = list(required_body_indices)
    body_points = person_keypoints[body_indices]
    body_inside_box = np.all(
        (body_points[:, 0] >= x1)
        & (body_points[:, 0] <= x2)
        & (body_points[:, 1] >= y1)
        & (body_points[:, 1] <= y2)
    )
    head_inside_box = any(
        person_confidences[index] >= POSE_KEYPOINT_CONFIDENCE_THRESHOLD
        and x1 <= person_keypoints[index, 0] <= x2
        and y1 <= person_keypoints[index, 1] <= y2
        for index in head_indices
    )
    if not body_inside_box or not head_inside_box:
        return result(
            False,
            "Make sure your head, shoulders, hips, knees, and feet fit inside the yellow box.",
            "partial",
        )

    edge_margin_x = frame_width * 0.01
    edge_margin_y = frame_height * 0.01
    if x1 <= edge_margin_x or y1 <= edge_margin_y or x2 >= frame_width - edge_margin_x or y2 >= frame_height - edge_margin_y:
        return result(False, "Move so your entire body is inside the frame.", "partial")

    person_height_ratio = (y2 - y1) / frame_height
    if person_height_ratio > MAX_PERSON_FRAME_HEIGHT_RATIO:
        return result(False, "Move further back until your full body fits comfortably in frame.", "too_close")
    if person_height_ratio < MIN_PERSON_FRAME_HEIGHT_RATIO:
        return result(False, "Move closer so your full body is clearly visible in frame.", "too_far")
    if box_confidence < POSE_BOX_CONFIDENCE_THRESHOLD or np.any(
        person_confidences[list(required_body_indices)] < POSE_KEYPOINT_CONFIDENCE_THRESHOLD
    ):
        return result(False, "Hold still while the camera checks your pose.", "low_confidence")

    ready_result = result(
        True,
        "Perfect! Your full body is visible and the framing looks good. The camera cannot verify the exact distance.",
        None,
    )
    ready_result["person_height_ratio"] = person_height_ratio
    return ready_result


@app.post("/pose-readiness")
async def pose_readiness(file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()

    try:
        image = read_image_bytes(content)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid camera frame") from error

    frame_height, frame_width = image.shape[:2]
    try:
        result = model(image, conf=0.35, verbose=False)[0]
        if result.keypoints is None or result.boxes is None:
            boxes = np.empty((0, 4), dtype=float)
            box_confidences = np.empty((0,), dtype=float)
            keypoints = np.empty((0, 17, 2), dtype=float)
            keypoint_confidences = None
        else:
            boxes = result.boxes.xyxy.cpu().numpy()
            box_confidences = result.boxes.conf.cpu().numpy()
            keypoints = result.keypoints.xy.cpu().numpy()
            keypoint_confidences = (
                result.keypoints.conf.cpu().numpy()
                if result.keypoints.conf is not None
                else None
            )
    except Exception as error:
        logger.exception("Real-time pose detection failed")
        raise HTTPException(status_code=500, detail="Pose detection failed for the camera frame.") from error

    return evaluate_pose_readiness(
        boxes,
        box_confidences,
        keypoints,
        keypoint_confidences,
        frame_width,
        frame_height,
    )


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    mode: Literal["automatic", "manual"] = Form("automatic"),
    height: float | None = Form(None),
    gender: str = Form("women"),
) -> dict:
    if mode == "manual" and (
        height is None or not np.isfinite(height) or height <= 0
    ):
        raise HTTPException(status_code=422, detail="A positive height is required for manual size prediction")
    if mode == "automatic" and height is not None and (
        not np.isfinite(height) or height <= 0
    ):
        raise HTTPException(status_code=422, detail="Height must be a positive number in centimeters")

    content = await file.read()

    try:
        image = read_image_bytes(content)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image file")

    result = model(image, conf=0.8)[0] #send image to sizeEngine model for prediction

    annotated_image = result.plot()

    measurements = []

    if result.keypoints is not None: #if keypoints are detected, extract measurements
        keypoints = result.keypoints.xy.cpu().numpy()
        if mode == "automatic":
            measurements = build_automatic_predictions(
                keypoints,
                gender,
                height,
                frame_height=image.shape[0],
            )
        else:
            measurements = build_measurements(keypoints, height, gender)

    _, encoded = cv2.imencode(".jpg", annotated_image)
    image_base64 = base64.b64encode(encoded.tobytes()).decode("utf-8")

    return {
        "annotated_image": f"data:image/jpeg;base64,{image_base64}",
        "measurements": measurements,
        "detections": len(result.boxes) if hasattr(result, "boxes") else 0,
    } #return the annotated image, measurements, and number of detections send to frontend for display


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
