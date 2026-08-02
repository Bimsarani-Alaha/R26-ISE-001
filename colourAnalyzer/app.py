# backend/app.py
import os
import sys
import warnings

# SUPPRESS ALL WARNINGS AND VERBOSE OUTPUT
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')

import json
import uuid
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from color_analyzer import ColorAnalyzer
import base64
from io import BytesIO
from PIL import Image

# Import the CVD Transformer
from cvd_transformer import CVDTransformer

# ============================================
# FIX: Import background removal functions from color_analyzer
# ============================================
from color_analyzer import remove_background, cleanup_mask

# ============================================
# FIX: Keras-version compatibility shim (see keras_compat.py for the full
# explanation). This is a defense-in-depth safety net for Model 3's loader
# below - the REAL, complete fix is matching your TensorFlow/Keras version
# to the one the notebooks trained with (TensorFlow==2.20.0 / Keras>=3.10,
# see requirements.txt). Once your environment matches, this shim is a
# harmless no-op; it only activates if it ever sees the newer config keys.
# ============================================
from keras_compat import safe_load_model

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


MODEL_PATH = 'models/final_model.keras'
LABEL_PATH = 'models/label_classes.npy'

CVD_MODEL_PATH = 'models/cvd_model.keras'
CVD_CONFIG_PATH = 'models/preprocessing_config.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_temp_path(filename):
    ext = secure_filename(filename).rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}.{ext}")


def image_to_base64(image):
    """Convert numpy image to base64 string"""
    _, buffer = cv2.imencode('.jpg', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buffer).decode('utf-8')

# Initialize analyzers (lazy loading)
analyzer = None
cvd_transformer = None

def get_analyzer():
    """Load Model 1 - Color Analyzer"""
    global analyzer
    if analyzer is None:
        print("📦 Loading Model 1 (Color Analyzer)...")
        try:
            analyzer = ColorAnalyzer(MODEL_PATH, LABEL_PATH)
            print(f"✅ Model 1 loaded! Labels: {list(analyzer.classes)}")
        except Exception as e:
            print(f"❌ Error loading Model 1: {str(e)}")
            raise e
    return analyzer

def get_cvd_transformer():
    """Load Model 2 - CVD Transformer"""
    global cvd_transformer
    if cvd_transformer is None:
        print("📦 Loading Model 2 (CVD Transformer)...")
        try:
            cvd_transformer = CVDTransformer(CVD_MODEL_PATH, CVD_CONFIG_PATH)
            print(f"✅ Model 2 loaded! CVD Types: {list(cvd_transformer.cvd_types)}")
        except Exception as e:
            print(f"❌ Error loading Model 2: {str(e)}")
            raise e
    return cvd_transformer

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model1_loaded': analyzer is not None,
        'model2_loaded': cvd_transformer is not None
    })

# ============================================
# MODEL 1: COLOR ANALYSIS ENDPOINT
# ============================================

