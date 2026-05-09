from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
from skimage import color
from skimage.color import deltaE_ciede2000
from sklearn.cluster import KMeans
from rembg import remove as remove_bg, new_session  
import pickle
import io
import os

app = FastAPI(title="CVD Clothing Matcher API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load Models ────────────────────────────────────────────────────────────────

with open("model.pkl", "rb") as f:
    rf_model = pickle.load(f)
print("✅ Random Forest model loaded")

nn_model = None
try:
    from tensorflow.keras.models import load_model
    if os.path.exists("model.h5"):
        nn_model = load_model("model.h5")
        print("✅ Neural Network model loaded")
    else:
        print("⚠️  model.h5 not found — running RF-only mode")
except Exception as e:
    print(f"⚠️  Could not load model.h5: {e} — running RF-only mode")

    # ── Pre-load rembg session at startup ─────────────────────────────────────────
REMBG_SESSION = new_session("u2net")   # ← ADD THIS BLOCK
print("✅ Background removal model loaded")

# Label order must match training encoding: Good=0, Moderate=1, Poor=2
NN_CLASSES = ["Good", "Moderate", "Poor"]

# ── Colour Extraction ──────────────────────────────────────────────────────────

def remove_background(image_bytes: bytes) -> np.ndarray:
    cleaned = remove_bg(image_bytes, session=REMBG_SESSION)
    img     = Image.open(io.BytesIO(cleaned)).convert("RGBA")
    return np.array(img)

def get_foreground_pixels(image_bytes: bytes) -> np.ndarray:
    rgba       = remove_background(image_bytes)
    r, g, b, a = rgba[:,:,0], rgba[:,:,1], rgba[:,:,2], rgba[:,:,3]

    alpha_mask  = a > 128
    brightness  = r.astype(float) + g + b
    color_mask  = (brightness > 80) & (brightness < 720)
    mx = np.maximum(np.maximum(r, g), b).astype(float)
    mn = np.minimum(np.minimum(r, g), b).astype(float)
    sat_mask    = np.where(mx > 0, (mx - mn) / mx, 0) > 0.08

    final_mask  = alpha_mask & color_mask & sat_mask
    pixels      = rgba[:, :, :3][final_mask].astype(float)

    if len(pixels) < 10:
        pixels = rgba[:, :, :3][alpha_mask].astype(float)

    return pixels

def get_dominant_color(image_bytes: bytes) -> list:
    pixels = get_foreground_pixels(image_bytes)
    k      = min(3, max(1, len(pixels) // 10))
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    kmeans.fit(pixels)
    counts   = np.bincount(kmeans.labels_)
    dominant = kmeans.cluster_centers_[np.argmax(counts)]
    return [int(dominant[0]), int(dominant[1]), int(dominant[2])]

def get_color_palette(image_bytes: bytes, n: int = 3) -> list:
    pixels = get_foreground_pixels(image_bytes)
    k      = min(n, max(1, len(pixels) // 10))
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    kmeans.fit(pixels)
    counts  = np.bincount(kmeans.labels_)
    total   = counts.sum()
    palette = []
    for idx in np.argsort(-counts):
        rgb = [int(v) for v in kmeans.cluster_centers_[idx]]
        palette.append({
            "hex":        to_hex(rgb),
            "rgb":        rgb,
            "percentage": round(float(counts[idx] / total) * 100, 1),
        })
    return palette

# ── Delta E ────────────────────────────────────────────────────────────────────

def rgb_to_lab(rgb):
    arr = np.array(rgb, dtype=float) / 255.0
    return color.rgb2lab(arr.reshape(1, 1, 3))[0][0]

def calculate_delta_e(rgb1, rgb2):
    return round(float(deltaE_ciede2000(rgb_to_lab(rgb1), rgb_to_lab(rgb2))), 2)

# ── Prediction ─────────────────────────────────────────────────────────────────

def predict_rf(features):
    """Random Forest prediction → label + per-class probabilities."""
    proba      = rf_model.predict_proba(features)[0]
    label      = rf_model.predict(features)[0]
    classes    = list(rf_model.classes_)
    prob_dict  = {c: round(float(p) * 100, 1) for c, p in zip(classes, proba)}
    confidence = round(float(max(proba)) * 100, 1)
    return label, confidence, prob_dict

def predict_nn(features):
    """Neural Network prediction → label + per-class probabilities."""
    if nn_model is None:
        return None, None, None
    proba      = nn_model.predict(np.array(features), verbose=0)[0]
    label      = NN_CLASSES[int(np.argmax(proba))]
    prob_dict  = {c: round(float(p) * 100, 1) for c, p in zip(NN_CLASSES, proba)}
    confidence = round(float(max(proba)) * 100, 1)
    return label, confidence, prob_dict

def ensemble_predict(features):
    """
    Combine RF + NN probabilities (average) for a final ensemble prediction.
    Falls back to RF-only if NN is unavailable.
    """
    rf_label, rf_conf, rf_probs = predict_rf(features)

    if nn_model is None:
        return rf_label, rf_conf, rf_probs, rf_label, rf_conf, None, None

    nn_label, nn_conf, nn_probs = predict_nn(features)

    # Average probabilities across both models (same class order)
    classes = ["Good", "Moderate", "Poor"]
    avg_probs = {
        c: round((rf_probs.get(c, 0) + nn_probs.get(c, 0)) / 2, 1)
        for c in classes
    }
    ensemble_label = max(avg_probs, key=avg_probs.get)
    ensemble_conf  = round(avg_probs[ensemble_label], 1)

    return ensemble_label, ensemble_conf, avg_probs, rf_label, rf_conf, nn_label, nn_conf

# ── Match Advice ───────────────────────────────────────────────────────────────

MATCH_ADVICE = {
    "Good": {
        "tip":   "Great combination! These colours complement each other well.",
        "emoji": "✅",
    },
    "Moderate": {
        "tip":   "Acceptable pairing. Consider adding a neutral accessory to tie the look together.",
        "emoji": "⚠️",
    },
    "Poor": {
        "tip":   "These colours may clash. Try swapping one piece for a neutral tone.",
        "emoji": "❌",
    },
}

def delta_e_description(de):
    if de < 10:  return "Very similar colours"
    if de < 25:  return "Noticeable difference"
    if de < 50:  return "Strong contrast"
    return "Very high contrast"

# ── CVD Helpers ────────────────────────────────────────────────────────────────

def get_hue_category(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    mx, mn  = max(r, g, b), min(r, g, b)
    d       = mx - mn
    if d < 0.12:
        return "white" if mx > 0.85 else ("black" if mx < 0.25 else "gray")
    if   mx == r: h = ((g - b) / d) % 6
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

def cvd_recommendation(top_cat, bottom_cat, cvd_type):
    """Return a plain-English CVD tip when colours may be confused."""
    if cvd_type == "Normal":
        return None
    top_hard    = is_hard_to_distinguish(top_cat, cvd_type)
    bottom_hard = is_hard_to_distinguish(bottom_cat, cvd_type)
    if top_hard and bottom_hard:
        return (f"Both colours may look similar under {cvd_type}. "
                "Consider adding a strong brightness contrast or a neutral piece.")
    if top_hard:
        return f"Your top colour may be hard to distinguish under {cvd_type}."
    if bottom_hard:
        return f"Your bottom colour may be hard to distinguish under {cvd_type}."
    return "These colours should be distinguishable with your colour vision profile."

def to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "CVD Clothing Matcher API v2 is running",
        "models":  {
            "random_forest": True,
            "neural_network": nn_model is not None,
            "mode": "ensemble" if nn_model is not None else "random_forest_only",
        }
    }

@app.get("/health")
def health():
    return {"ok": True, "nn_loaded": nn_model is not None}

@app.post("/analyse")
async def analyse(
    top:      UploadFile = File(...),
    bottom:   UploadFile = File(...),
    cvd_type: str        = Form(...),
):
    top_bytes    = await top.read()
    bottom_bytes = await bottom.read()

    # Validate uploads
    for name, data in [("top", top_bytes), ("bottom", bottom_bytes)]:
        if not data:
            raise HTTPException(status_code=400, detail=f"Empty file for {name}")

    # Colours
    top_rgb    = get_dominant_color(top_bytes)
    bottom_rgb = get_dominant_color(bottom_bytes)
    delta_e    = calculate_delta_e(top_rgb, bottom_rgb)

    # Palettes (top-3 colours per garment)
    top_palette    = get_color_palette(top_bytes,    n=3)
    bottom_palette = get_color_palette(bottom_bytes, n=3)

    # Predictions
    features = [[
        top_rgb[0], top_rgb[1], top_rgb[2],
        bottom_rgb[0], bottom_rgb[1], bottom_rgb[2],
        delta_e,
    ]]
    (ensemble_label, ensemble_conf, ensemble_probs,
     rf_label, rf_conf, nn_label, nn_conf) = ensemble_predict(features)

    # CVD
    top_cat    = get_hue_category(top_rgb)
    bottom_cat = get_hue_category(bottom_rgb)
    cvd_tip    = cvd_recommendation(top_cat, bottom_cat, cvd_type)

    advice = MATCH_ADVICE.get(ensemble_label, MATCH_ADVICE["Moderate"])

    return {
        # ── Colours ──
        "top_color": {
            "hex":     to_hex(top_rgb),
            "name":    COLOR_NAMES.get(top_cat, top_cat),
            "rgb":     top_rgb,
            "palette": top_palette,
        },
        "bottom_color": {
            "hex":     to_hex(bottom_rgb),
            "name":    COLOR_NAMES.get(bottom_cat, bottom_cat),
            "rgb":     bottom_rgb,
            "palette": bottom_palette,
        },

        # ── Match ──
        "delta_e":             delta_e,
        "delta_e_description": delta_e_description(delta_e),
        "match_label":         f"{ensemble_label} match",
        "confidence":          ensemble_conf,
        "advice":              advice["tip"],
        "advice_emoji":        advice["emoji"],

        # ── Model breakdown ──
        "model_details": {
            "mode":              "ensemble" if nn_model is not None else "random_forest_only",
            "ensemble_probs":    ensemble_probs,
            "random_forest":     {"label": rf_label,  "confidence": rf_conf},
            "neural_network":    {"label": nn_label,  "confidence": nn_conf}
                                  if nn_model is not None else None,
        },

        # ── CVD ──
        "cvd_type":    cvd_type,
        "top_hard":    is_hard_to_distinguish(top_cat, cvd_type),
        "bottom_hard": is_hard_to_distinguish(bottom_cat, cvd_type),
        "cvd_tip":     cvd_tip,
    }