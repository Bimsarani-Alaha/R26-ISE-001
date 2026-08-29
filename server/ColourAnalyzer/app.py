# ColourAnalyzer/app.py
import os
import sys
import warnings


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# SUPPRESS ALL WARNINGS AND VERBOSE OUTPUT
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')

import json
import uuid
import tempfile
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import aiofiles
import asyncio

# --- Simplified model imports (one file per model) ---
from model_color import ColorAnalyzer, remove_background, cleanup_mask
from model_cvd import CVDTransformer
from model_pattern import PatternTransformer

# ============================================
# PYDANTIC MODELS FOR REQUEST/VALIDATION
# ============================================

class URLRequest(BaseModel):
    url: HttpUrl
    cvd_type: Optional[str] = None
    has_person: Optional[bool] = False

class CVDRequest(BaseModel):
    url: HttpUrl
    cvd_type: str

class PatternRequest(BaseModel):
    url: HttpUrl

class BatchRequest(BaseModel):
    urls: List[HttpUrl]

# ============================================
# FASTAPI APP INITIALIZATION
# ============================================

app = FastAPI(
    title="T-Shirt Color Analyzer + CVD Generator + Pattern Recognizer API",
    description="Multi-model API for fashion analysis including multi-colour classification, CVD simulation, and pattern recognition",
    version="5.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================
# MODEL PATHS
# ============================================

MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Model 2 / Model 3 are already version-agnostic (npz weights + json config)
CVD_WEIGHTS_PATH = os.path.join(MODELS_DIR, 'cvd_generator_weights.npz')
CVD_CONFIG_PATH = os.path.join(MODELS_DIR, 'preprocessing_config.json')
PATTERN_WEIGHTS_PATH = os.path.join(MODELS_DIR, 'pattern_model_weights.npz')
PATTERN_CONFIG_PATH = os.path.join(MODELS_DIR, 'pattern_config.json')

# ============================================
# HELPERS
# ============================================

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def unique_temp_path(filename: str) -> str:
    ext = secure_filename(filename).rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}.{ext}")

def secure_filename(filename: str) -> str:
    """Simple secure filename - removes path traversal"""
    return os.path.basename(filename.replace('\\', '/'))

def image_to_base64(image: np.ndarray) -> str:
    """Convert numpy image to base64 string"""
    _, buffer = cv2.imencode('.jpg', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buffer).decode('utf-8')