@app.route('/analyze', methods=['POST'])
def analyze_image():
    """
    Analyze uploaded image for colors (Model 1 - Color Classifier)
    """
    temp_path = None
    try:
        print("📥 Received analyze request")

        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use PNG, JPG, JPEG, or WEBP'}), 400

        temp_path = unique_temp_path(file.filename)
        file.save(temp_path)
        print(f"✅ File saved: {temp_path}")

        analyzer_instance = get_analyzer()
        print("✅ Analyzer instance ready")

        print("🔍 Starting color analysis...")
       
        colors, bias, img = analyzer_instance.predict(temp_path)
        print(f"✅ Analysis complete: {colors}")

        cnn_color = bias['color']
        cnn_conf = bias['conf'] * 100
        lab_colors = [c for c, _ in colors]

        if cnn_color not in lab_colors:
            print(f"⚠️  CNN predicted '{cnn_color}' but LAB detected {lab_colors}")
            cnn_conf = 10.0
            bias['color'] = f"{cnn_color} (CNN)"
            bias['conf'] = 0.1
        else:
            print(f"✅ CNN predicted '{cnn_color}' which matches LAB analysis")
            cnn_conf = min(95.0, cnn_conf * 1.1)

        response = {
            'success': True,
            'colors': [{'name': c, 'percentage': round(p, 2)} for c, p in colors],
            'cnn_guide': {
                'color': cnn_color,
                'confidence': round(cnn_conf, 2)
            },
            'num_colors': len(colors),
            'image_preview': image_to_base64(img),
            'status': 'analysis_complete'
        }

        print("✅ Response prepared")
        return jsonify(response)

    except Exception as e:
        print(f"❌ ERROR in analyze_image: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("✅ Temp file cleaned")
            except Exception as cleanup_err:
                print(f"⚠️  Could not remove temp file: {cleanup_err}")

# ============================================
# MODEL 1: COLOR ANALYSIS FROM URL
# ============================================

@app.route('/analyze-url', methods=['POST'])
def analyze_url():
    """
    Analyze image from URL using Model 1
    """
    temp_path = None
    try:
        data = request.get_json()

        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400

        import requests

        response = requests.get(data['url'], timeout=10)
        response.raise_for_status()

        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': 'Could not decode image from URL'}), 400

        temp_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}.jpg")
        cv2.imwrite(temp_path, img)

        analyzer_instance = get_analyzer()
        colors, bias, _ = analyzer_instance.predict(temp_path)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        cnn_color = bias['color']
        cnn_conf = bias['conf'] * 100
        lab_colors = [c for c, _ in colors]

        if cnn_color not in lab_colors:
            cnn_conf = 10.0
            bias['color'] = f"{cnn_color} (CNN)"
            bias['conf'] = 0.1
        else:
            cnn_conf = min(95.0, cnn_conf * 1.1)

        response_json = {
            'success': True,
            'colors': [{'name': c, 'percentage': round(p, 2)} for c, p in colors],
            'cnn_guide': {
                'color': cnn_color,
                'confidence': round(cnn_conf, 2)
            },
            'num_colors': len(colors),
            'image_preview': image_to_base64(img_rgb),
            'status': 'analysis_complete'
        }

        return jsonify(response_json)

    except Exception as e:
        print(f"❌ ERROR in analyze_url: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                print(f"⚠️  Could not remove temp file: {cleanup_err}")

# ============================================
# MODEL 2: CVD GENERATOR ENDPOINT
# ============================================

@app.route('/generate-cvd', methods=['POST'])
def generate_cvd_image():
    """
    Generate a CVD simulation image using Model 2 from file upload.
    """
    temp_path = None
    try:
        print("📥 Received CVD generation request")

        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400

        cvd_type = request.form.get('cvd_type', '').lower()
        if cvd_type not in ['protanopia', 'deuteranopia', 'tritanopia']:
            return jsonify({'error': 'Invalid CVD type. Choose protanopia, deuteranopia, or tritanopia.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use PNG, JPG, JPEG, or WEBP'}), 400

        temp_path = unique_temp_path(file.filename)
        file.save(temp_path)
        print(f"✅ File saved: {temp_path}")

        img = cv2.imread(temp_path)
        if img is None:
            return jsonify({'error': 'Could not read image file'}), 400
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

        return jsonify(response)

    except Exception as e:
        print(f"❌ ERROR in generate_cvd_image: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("✅ Temp file cleaned")
            except Exception as cleanup_err:
                print(f"⚠️  Could not remove temp file: {cleanup_err}")

# ============================================
# MODEL 2: CVD GENERATOR FROM URL
# ============================================

@app.route('/generate-cvd-url', methods=['POST'])
def generate_cvd_image_url():
    """
    Generate a CVD simulation image from a URL using Model 2.
    """
    try:
        print("📥 Received CVD generation request from URL")

        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400

        cvd_type = data.get('cvd_type', '').lower()
        if cvd_type not in ['protanopia', 'deuteranopia', 'tritanopia']:
            return jsonify({'error': 'Invalid CVD type. Choose protanopia, deuteranopia, or tritanopia.'}), 400

        import requests
        response = requests.get(data['url'], timeout=10)
        response.raise_for_status()

        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': 'Could not decode image from URL'}), 400

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        transformer = get_cvd_transformer()
        print(f"🔍 Generating {cvd_type} simulation from URL...")
        cvd_image_rgb = transformer.transform(img_rgb, cvd_type)
        print(f"✅ Generation complete. Output shape: {cvd_image_rgb.shape}")

        response_json = {
            'success': True,
            'cvd_image': image_to_base64(cvd_image_rgb),
            'cvd_type': cvd_type,
            'status': 'generation_complete'
        }

        return jsonify(response_json)

    except Exception as e:
        print(f"❌ ERROR in generate_cvd_image_url: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# MODEL 1: BATCH CLASSIFICATION
# ============================================

@app.route('/classify-batch', methods=['POST'])
def classify_batch():
    """
    Batch classify multiple images using Model 1
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No image files provided'}), 400

        files = request.files.getlist('images')

        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 images per batch'}), 400

        analyzer_instance = get_analyzer()

        results = []

        for file in files:
            if not allowed_file(file.filename):
                continue

            temp_path = unique_temp_path(file.filename)
            file.save(temp_path)

            try:
                colors, bias, _ = analyzer_instance.predict(temp_path)

                cnn_color = bias['color']
                cnn_conf = bias['conf'] * 100
                lab_colors = [c for c, _ in colors]

                if cnn_color not in lab_colors:
                    cnn_conf = 10.0
                else:
                    cnn_conf = min(95.0, cnn_conf * 1.1)

                results.append({
                    'filename': secure_filename(file.filename),
                    'colors': [{'name': c, 'percentage': round(p, 2)} for c, p in colors],
                    'cnn_guide': cnn_color,
                    'confidence': round(cnn_conf, 2)
                })
            except Exception as e:
                results.append({
                    'filename': secure_filename(file.filename),
                    'error': str(e)
                })
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        print(f"❌ ERROR in classify_batch: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# MODEL 3: PATTERN RECOGNIZER
# ============================================

# Import necessary libraries for the pattern recognizer
import tensorflow as tf
from tensorflow import keras
from sklearn.cluster import KMeans
import pandas as pd

PATTERN_MODEL_PATH = 'models/pattern_model.keras'
pattern_model = None

def get_pattern_model():
    """Load Model 3 - Pattern Recognizer"""
    global pattern_model
    if pattern_model is None:
        print("📦 Loading Model 3 (Pattern Recognizer)...")
        try:
            # FIX: was keras.models.load_model(PATTERN_MODEL_PATH, compile=False).
            # safe_load_model() applies the keras_compat InputLayer patch as a
            # safety net; the real fix is matching TensorFlow/Keras to the
            # notebook's training environment (see requirements.txt).
            pattern_model = safe_load_model(PATTERN_MODEL_PATH, compile=False)
            print("✅ Model 3 loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading Model 3: {str(e)}")
            raise RuntimeError(
                f"Could not load Pattern Recognizer model from '{PATTERN_MODEL_PATH}'. "
                "Please ensure the file exists and is the correct format (e.g., final_model.keras)."
            ) from e
    return pattern_model

def preprocess_for_pattern(image):
    """
    Prepares an image for the Pattern Recognizer (Model 3).
    This replicates the logic from the training notebook (ColorBlind3-4).
    """
    # 1. Background Removal (GrabCut + cleanup) - Use the same function from ColorAnalyzer
    mask = remove_background(image)
    mask = cleanup_mask(mask)
    
    if mask.sum() < 500:
        # If mask is too small, use a centered ellipse as a fallback
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype='uint8')
        cv2.ellipse(mask, (w // 2, h // 2), (int(w * 0.42), int(h * 0.42)), 0, 0, 360, 1, -1)
    
    # 2. Isolate the garment using the mask
    garment_only = image.copy()
    garment_only[mask == 0] = 0

    # 3. Build the pseudo-label (the "pixel table" logic from the notebook)
    #    This creates the black & white cluster mask based on color clustering.
    h, w = mask.shape
    fg = mask.astype(bool)
    lab_img = cv2.cvtColor(garment_only, cv2.COLOR_RGB2LAB).astype(np.float32)
    ys, xs = np.where(fg)
    fg_pixels_lab = lab_img[ys, xs]

    # If there are not enough foreground pixels, return a blank mask
    if len(fg_pixels_lab) < 20:
        return np.zeros((h, w, 1), dtype=np.float32), mask

    # Perform KMeans clustering to separate into two colors (black/white)
    km = KMeans(n_clusters=2, n_init=6, random_state=42)
    raw_clusters = km.fit_predict(fg_pixels_lab)
    
    # Re-order clusters by mean lightness (higher L = white cluster)
    mean_L = [fg_pixels_lab[raw_clusters == c, 0].mean() for c in (0, 1)]
    white_cluster_raw = int(np.argmax(mean_L))
    cluster_final = (raw_clusters == white_cluster_raw).astype(np.uint8)

    # Create the target mask (1 = white/foreground, 0 = black/background)
    binary_mask = np.zeros((h, w), dtype=np.uint8)
    binary_mask[ys, xs] = cluster_final
    
    # The input for the U-Net is the garment-only image, normalized to [0,1]
    input_for_model = garment_only.astype(np.float32) / 255.0
    
    return input_for_model, binary_mask

# ============================================
# MODEL 3: PATTERN RECOGNIZER FROM FILE
# ============================================

@app.route('/pattern-recognize', methods=['POST'])
def pattern_recognize():
    """
    Upload an image and get the black & white pattern mask using Model 3.
    Returns a combined comparison view with overlay.
    """
    temp_path = None
    try:
        print("📥 Received pattern recognition request")

        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use PNG, JPG, JPEG, or WEBP'}), 400

        temp_path = unique_temp_path(file.filename)
        file.save(temp_path)
        print(f"✅ File saved: {temp_path}")

        img = cv2.imread(temp_path)
        if img is None:
            return jsonify({'error': 'Could not read image file'}), 400
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Process the pattern
        result = process_pattern_image(img_rgb)

        print("✅ Pattern recognition complete.")
        return jsonify(result)

    except Exception as e:
        print(f"❌ ERROR in pattern_recognize: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("✅ Temp file cleaned")
            except Exception as cleanup_err:
                print(f"⚠️  Could not remove temp file: {cleanup_err}")

# ============================================
# MODEL 3: PATTERN RECOGNIZER FROM URL
# ============================================

@app.route('/pattern-recognize-url', methods=['POST'])
def pattern_recognize_url():
    """
    Process pattern recognition from a URL using Model 3.
    """
    try:
        print("📥 Received pattern recognition request from URL")

        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400

        import requests
        response = requests.get(data['url'], timeout=10)
        response.raise_for_status()

        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': 'Could not decode image from URL'}), 400

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Process the pattern
        result = process_pattern_image(img_rgb)

        print("✅ Pattern recognition complete from URL.")
        return jsonify(result)

    except Exception as e:
        print(f"❌ ERROR in pattern_recognize_url: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# COMMON PATTERN PROCESSING FUNCTION
# ============================================

def process_pattern_image(img_rgb):
    """
    Common function to process pattern recognition on an RGB image.
    Returns the response dictionary.
    """
    # --- Preprocess for the Pattern Recognizer ---
    input_for_model, binary_mask = preprocess_for_pattern(img_rgb)
    
    if input_for_model.shape[0] == 0 or input_for_model.shape[1] == 0:
        return {'error': 'Preprocessing failed. Could not isolate garment.'}, 400

    # Prepare input for the U-Net: (1, 224, 224, 3)
    input_resized = cv2.resize(input_for_model, (224, 224))
    input_tensor = np.expand_dims(input_resized, axis=0)

    # --- Load and run the model ---
    pattern_model = get_pattern_model()
    print("🔍 Running Pattern Recognition...")
    
    # Predict the mask (sigmoid output between 0 and 1)
    prediction = pattern_model.predict(input_tensor, verbose=0)
    pred_mask = (prediction[0, :, :, 0] > 0.5).astype(np.uint8) * 255

    # Resize the prediction back to the original image size
    h, w = img_rgb.shape[:2]
    pred_mask_resized = cv2.resize(pred_mask, (w, h), interpolation=cv2.INTER_NEAREST)
    
    # Apply the original garment mask to remove any stray background predictions
    original_garment_mask = preprocess_for_pattern(img_rgb)[1]
    final_mask = np.where(original_garment_mask > 0, pred_mask_resized, 0).astype(np.uint8)

    # ============================================
    # IMPROVED VISUALIZATION - WIDE COMPARISON VIEW
    # ============================================
    
    # 1. Create overlay image (pattern on original with darkened background)
    overlay = cv2.addWeighted(img_rgb, 0.3, np.zeros_like(img_rgb), 0, 0)
    overlay[final_mask > 0] = [255, 255, 255]  # White pattern on darkened original
    
    # Add red outline around the pattern for clarity
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.Canny(final_mask, 100, 200)
    overlay[edges > 0] = [255, 0, 0]  # Red outline
    
    # 2. Create a wider combined view with original + overlay side by side
    combined_width = w * 2 + 40  # 40px gap between images
    combined_height = h
    
    # Create the combined image with dark background
    combined = np.full((combined_height, combined_width, 3), 20, dtype=np.uint8)
    
    # Place original image on the left
    combined[:h, :w] = img_rgb
    
    # Place overlay on the right with a gap
    combined[:h, w+40:w+40+w] = overlay
    
    # Add labels with larger text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.8, min(1.5, combined_height / 400))
    thickness = max(2, int(font_scale * 2))
    
    # Dark background for text
    cv2.rectangle(combined, (10, 10), (10 + 200, 10 + 50), (0, 0, 0), -1)
    cv2.rectangle(combined, (w+40+10, 10), (w+40+10 + 200, 10 + 50), (0, 0, 0), -1)
    
    cv2.putText(combined, 'Original', (15, 45), font, font_scale * 0.7, (255, 255, 255), thickness)
    cv2.putText(combined, 'Pattern Overlay', (w+40+15, 45), font, font_scale * 0.7, (255, 255, 255), thickness)
    
    # Add a thin border around each section
    cv2.rectangle(combined, (0, 0), (w, h), (64, 255, 218), 2)
    cv2.rectangle(combined, (w+40, 0), (w+40+w, h), (64, 255, 218), 2)

    # 3. Create a pure pattern image for download (black background, white pattern)
    pattern_image = np.zeros((h, w, 3), dtype=np.uint8)
    pattern_image[final_mask > 0] = [255, 255, 255]

    # 4. Also create a mask visualization with colored overlay for better visibility
    colored_pattern = img_rgb.copy()
    colored_pattern[final_mask == 0] = colored_pattern[final_mask == 0] * 0.2
    colored_pattern[final_mask > 0] = [255, 255, 255]

    # --- Prepare the response ---
    response = {
        'success': True,
        'combined_image': image_to_base64(combined),
        'pattern_image': image_to_base64(pattern_image),
        'overlay_image': image_to_base64(overlay),
        'colored_pattern': image_to_base64(colored_pattern),
        'original_preview': image_to_base64(img_rgb),
        'mask_data': final_mask.tolist(),
        'dimensions': {
            'width': w,
            'height': h
        },
        'status': 'pattern_generation_complete'
    }
    
    return response


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 T-Shirt Color Analyzer + CVD Generator + Pattern Recognizer API")
    print("=" * 50)
    print(f"📁 Model 1 (Color Classifier): {MODEL_PATH}")
    print(f"🏷️  Model 1 Labels: {LABEL_PATH}")
    print(f"📁 Model 2 (CVD Transformer): {CVD_MODEL_PATH}")
    print(f"📁 Model 3 (Pattern Recognizer): {PATTERN_MODEL_PATH}")
    print("🌐 Server running at http://localhost:5000")
    print("=" * 50)
    print("ℹ️  Models will load on first request (lazy loading)")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)