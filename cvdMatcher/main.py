from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
from skimage import color
from skimage.color import deltaE_ciede2000
from sklearn.cluster import KMeans
import pickle
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the trained model once when the server starts
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

print("Model loaded successfully")

# ── Colour extraction ──────────────────────────────────────────────────────────

def get_dominant_color(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((100, 100))
    pixels = np.array(img).reshape(-1, 3).astype(float)
    kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
    kmeans.fit(pixels)
    counts = np.bincount(kmeans.labels_)
    dominant = kmeans.cluster_centers_[np.argmax(counts)]
    return [int(dominant[0]), int(dominant[1]), int(dominant[2])]

# ── Delta E ────────────────────────────────────────────────────────────────────

def rgb_to_lab(rgb):
    arr = np.array(rgb, dtype=float) / 255.0
    return color.rgb2lab(arr.reshape(1, 1, 3))[0][0]

def calculate_delta_e(rgb1, rgb2):
    return round(float(deltaE_ciede2000(rgb_to_lab(rgb1), rgb_to_lab(rgb2))), 2)

# ── Predict using trained model ────────────────────────────────────────────────

def predict_match(rgb1, rgb2, delta_e):
    features = [[
        rgb1[0], rgb1[1], rgb1[2],
        rgb2[0], rgb2[1], rgb2[2],
        delta_e
    ]]
    prediction = model.predict(features)[0]      # "Good", "Moderate", or "Poor"
    probabilities = model.predict_proba(features)[0]
    confidence = round(float(max(probabilities)) * 100, 1)
    return prediction, confidence

# ── CVD distinguishability (unchanged) ────────────────────────────────────────

def get_hue_category(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    mx, mn = max(r,g,b), min(r,g,b)
    d = mx - mn
    if d < 0.12:
        return "white" if mx > 0.85 else ("black" if mx < 0.25 else "gray")
    if mx == r:   h = ((g - b) / d) % 6
    elif mx == g: h = (b - r) / d + 2
    else:         h = (r - g) / d + 4
    h *= 60
    if h < 20 or h >= 340: return "red"
    elif h < 45:  return "orange"
    elif h < 75:  return "yellow"
    elif h < 150: return "green"
    elif h < 195: return "cyan"
    elif h < 255: return "blue"
    elif h < 285: return "violet"
    return "pink"

CVD_CONFUSION = {
    "Protanopia":   [("red","green"),("red","cyan"),("orange","green"),("red","gray"),("orange","cyan")],
    "Deuteranopia": [("red","green"),("red","yellow"),("orange","yellow"),("green","yellow"),("orange","green")],
    "Tritanopia":   [("blue","yellow"),("blue","orange"),("violet","yellow"),("cyan","pink"),("blue","green")],
}

COLOR_NAMES = {
    "red":"Red","orange":"Orange","yellow":"Yellow","green":"Green",
    "cyan":"Cyan","blue":"Blue","violet":"Violet","pink":"Pink/Magenta",
    "white":"White","black":"Black","gray":"Gray/Neutral",
}

def is_hard_to_distinguish(category, cvd_type):
    if cvd_type == "Normal": return False
    return any(category in (a, b) for a, b in CVD_CONFUSION.get(cvd_type, []))

def to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

# ── Endpoint ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "CVD Clothing Matcher API is running"}

@app.post("/analyse")
async def analyse(
    top: UploadFile = File(...),
    bottom: UploadFile = File(...),
    cvd_type: str = Form(...),
):
    top_bytes    = await top.read()
    bottom_bytes = await bottom.read()

    top_rgb    = get_dominant_color(top_bytes)
    bottom_rgb = get_dominant_color(bottom_bytes)

    delta_e = calculate_delta_e(top_rgb, bottom_rgb)

    # ← Model predicts the match label
    match_result, confidence = predict_match(top_rgb, bottom_rgb, delta_e)

    top_cat    = get_hue_category(top_rgb)
    bottom_cat = get_hue_category(bottom_rgb)

    return {
        "top_color":    {"hex": to_hex(top_rgb),    "name": COLOR_NAMES.get(top_cat, top_cat),       "rgb": top_rgb},
        "bottom_color": {"hex": to_hex(bottom_rgb), "name": COLOR_NAMES.get(bottom_cat, bottom_cat), "rgb": bottom_rgb},
        "delta_e":      delta_e,
        "match_label":  f"{match_result} match",
        "confidence":   confidence,
        "top_hard":     is_hard_to_distinguish(top_cat, cvd_type),
        "bottom_hard":  is_hard_to_distinguish(bottom_cat, cvd_type),
        "cvd_type":     cvd_type,
    }