async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file and return path"""
    temp_path = unique_temp_path(upload_file.filename)
    async with aiofiles.open(temp_path, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)
    return temp_path

async def download_image_from_url(url: str) -> np.ndarray:
    """Download image from URL and return as numpy array"""
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()

        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Could not decode image from URL")

        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# ============================================
# LAZY LOADING FOR MODELS
# ============================================

analyzer = None
cvd_transformer = None
pattern_model = None

def get_analyzer() -> ColorAnalyzer:
    """Load Model 1 - Multi-Colour Analyzer (v6, version-agnostic)"""
    global analyzer
    if analyzer is None:
        print("📦 Loading Model 1 (Multi-Colour Analyzer v6)...")
        try:
            # CHANGED: single directory, not four separate .keras/.json paths.
            analyzer = ColorAnalyzer(MODELS_DIR)
            print(f"✅ Model 1 loaded! Base classes: {analyzer.class_names}")
        except Exception as e:
            print(f"❌ Error loading Model 1: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load Color Analyzer: {str(e)}")
    return analyzer

def get_cvd_transformer() -> CVDTransformer:
    """Load Model 2 - CVD Transformer"""
    global cvd_transformer
    if cvd_transformer is None:
        print("📦 Loading Model 2 (CVD Transformer)...")
        try:
            cvd_transformer = CVDTransformer(CVD_WEIGHTS_PATH, CVD_CONFIG_PATH)
            print(f"✅ Model 2 loaded! CVD Types: {list(cvd_transformer.cvd_types)}")
        except Exception as e:
            print(f"❌ Error loading Model 2: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load CVD Transformer: {str(e)}")
    return cvd_transformer

def get_pattern_model() -> PatternTransformer:
    """Load Model 3 - Pattern Recognizer (version-agnostic)"""
    global pattern_model
    if pattern_model is None:
        print("📦 Loading Model 3 (Pattern Recognizer)...")
        try:
            pattern_model = PatternTransformer(PATTERN_WEIGHTS_PATH, PATTERN_CONFIG_PATH)
            print("✅ Model 3 loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading Model 3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load Pattern Recognizer: {str(e)}")
    return pattern_model

# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@app.get("/health")
async def health_check():
    """Check API health and model status"""
    return {
        'status': 'healthy',
        'model1_loaded': analyzer is not None,
        'model2_loaded': cvd_transformer is not None,
        'model3_loaded': pattern_model is not None
    }

# ============================================
# MODEL 1: MULTI-COLOUR ANALYSIS ENDPOINTS
# ============================================

@app.post("/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    has_person: bool = Form(False)
):
    """
    Analyze uploaded image for colours (Model 1 - Multi-Colour Analyzer v6).
    Set has_person=true if the photo shows a person wearing the shirt
    (so skin tones get excluded from the colour analysis).
    """
    temp_path = None
    try:
        print("📥 Received analyze request")

        if not allowed_file(image.filename):
            raise HTTPException(status_code=400, detail="File type not allowed. Use PNG, JPG, JPEG, or WEBP")

        # Save file
        temp_path = await save_upload_file(image)
        print(f"✅ File saved: {temp_path}")

        analyzer_instance = get_analyzer()
        print("✅ Analyzer instance ready")

        print("🔍 Starting colour analysis...")
        result, img_rgb = analyzer_instance.predict(temp_path, has_person=has_person)
        print(f"✅ Analysis complete: {result['colors']}")

        response = {
            'success': True,
            'base_color': result['base_color'],
            'base_color_confidence': round(result['base_color_confidence'] * 100, 2),
            'colors': [
                {
                    'name': c['color_name'],
                    'rgb': c['rgb'],
                    'percentage': c['percentage'],
                    'name_confidence': round(c['name_confidence'] * 100, 2),
                }
                for c in result['colors']
            ],
            'num_colors': result['num_colors'],
            'image_preview': image_to_base64(img_rgb),
            'status': 'analysis_complete'
        }

        print("✅ Response prepared")
        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in analyze_image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("✅ Temp file cleaned")
            except Exception as cleanup_err:
                print(f"⚠️  Could not remove temp file: {cleanup_err}")

@app.post("/analyze-url")
async def analyze_url(request: URLRequest):
    """
    Analyze image from URL using Model 1 (Multi-Colour Analyzer v6).
    """
    try:
        print("📥 Received analyze URL request")

        img_rgb = await download_image_from_url(str(request.url))

        analyzer_instance = get_analyzer()
        result = analyzer_instance.analyze_image(img_rgb, has_person=bool(request.has_person))

        response = {
            'success': True,
            'base_color': result['base_color'],
            'base_color_confidence': round(result['base_color_confidence'] * 100, 2),
            'colors': [
                {
                    'name': c['color_name'],
                    'rgb': c['rgb'],
                    'percentage': c['percentage'],
                    'name_confidence': round(c['name_confidence'] * 100, 2),
                }
                for c in result['colors']
            ],
            'num_colors': result['num_colors'],
            'image_preview': image_to_base64(img_rgb),
            'status': 'analysis_complete'
        }

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in analyze_url: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# MODEL 2: CVD GENERATOR ENDPOINTS
# ============================================

@app.post("/generate-cvd")
async def generate_cvd_image(
    image: UploadFile = File(...),
    cvd_type: str = Form(...)
):
    """
    Generate a CVD simulation image using Model 2 from file upload.
    """
    temp_path = None
    try:
        print("📥 Received CVD generation request")

        if not allowed_file(image.filename):
            raise HTTPException(status_code=400, detail="File type not allowed. Use PNG, JPG, JPEG, or WEBP")

        cvd_type = cvd_type.lower()
        if cvd_type not in ['protanopia', 'deuteranopia', 'tritanopia']:
            raise HTTPException(status_code=400, detail="Invalid CVD type. Choose protanopia, deuteranopia, or tritanopia.")

        temp_path = await save_upload_file(image)
        print(f"✅ File saved: {temp_path}")

        img = cv2.imread(temp_path)
        if img is None:
            raise HTTPException(status_code=400, detail="Could not read image file")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        transformer = get_cvd_transformer()
        print(f"🔍 Generating {cvd_type} simulation...")
        cvd_image_rgb = transformer.transform(img_rgb, cvd_type)
        print(f"✅ Generation complete. Output shape: {cvd_image_rgb.shape}")

        response = {
            'success': True,
            'cvd_image': image_to_base64(cvd_image_rgb),
            'cvd_type': cvd_type,
            'status': 'generation_complete'
        }

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in generate_cvd_image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("✅ Temp file cleaned")
            except Exception as cleanup_err:
                print(f"⚠️  Could not remove temp file: {cleanup_err}")

@app.post("/generate-cvd-url")
async def generate_cvd_image_url(request: CVDRequest):
    """
    Generate a CVD simulation image from a URL using Model 2.
    """
    try:
        print("📥 Received CVD generation request from URL")

        cvd_type = request.cvd_type.lower()
        if cvd_type not in ['protanopia', 'deuteranopia', 'tritanopia']:
            raise HTTPException(status_code=400, detail="Invalid CVD type. Choose protanopia, deuteranopia, or tritanopia.")

        img_rgb = await download_image_from_url(str(request.url))

        transformer = get_cvd_transformer()
        print(f"🔍 Generating {cvd_type} simulation from URL...")
        cvd_image_rgb = transformer.transform(img_rgb, cvd_type)
        print(f"✅ Generation complete. Output shape: {cvd_image_rgb.shape}")

        response = {
            'success': True,
            'cvd_image': image_to_base64(cvd_image_rgb),
            'cvd_type': cvd_type,
            'status': 'generation_complete'
        }

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in generate_cvd_image_url: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# MODEL 1: BATCH CLASSIFICATION
# ============================================

@app.post("/classify-batch")
async def classify_batch(
    images: List[UploadFile] = File(...),
    has_person: bool = Form(False)
):
    """
    Batch classify multiple images using Model 1 (Multi-Colour Analyzer v6)
    """
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images per batch")

    analyzer_instance = get_analyzer()
    results = []

    for file in images:
        if not allowed_file(file.filename):
            continue

        temp_path = None
        try:
            temp_path = await save_upload_file(file)

            result, _img_rgb = analyzer_instance.predict(temp_path, has_person=has_person)

            results.append({
                'filename': secure_filename(file.filename),
                'base_color': result['base_color'],
                'base_color_confidence': round(result['base_color_confidence'] * 100, 2),
                'colors': [
                    {
                        'name': c['color_name'],
                        'rgb': c['rgb'],
                        'percentage': c['percentage'],
                        'name_confidence': round(c['name_confidence'] * 100, 2),
                    }
                    for c in result['colors']
                ],
                'num_colors': result['num_colors'],
            })
        except Exception as e:
            results.append({
                'filename': secure_filename(file.filename),
                'error': str(e)
            })
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    return JSONResponse(content={
        'success': True,
        'results': results
    })

# ============================================
# MODEL 3: PATTERN RECOGNIZER
# ============================================

from sklearn.cluster import KMeans

def preprocess_for_pattern(image: np.ndarray):
    """
    Prepares an image for the Pattern Recognizer (Model 3).
    """
    # 1. Background Removal (GrabCut + cleanup) - shared with Model 1
    mask = remove_background(image)
    mask = cleanup_mask(mask)

    if mask.sum() < 500:
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype='uint8')
        cv2.ellipse(mask, (w // 2, h // 2), (int(w * 0.42), int(h * 0.42)), 0, 0, 360, 1, -1)

    garment_only = image.copy()
    garment_only[mask == 0] = 0

    h, w = mask.shape
    fg = mask.astype(bool)
    lab_img = cv2.cvtColor(garment_only, cv2.COLOR_RGB2LAB).astype(np.float32)
    ys, xs = np.where(fg)
    fg_pixels_lab = lab_img[ys, xs]

    if len(fg_pixels_lab) < 20:
        return np.zeros((h, w, 1), dtype=np.float32), mask

    km = KMeans(n_clusters=2, n_init=6, random_state=42)
    raw_clusters = km.fit_predict(fg_pixels_lab)

    mean_L = [fg_pixels_lab[raw_clusters == c, 0].mean() for c in (0, 1)]
    white_cluster_raw = int(np.argmax(mean_L))
    cluster_final = (raw_clusters == white_cluster_raw).astype(np.uint8)

    binary_mask = np.zeros((h, w), dtype=np.uint8)
    binary_mask[ys, xs] = cluster_final

    input_for_model = garment_only.astype(np.float32) / 255.0

    return input_for_model, binary_mask

def process_pattern_image(img_rgb: np.ndarray):
    """
    Common function to process pattern recognition on an RGB image.
    """
    input_for_model, binary_mask = preprocess_for_pattern(img_rgb)

    if input_for_model.shape[0] == 0 or input_for_model.shape[1] == 0:
        raise HTTPException(status_code=400, detail="Preprocessing failed. Could not isolate garment.")

    input_resized = cv2.resize(input_for_model, (224, 224))
    input_tensor = np.expand_dims(input_resized, axis=0)

    pattern_model_instance = get_pattern_model()
    print("🔍 Running Pattern Recognition...")

    prediction = pattern_model_instance.predict(input_tensor)
    pred_mask = (prediction[0, :, :, 0] > 0.5).astype(np.uint8) * 255

    h, w = img_rgb.shape[:2]
    pred_mask_resized = cv2.resize(pred_mask, (w, h), interpolation=cv2.INTER_NEAREST)

    original_garment_mask = preprocess_for_pattern(img_rgb)[1]
    final_mask = np.where(original_garment_mask > 0, pred_mask_resized, 0).astype(np.uint8)

    overlay = cv2.addWeighted(img_rgb, 0.3, np.zeros_like(img_rgb), 0, 0)
    overlay[final_mask > 0] = [255, 255, 255]

    edges = cv2.Canny(final_mask, 100, 200)
    overlay[edges > 0] = [255, 0, 0]

    combined_width = w * 2 + 40
    combined_height = h
    combined = np.full((combined_height, combined_width, 3), 20, dtype=np.uint8)
    combined[:h, :w] = img_rgb
    combined[:h, w+40:w+40+w] = overlay

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.8, min(1.5, combined_height / 400))
    thickness = max(2, int(font_scale * 2))

    cv2.rectangle(combined, (10, 10), (10 + 200, 10 + 50), (0, 0, 0), -1)
    cv2.rectangle(combined, (w+40+10, 10), (w+40+10 + 200, 10 + 50), (0, 0, 0), -1)
    cv2.putText(combined, 'Original', (15, 45), font, font_scale * 0.7, (255, 255, 255), thickness)
    cv2.putText(combined, 'Pattern Overlay', (w+40+15, 45), font, font_scale * 0.7, (255, 255, 255), thickness)
    cv2.rectangle(combined, (0, 0), (w, h), (64, 255, 218), 2)
    cv2.rectangle(combined, (w+40, 0), (w+40+w, h), (64, 255, 218), 2)

    pattern_image = np.zeros((h, w, 3), dtype=np.uint8)
    pattern_image[final_mask > 0] = [255, 255, 255]

    colored_pattern = img_rgb.copy()
    colored_pattern[final_mask == 0] = colored_pattern[final_mask == 0] * 0.2
    colored_pattern[final_mask > 0] = [255, 255, 255]

    response = {
        'success': True,
        'combined_image': image_to_base64(combined),
        'pattern_image': image_to_base64(pattern_image),
        'overlay_image': image_to_base64(overlay),
        'colored_pattern': image_to_base64(colored_pattern),
        'original_preview': image_to_base64(img_rgb),
        'mask_data': final_mask.tolist(),
        'dimensions': {'width': w, 'height': h},
        'status': 'pattern_generation_complete'
    }

    return response

@app.post("/pattern-recognize")
async def pattern_recognize(image: UploadFile = File(...)):
    temp_path = None
    try:
        print("📥 Received pattern recognition request")

        if not allowed_file(image.filename):
            raise HTTPException(status_code=400, detail="File type not allowed. Use PNG, JPG, JPEG, or WEBP")

        temp_path = await save_upload_file(image)
        print(f"✅ File saved: {temp_path}")

        img = cv2.imread(temp_path)
        if img is None:
            raise HTTPException(status_code=400, detail="Could not read image file")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        result = process_pattern_image(img_rgb)

        print("✅ Pattern recognition complete.")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in pattern_recognize: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("✅ Temp file cleaned")
            except Exception as cleanup_err:
                print(f"⚠️  Could not remove temp file: {cleanup_err}")

@app.post("/pattern-recognize-url")
async def pattern_recognize_url(request: PatternRequest):
    try:
        print("📥 Received pattern recognition request from URL")

        img_rgb = await download_image_from_url(str(request.url))

        result = process_pattern_image(img_rgb)

        print("✅ Pattern recognition complete from URL.")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in pattern_recognize_url: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "T-Shirt Color Analyzer + CVD Generator + Pattern Recognizer API",
        "version": "5.0.0",
        "endpoints": {
            "/health": "Check API health",
            "/analyze": "Upload image for multi-colour analysis, optional has_person form field (POST)",
            "/analyze-url": "Analyze image from URL, optional has_person field (POST)",
            "/generate-cvd": "Generate CVD simulation from upload (POST)",
            "/generate-cvd-url": "Generate CVD simulation from URL (POST)",
            "/classify-batch": "Batch classify multiple images, optional has_person form field (POST)",
            "/pattern-recognize": "Recognize pattern from upload (POST)",
            "/pattern-recognize-url": "Recognize pattern from URL (POST)"
        }
    }

# ============================================
# RUN SERVER (standalone testing only -- normally mounted by server.py)
# ============================================

if __name__ == '__main__':
    import uvicorn

    print("=" * 50)
    print("🚀 T-Shirt Color Analyzer + CVD Generator + Pattern Recognizer API (v5)")
    print("=" * 50)
    print(f"📁 Model 1 (Colour Analyzer) directory: {MODELS_DIR}")
    print(f"📁 Model 2 (CVD Transformer): {CVD_WEIGHTS_PATH}")
    print(f"📁 Model 3 (Pattern Recognizer): {PATTERN_WEIGHTS_PATH}")
    print("🌐 Server running at http://localhost:5000")
    print("📚 API Docs at http://localhost:5000/docs")
    print("=" * 50)
    print("ℹ️  Models will load on first request (lazy loading)")
    print("=" * 50)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )