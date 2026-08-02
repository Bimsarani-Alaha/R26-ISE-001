import os
import json
import numpy as np
import cv2

# SUPPRESS ALL TENSORFLOW VERBOSE OUTPUT
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import EfficientNetB2
from tensorflow.keras.applications.efficientnet import preprocess_input
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# ============================================
# FIX: Keras-version compatibility shim.
# ============================================
# Same root cause explained in cvd_transformer.py / keras_compat.py: a
# .keras file saved with a newer Keras version can fail to deserialize its
# InputLayer on an older installed Keras (TypeError about 'batch_shape'
# and 'optional'). Model 1 currently survives via the load_weights()
# fallback below, but wiring safe_load_model() into the primary
# load_model() attempt means it uses your REAL saved model + weights
# directly (the correct, exact restore) instead of relying on the
# less-precise by-name weight copy fallback.
from keras_compat import safe_load_model

# ============================================
# STANDALONE BACKGROUND REMOVAL FUNCTIONS
# ============================================

def estimate_background_color(image, border_frac=0.04):
    h, w = image.shape[:2]
    bw = max(2, int(min(h, w) * border_frac))
    top = image[:bw, :, :].reshape(-1, 3)
    bottom = image[-bw:, :, :].reshape(-1, 3)
    left = image[:, :bw, :].reshape(-1, 3)
    right = image[:, -bw:, :].reshape(-1, 3)
    border_pixels = np.vstack([top, bottom, left, right]).astype(np.float32)
    return np.median(border_pixels, axis=0)


def _lab_distance_map(image, bg_color_rgb):
    """FIX: New helper. Per-pixel LAB distance of `image` from a single
    RGB background color estimate. Used both to seed GrabCut and as the
    final safety-net filter in analyze()."""
    img_f = image.astype(np.float32) / 255.0
    lab_img = cv2.cvtColor(img_f, cv2.COLOR_RGB2LAB)
    bg_lab = cv2.cvtColor(
        np.uint8([[np.clip(bg_color_rgb, 0, 255)]]).astype(np.float32) / 255.0,
        cv2.COLOR_RGB2LAB
    )[0, 0]
    dist = np.sqrt(np.sum((lab_img - bg_lab) ** 2, axis=2))
    return dist, lab_img


