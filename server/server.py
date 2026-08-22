import base64
import os
import cv2
import numpy as np
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from ColourAnalyzer.app import app as coloranalyzer_app
from cvdMatcher.main import app as cvdmatcher_app


# Ensure the sizePredictionEngine folder is importable by this server module.
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir / "sizePredictionEngine"))

from sizeAnalyzer import get_size_label


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
app.mount("/cvdmatcher", cvdmatcher_app)

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