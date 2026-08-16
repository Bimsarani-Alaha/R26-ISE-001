

import os
import json
import importlib.util

import numpy as np
import cv2
from PIL import Image, ImageOps
from sklearn.cluster import KMeans
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# ============================================================
# CIE-Lab helpers (same pure-NumPy implementation as the notebook,
# needed by the colour-name classifier's input pipeline)
# ============================================================

_M_RGB2XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
])
_D65_WHITE = np.array([0.95047, 1.00000, 1.08883])


def rgb_to_lab(rgb):
    """Vectorised sRGB (0-255) -> CIE-Lab conversion. Accepts shape (...,3)."""
    rgb = np.asarray(rgb, dtype=np.float64) / 255.0
    mask = rgb > 0.04045
    rgb_lin = np.where(mask, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)

    xyz = rgb_lin @ _M_RGB2XYZ.T
    xyz = xyz / _D65_WHITE

    delta = 6.0 / 29.0
    mask2 = xyz > delta ** 3
    f = np.where(mask2, np.cbrt(xyz), xyz / (3 * delta ** 2) + 4.0 / 29.0)

    L = 116.0 * f[..., 1] - 16.0
    a = 500.0 * (f[..., 0] - f[..., 1])
    b = 200.0 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def normalise_lab(lab):
    """Squashes Lab into a roughly [0,1] range, matching training."""
    L = lab[..., 0] / 100.0
    a = (lab[..., 1] + 128.0) / 255.0
    b = (lab[..., 2] + 128.0) / 255.0
    return np.stack([L, a, b], axis=-1).astype(np.float32)


# ============================================================
# Cross-version weight loading
# ============================================================

def _load_architecture_module(py_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, py_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_weights_from_npz(model, weights_npz_path):
    """Loads an .npz produced by the training notebook's export_layer_weights()
    back into a freshly-built model of the SAME architecture."""
    data = np.load(weights_npz_path)
    by_layer = {}
    for key in data.files:
        idx_str, _name, w_str = key.split("__")
        idx = int(idx_str)
        w_idx = int(w_str[1:])
        by_layer.setdefault(idx, {})[w_idx] = data[key]

    layers_list = model.layers
    copied = 0
    for idx, weight_map in by_layer.items():
        layer = layers_list[idx]
        ordered = [weight_map[j] for j in sorted(weight_map)]
        layer.set_weights(ordered)
        copied += 1
    return copied


# ============================================================
# Background removal / mask cleanup
# (also imported directly by app.py's Model-3 pattern preprocessing:
#  `from model_color import ColorAnalyzer, remove_background, cleanup_mask`)
# ============================================================

def remove_background(image_rgb, iterations=5, margin_ratio=0.03):
    """GrabCut background removal on a raw RGB uint8 numpy array.
    Returns a uint8 mask (1 = garment/foreground, 0 = background)."""
    h, w = image_rgb.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    mx, my = max(1, int(w * margin_ratio)), max(1, int(h * margin_ratio))
    rect = (mx, my, max(1, w - 2 * mx), max(1, h - 2 * my))

    try:
        cv2.grabCut(image_rgb, mask, rect, bgd_model, fgd_model, iterations, cv2.GC_INIT_WITH_RECT)
        binary_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    except cv2.error:
        binary_mask = np.ones((h, w), dtype=np.uint8)

    return binary_mask


def cleanup_mask(mask, min_area_ratio=0.01):
    """Morphological cleanup + largest connected-component isolation."""
    mask = (mask > 0).astype(np.uint8)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    num, labels_im, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num <= 1:
        return mask

    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_idx = 1 + int(np.argmax(areas))
    total_px = mask.shape[0] * mask.shape[1]
    if areas[largest_idx - 1] < min_area_ratio * total_px:
        return mask
    return (labels_im == largest_idx).astype(np.uint8)


def exclude_skin(image_rgb, mask):
    """Removes likely-skin pixels (YCrCb thresholding) from a garment mask."""
    ycrcb = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2YCrCb)
    Y, Cr, Cb = ycrcb[:, :, 0], ycrcb[:, :, 1], ycrcb[:, :, 2]
    skin_mask = (Cr > 135) & (Cr < 180) & (Cb > 85) & (Cb < 135) & (Y > 60)
    return (mask.astype(bool) & (~skin_mask)).astype(np.uint8)


# ============================================================
# Production inference class
# ============================================================