def remove_background(image):

    h, w = image.shape[:2]
    bg_color_rgb = estimate_background_color(image)
    dist, _ = _lab_distance_map(image, bg_color_rgb)

    # --- Strategy 1: GrabCut seeded with a real trimap ---
    try:
        gc_mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
        gc_mask[dist > 18] = cv2.GC_PR_FGD   # probably foreground
        gc_mask[dist > 35] = cv2.GC_FGD      # definitely foreground
        gc_mask[dist < 6] = cv2.GC_BGD       # definitely background

        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        cv2.grabCut(image, gc_mask, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
        bm = np.where(
            (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 1, 0
        ).astype('uint8')

        k = np.ones((5, 5), np.uint8)
        bm = cv2.morphologyEx(bm, cv2.MORPH_CLOSE, k)
        bm = cv2.morphologyEx(bm, cv2.MORPH_OPEN, k)
        n, lab_cc, stats, _ = cv2.connectedComponentsWithStats(bm, 8)
        if n > 1:
            largest = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
            bm = (lab_cc == largest).astype('uint8')

     
        bm = cv2.erode(bm, np.ones((5, 5), np.uint8), iterations=1)

        if 0.05 < bm.mean() < 0.95:
            return bm
    except Exception:
        pass

    # --- Strategy 2: edge/contour fallback, also color-seeded ---
    try:
        fg_probable = (dist > 18).astype(np.uint8) * 255
        edges = cv2.Canny(fg_probable, 50, 150)
        edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            bm = np.zeros((h, w), dtype='uint8')
            cv2.drawContours(bm, [largest], -1, 1, -1)
            bm = cv2.morphologyEx(bm, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
            bm = cv2.erode(bm, np.ones((5, 5), np.uint8), iterations=1)
            if 0.05 < bm.mean() < 0.95:
                return bm
    except Exception:
        pass

    # --- Strategy 3: pure color-distance threshold, no shape assumption ---
    bm = (dist > 18).astype('uint8')
    bm = cv2.morphologyEx(bm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    bm = cv2.morphologyEx(bm, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab_cc, stats, _ = cv2.connectedComponentsWithStats(bm, 8)
    if n > 1:
        largest = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
        bm = (lab_cc == largest).astype('uint8')
    if bm.sum() > 100:
        return bm

    # --- Last resort: centered ellipse (unchanged) ---
    bm = np.zeros((h, w), dtype='uint8')
    cv2.ellipse(bm, (w // 2, h // 2), (int(w * 0.42), int(h * 0.42)), 0, 0, 360, 1, -1)
    return bm


def cleanup_mask(mask):
    """Remove noise, keep largest region, fill holes"""
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n > 1:
        largest = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
        mask = (lab == largest).astype('uint8')
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((10, 10), np.uint8))
    return mask


def preprocess_image(image, size=(224, 224)):
    """Preprocess for training"""
    img = cv2.resize(image, size)
    mask = remove_background(img)
    mask = cleanup_mask(mask)

    shirt = img.copy()
    shirt[mask == 0] = [0, 0, 0]

    lab = cv2.cvtColor(shirt, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    return enhanced, mask

# ============================================
# MAIN COLOR ANALYZER CLASS
# ============================================

class ColorAnalyzer:
    """
    FULL PIPELINE - Uses LAB analysis as PRIMARY
    CNN only as a GUIDE
    """

    def __init__(self, model_path, label_path):
        tf.get_logger().setLevel('ERROR')

        try:
            self.classes = np.load(label_path, allow_pickle=True)
            self.le = LabelEncoder()
            self.le.classes_ = self.classes
            print(f"✅ Labels loaded: {list(self.classes)}")
        except Exception as e:
            print(f"❌ Error loading labels: {str(e)}")
            raise

        try:
            print("🔨 Building model architecture...")
            base_model = EfficientNetB2(
                input_shape=(224, 224, 3),
                include_top=False,
                weights=None,
                pooling='avg'
            )

            inp = keras.Input(shape=(224, 224, 3))
            x = base_model(inp)
            x = layers.Dense(256, kernel_regularizer=keras.regularizers.l2(0.001))(x)
            x = layers.BatchNormalization()(x)
            x = layers.Activation('relu')(x)
            x = layers.Dropout(0.5)(x)
            x = layers.Dense(128, kernel_regularizer=keras.regularizers.l2(0.001))(x)
            x = layers.BatchNormalization()(x)
            x = layers.Activation('relu')(x)
            x = layers.Dropout(0.4)(x)
            out = layers.Dense(len(self.classes), activation='softmax')(x)

            self.model = keras.Model(inp, out)
            print("✅ Model architecture built")
        except Exception as e:
            print(f"❌ Error building model: {str(e)}")
            raise

        try:
            print(f"📥 Loading weights from: {model_path}")
            try:
                # FIX: use safe_load_model() so the InputLayer batch_shape/
                # optional Keras-version mismatch can't silently push this
                # onto the less-precise load_weights() fallback below.
                full_model = safe_load_model(model_path, compile=False)
                print("✅ Full model loaded!")

                for layer in self.model.layers:
                    for full_layer in full_model.layers:
                        if layer.name == full_layer.name:
                            try:
                                weights = full_layer.get_weights()
                                if weights:
                                    layer.set_weights(weights)
                                    print(f"  ✅ Copied weights for: {layer.name}")
                            except Exception as e:
                                print(f"  ⚠️  Could not copy {layer.name}: {e}")
                print("✅ Weights loaded successfully!")
            except Exception as e:
                print(f"⚠️  Full model load failed: {e}")
                try:
                    self.model.load_weights(model_path, skip_mismatch=True)
                    print("✅ Model weights loaded with skip_mismatch!")
                except Exception as e2:
                    print(f"❌ Both methods failed: {e2}")
                    raise
        except Exception as e:
            print(f"❌ Error loading weights: {str(e)}")
            print("⚠️  Continuing with random weights")

        # LAB color centers
        self.families = {
            'red':    {'center': [50, 60, 40],  'thresh': 30, 'merge': 25},
            'blue':   {'center': [35, 10, -45], 'thresh': 30, 'merge': 25},
            'green':  {'center': [50, -55, 45], 'thresh': 30, 'merge': 25},
            'yellow': {'center': [85, -15, 75], 'thresh': 28, 'merge': 22},
            'orange': {'center': [60, 35, 60],  'thresh': 28, 'merge': 22},
            'purple': {'center': [30, 40, -35], 'thresh': 30, 'merge': 25},
            'pink':   {'center': [70, 30, 10],  'thresh': 25, 'merge': 20},
            'brown':  {'center': [35, 18, 28],  'thresh': 28, 'merge': 22},
            'black':  {'center': [8, 2, 2],     'thresh': 20, 'merge': 15},
            'white':  {'center': [95, 0, 2],    'thresh': 20, 'merge': 15}
        }

    def _grid_segments(self, h, w, n=16):
       
        segs = np.zeros((h, w), dtype=np.int32)
        gh, gw = max(4, h // n), max(4, w // n)
        sid = 1
        for i in range(0, h, gh):
            for j in range(0, w, gw):
                segs[i:min(i + gh, h), j:min(j + gw, w)] = sid
                sid += 1
        return segs

    def _lab_dist(self, a, b):
        return np.sqrt(np.sum((np.array(a) - np.array(b)) ** 2))

    def _find_family(self, lab_pixel):
        best, bd = 'unknown', float('inf')
        for name, info in self.families.items():
            d = self._lab_dist(lab_pixel, info['center'])
            if d < bd and d < info['thresh']:
                bd = d
                best = name
        return best

    def _merge_similar(self, areas):
        from collections import defaultdict
        merged = defaultdict(float)
        processed = set()
        items = list(areas.items())

        for i, (c1, a1) in enumerate(items):
            if c1 in processed:
                continue
            total = a1
            processed.add(c1)

            for j, (c2, a2) in enumerate(items):
                if i == j or c2 in processed:
                    continue

                d = self._lab_dist(self.families[c1]['center'], self.families[c2]['center'])
                max_d = max(self.families[c1]['merge'], self.families[c2]['merge'])

                if d < max_d:
                    total += a2
                    processed.add(c2)

            merged[c1] = total

        return merged

    def analyze(self, image, cnn_bias=None):
        """FULL ANALYSIS PIPELINE - LAB is PRIMARY"""
        h, w = image.shape[:2]

        # STEP 1: Background removal
        mask = remove_background(image)
        mask = cleanup_mask(mask)

        if mask.sum() < 100:
            return [], mask, None

        # STEP 2: LAB conversion (reused below for the background safety net too)
        lab = cv2.cvtColor((image.astype(np.float32) / 255.0), cv2.COLOR_RGB2LAB)

        bg_color_rgb = estimate_background_color(image)
        bg_dist, _ = _lab_distance_map(image, bg_color_rgb)
        clean_mask = mask.copy()
        clean_mask[(bg_dist < 15) & (mask > 0)] = 0

        if clean_mask.sum() >= 0.15 * mask.sum():
            mask = clean_mask

        # STEP 3: Superpixels
        segments = self._grid_segments(h, w, 16)

        # STEP 4: Analyze each segment
        from collections import defaultdict
        areas = defaultdict(float)

        for sid in np.unique(segments):
            sm = (segments == sid) & (mask > 0)
            sa = sm.sum()

            if sa < 20:
                continue

            mean_lab = lab[sm].mean(axis=0)
            family = self._find_family(mean_lab)

            if family != "unknown":
                areas[family] += sa

        if not areas:
            return [], mask, segments

        # STEP 5: Merge similar colors
        merged = self._merge_similar(areas)

        # STEP 6: Calculate percentages & filter <7%
        total = sum(merged.values())
        pcts = {c: (a / total) * 100 for c, a in merged.items() if (a / total) * 100 >= 7}

        # STEP 7: Apply CNN bias (guide only)
        if cnn_bias and cnn_bias.get('conf', 0) > 0.7:
            cc = cnn_bias.get('color')
            if cc in pcts:
                pcts[cc] = min(100, pcts[cc] * 1.1)

        # STEP 8: Top 2 + normalize
        result = sorted(pcts.items(), key=lambda x: x[1], reverse=True)[:2]
        t = sum(p for _, p in result)
        if t > 0:
            result = [(c, (p / t) * 100) for c, p in result]

        return result, mask, segments

    def predict(self, image_path, show=False):
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # CNN bias (but we'll override if wrong)
        proc, _ = preprocess_image(img)
        pi = preprocess_input(proc.astype(np.float32))
        pred = self.model.predict(np.expand_dims(pi, 0), verbose=0)[0]
        bias = {
            'color': self.le.classes_[np.argmax(pred)],
            'conf': float(pred.max())
        }

        # LAB analysis is PRIMARY
        colors, mask, segs = self.analyze(img, bias)

        return colors, bias, img