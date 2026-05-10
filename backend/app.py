from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import base64
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
CLASSIFIER_PATH = BASE_DIR / "models" / "tshirt_color_classifier.h5"
GENERATOR_PATH = BASE_DIR / "models" / "cvd_generator.keras"

IMG_SIZE_CLASSIFIER = 224
IMG_SIZE_GENERATOR = 128
CLASS_NAMES = ["blue", "brown", "green", "red", "yellow"]
CVD_MAP = {"Protanopia": 0, "Deuteranopia": 1, "Tritanopia": 2}

print("Loading models...")
classifier = tf.keras.models.load_model(CLASSIFIER_PATH)
generator = tf.keras.models.load_model(GENERATOR_PATH)
print("Models loaded successfully!")

def predict(img):
    img = img.resize((IMG_SIZE_CLASSIFIER, IMG_SIZE_CLASSIFIER))
    arr = tf.keras.applications.mobilenet_v2.preprocess_input(np.array(img).astype(np.float32))
    pred = classifier.predict(np.expand_dims(arr, 0), verbose=0)[0]
    idx = pred.argmax()
    return CLASS_NAMES[idx], float(pred[idx]), {CLASS_NAMES[i]: float(pred[i]) for i in range(5)}

def simulate(img, cvd_type):
    img = img.resize((IMG_SIZE_GENERATOR, IMG_SIZE_GENERATOR))
    arr = np.array(img).astype(np.float32) / 255.0
    cond = tf.one_hot([CVD_MAP[cvd_type]], depth=3)
    out = generator.predict([np.expand_dims(arr, 0), cond], verbose=0)[0]
    out = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(out)

@app.post("/predict")
async def predict_endpoint(
    image: UploadFile = File(...),
    cvdType: str = Form(...)
):
    contents = await image.read()
    original = Image.open(io.BytesIO(contents)).convert("RGB")
    
    color, confidence, all_confidences = predict(original)
    simulated = simulate(original, cvdType)
    
    buffer = io.BytesIO()
    simulated.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "success": True,
        "color": color,
        "confidence": confidence,
        "allConfidences": all_confidences,
        "simulatedImage": img_base64
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)