class ColorAnalyzer:
    """Version-agnostic Model 1 (multi-colour analyzer).

    Construct with the directory containing the exported artifacts:
        analyzer = ColorAnalyzer(MODEL_DIR)

    where MODEL_DIR has:
        base_color_architecture.py, base_color_model_weights.npz, base_color_config.json
        colour_name_architecture.py, colour_name_model_weights.npz, colour_name_config.json
        colour_name_classes.json
    """

    def __init__(self, model_dir, colour_name_classes_path=None):
        self.model_dir = model_dir

        # ---- Base 10-colour CNN ----
        base_arch = _load_architecture_module(
            os.path.join(model_dir, "base_color_architecture.py"), "base_color_architecture")
        with open(os.path.join(model_dir, "base_color_config.json")) as f:
            self.base_config = json.load(f)
        self.img_size = tuple(self.base_config["img_size"])
        self.class_names = self.base_config["class_names"]

        self.base_model, _ = base_arch.build_base_color_model(
            num_classes=self.base_config["num_classes"],
            img_size=self.img_size,
            backbone_weights=None,
        )
        load_weights_from_npz(self.base_model, os.path.join(model_dir, "base_color_model_weights.npz"))

        # ---- Colour-name classifier ----
        cname_arch = _load_architecture_module(
            os.path.join(model_dir, "colour_name_architecture.py"), "colour_name_architecture")
        with open(os.path.join(model_dir, "colour_name_config.json")) as f:
            self.cname_config = json.load(f)

        classes_path = colour_name_classes_path or os.path.join(model_dir, "colour_name_classes.json")
        with open(classes_path) as f:
            _cdb = json.load(f)
        self.color_names_arr = np.array(_cdb["names"])
        self.color_rgb = np.array(_cdb["rgb"], dtype=np.float64)

        self.color_name_model = cname_arch.build_color_name_model(self.cname_config["num_classes"])
        load_weights_from_npz(self.color_name_model, os.path.join(model_dir, "colour_name_model_weights.npz"))

        print(f"[ColorAnalyzer] ready. Base classes: {self.class_names} | "
              f"{len(self.color_names_arr)} colour names loaded.")

    # ---- internal helpers ----

    def _predict_base_color(self, pil_img):
        img = pil_img.convert("RGB").resize(self.img_size)
        arr = preprocess_input(np.array(img, dtype=np.float32))
        arr = np.expand_dims(arr, axis=0)
        preds = self.base_model.predict(arr, verbose=0)[0]
        idx = int(np.argmax(preds))
        return self.class_names[idx], float(preds[idx])

    def _closest_color_name(self, rgb):
        lab = rgb_to_lab(np.array(rgb, dtype=np.float64)).reshape(1, 3)
        x = normalise_lab(lab)
        preds = self.color_name_model.predict(x, verbose=0)[0]
        idx = int(np.argmax(preds))
        return str(self.color_names_arr[idx]), self.color_rgb[idx], float(preds[idx])

    def _color_breakdown(self, rgb_array, mask, k=6, min_percent=2.0):
        pixels = rgb_array[mask.astype(bool)]
        if len(pixels) == 0:
            return []
        k_eff = min(k, len(pixels))
        kmeans = KMeans(n_clusters=k_eff, n_init=8, random_state=42).fit(pixels)
        labels_ = kmeans.labels_
        centers = kmeans.cluster_centers_

        total = len(labels_)
        breakdown = []
        for i in range(k_eff):
            pct = 100.0 * np.sum(labels_ == i) / total
            if pct < min_percent:
                continue
            name, _ref_rgb, conf = self._closest_color_name(centers[i])
            breakdown.append({
                "color_name": name,
                "rgb": tuple(int(v) for v in centers[i]),
                "percentage": round(float(pct), 2),
                "name_confidence": conf,
            })
        breakdown.sort(key=lambda d: d["percentage"], reverse=True)
        return breakdown

    # ---- public API (matches app.py's usage exactly) ----

    def analyze_image(self, image_rgb, has_person=False):
        """image_rgb: HxWx3 RGB uint8 numpy array."""
        pil_img = Image.fromarray(image_rgb)

        mask = remove_background(image_rgb)
        if has_person:
            mask = exclude_skin(image_rgb, mask)
        mask = cleanup_mask(mask)

        base_color, base_conf = self._predict_base_color(pil_img)
        breakdown = self._color_breakdown(image_rgb, mask, k=6, min_percent=2.0)

        return {
            "base_color": base_color,
            "base_color_confidence": base_conf,
            "colors": breakdown,
            "num_colors": len(breakdown),
        }

    def predict(self, image_path, has_person=False):
        """image_path: path to an image file on disk. Returns (result, img_rgb)."""
        pil_img = Image.open(image_path)
        pil_img = ImageOps.exif_transpose(pil_img)
        pil_img = pil_img.convert("RGB")
        img_rgb = np.array(pil_img)

        result = self.analyze_image(img_rgb, has_person=has_person)
        return result, img_rgb