# ColourAnalyzer/model_color.py
import os
import json
import importlib.util

import numpy as np
import cv2
from PIL import Image, ImageOps
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# ============================================================
# CIE-Lab helpers (same pure-NumPy implementation as the notebook,
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



def _lab_merge_distance(lab_a, lab_b, l_weight_chromatic=0.22, l_weight_neutral=0.55,
                         neutral_chroma_thresh=16.0):
    """Perceptual distance between two Lab cluster centers, used only to
    decide whether they should be merged (not for colour-name lookup)."""
    chroma_a = float(np.hypot(lab_a[1], lab_a[2]))
    chroma_b = float(np.hypot(lab_b[1], lab_b[2]))
    avg_chroma = (chroma_a + chroma_b) / 2.0

    l_weight = l_weight_neutral if avg_chroma < neutral_chroma_thresh else l_weight_chromatic

    dL = (lab_a[0] - lab_b[0]) * l_weight
    da = lab_a[1] - lab_b[1]
    db = lab_a[2] - lab_b[2]
    return float(np.sqrt(dL ** 2 + da ** 2 + db ** 2))


def merge_similar_clusters(centers_rgb, counts, merge_distance=16.0,
                            l_weight_chromatic=0.22, l_weight_neutral=0.55,
                            neutral_chroma_thresh=16.0):
    """Agglomeratively merges KMeans cluster centers that are perceptually
    the same colour (differing mainly by lighting), using the adaptive
    Lab distance above.

    Args:
        centers_rgb: (n, 3) array of KMeans cluster centers in RGB.
        counts: (n,) array of pixel counts per cluster.
        merge_distance: clusters closer than this (in the adaptive Lab
            metric) get merged. Larger = more aggressive merging
            (fewer, broader colour groups). 14-20 is a reasonable
            practical range; tune against real sample photos.

    Returns:
        group_ids: (n,) int array assigning each input cluster to a
            merged group (1-indexed, from scipy).
    """
    n = len(centers_rgb)
    if n <= 1:
        return np.ones(n, dtype=int)

    labs = rgb_to_lab(np.asarray(centers_rgb, dtype=np.float64))
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = _lab_merge_distance(
                labs[i], labs[j],
                l_weight_chromatic=l_weight_chromatic,
                l_weight_neutral=l_weight_neutral,
                neutral_chroma_thresh=neutral_chroma_thresh,
            )
            dist[i, j] = dist[j, i] = d

    condensed = squareform(dist, checks=False)
    Z = linkage(condensed, method="average")
    group_ids = fcluster(Z, t=merge_distance, criterion="distance")
    return group_ids


# ============================================================
# Single / Dual / Multi classification
# ============================================================

def classify_and_flag_colors(breakdown, sub_color_threshold=5.0):
    """Mutates `breakdown` in place, adding an `is_sub_color` bool to
    every entry, and returns the shirt-level category string:
    'single', 'dual', or 'multi'.

    `breakdown` must already be sorted descending by 'percentage'
    (this is guaranteed by ColorAnalyzer._color_breakdown)."""
    n = len(breakdown)
    for c in breakdown:
        c["is_sub_color"] = False

    if n <= 1:
        return "single"

    if n > 3:
        return "multi"

    # n is 2 or 3 here.
    high = [c for c in breakdown if c["percentage"] >= sub_color_threshold]
    low = [c for c in breakdown if c["percentage"] < sub_color_threshold]

    if n == 3 and len(low) == 0:
        # Three real, sizeable colours -- doesn't reduce to single/dual.
        return "multi"

    for c in low:
        c["is_sub_color"] = True

    if len(high) >= 2:
        return "dual"
    if len(high) == 1:
        return "single"

    for c in breakdown:
        c["is_sub_color"] = False
    for c in breakdown[1:]:
        c["is_sub_color"] = True
    return "single"


# ============================================================
# Hard percentage floor -- final safety net.
# ============================================================

def apply_min_percent_floor(entries, floor):
    """entries: list of dicts each with 'percentage', '_count', '_lab'.
    Mutates/returns a NEW list where every entry's percentage is >=
    floor (unless only one entry remains, in which case it's whatever
    is left over, typically ~100%)."""
    if floor <= 0 or len(entries) <= 1:
        return list(entries)

    working = list(entries)
    while len(working) > 1:
        below = [e for e in working if e["percentage"] < floor]
        if not below:
            break
        # Fold the smallest offender first.
        smallest = min(below, key=lambda e: e["percentage"])
        candidates = [e for e in working if e is not smallest]
        nearest = min(
            candidates,
            key=lambda e: float(np.linalg.norm(smallest["_lab"] - e["_lab"])),
        )
        nearest["_count"] += smallest["_count"]
        nearest["percentage"] = round(nearest["percentage"] + smallest["percentage"], 2)
        working.remove(smallest)

    return working


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


def _erode_edge_halo(mask, erode_px=2):
    """Strips a couple of pixels off the mask boundary. Kills the
    anti-aliased garment/background halo that otherwise clusters as
    its own spurious near-background colour (e.g. a stray near-white
    reading on a dark shirt photographed against a light backdrop)."""
    if erode_px <= 0:
        return mask
    kernel = np.ones((3, 3), np.uint8)
    eroded = cv2.erode((mask > 0).astype(np.uint8), kernel, iterations=erode_px)
    # Never erode away the whole garment on a small/thin item.
    if eroded.sum() < 0.15 * mask.sum():
        return mask
    return eroded


def _denoise_for_clustering(image_rgb, mask):
    """Edge-preserving smoothing over the masked region only, to damp
    down fabric-fold micro-shadows / specular speckle / JPEG blocking
    before KMeans sees the pixels -- without blurring across a real
    colour boundary (bilateral filter is edge-aware)."""
    smoothed = cv2.bilateralFilter(image_rgb, d=7, sigmaColor=40, sigmaSpace=7)
    out = image_rgb.copy()
    m = mask.astype(bool)
    out[m] = smoothed[m]
    return out


def _largest_component_fraction(bool_mask_2d):
    """Fraction of a 2D boolean mask's True pixels that belong to its
    single largest connected blob. ~1.0 = one compact blob (a real
    printed logo / trim / contrast panel). Low (<0.4) = the pixels are
    scattered all over the garment (typical of a lighting/shadow
    artifact or JPEG noise, not a real design element)."""
    u8 = bool_mask_2d.astype(np.uint8)
    total = int(u8.sum())
    if total == 0:
        return 0.0
    num, _labels_im, stats, _ = cv2.connectedComponentsWithStats(u8, connectivity=8)
    if num <= 1:
        return 0.0
    largest = int(stats[1:, cv2.CC_STAT_AREA].max())
    return largest / total


# ============================================================
# Production inference class
# ============================================================

class ColorAnalyzer:
    

    def __init__(self, model_dir, colour_name_classes_path=None,
                 kmeans_k=8, min_percent=4.0, min_pixel_count=300,
                 compact_thresh=0.45,
                 merge_distance=16.0,
                 l_weight_chromatic=0.22, l_weight_neutral=0.55,
                 neutral_chroma_thresh=16.0,
                 erode_px=2, denoise=True,
                 final_dedup_distance=10.0,
                 final_min_percent=1.0,
                 sub_color_threshold=5.0):
        self.model_dir = model_dir

        # ---- post-processing / colour-grouping settings ----
        self.kmeans_k = kmeans_k
        self.min_percent = min_percent
        self.min_pixel_count = min_pixel_count
        self.compact_thresh = compact_thresh
        self.merge_distance = merge_distance
        self.l_weight_chromatic = l_weight_chromatic
        self.l_weight_neutral = l_weight_neutral
        self.neutral_chroma_thresh = neutral_chroma_thresh
        self.erode_px = erode_px
        self.denoise = denoise
        self.final_dedup_distance = final_dedup_distance
        # Hard floor: no reported colour below this % survives on its
        # own -- it gets folded into the nearest other colour. This is
        # what keeps shadow/lighting speckle (typically well under 1%)
        # from ever showing up as its own "minor colour" entry.
        self.final_min_percent = final_min_percent
        # Threshold used to decide single/dual/multi and which
        # colours get flagged as "sub colours" (see
        # classify_and_flag_colors() above).
        self.sub_color_threshold = sub_color_threshold

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

    def _color_breakdown(self, rgb_array, mask, k=None, min_percent=None,
                          min_pixel_count=None, merge_distance=None,
                          compact_thresh=None, erode_px=None, denoise=None,
                          final_dedup_distance=None, final_min_percent=None):
       
        k = self.kmeans_k if k is None else k
        min_percent = self.min_percent if min_percent is None else min_percent
        min_pixel_count = self.min_pixel_count if min_pixel_count is None else min_pixel_count
        merge_distance = self.merge_distance if merge_distance is None else merge_distance
        compact_thresh = self.compact_thresh if compact_thresh is None else compact_thresh
        erode_px = self.erode_px if erode_px is None else erode_px
        denoise = self.denoise if denoise is None else denoise
        final_dedup_distance = self.final_dedup_distance if final_dedup_distance is None else final_dedup_distance
        final_min_percent = self.final_min_percent if final_min_percent is None else final_min_percent

        clean_mask = _erode_edge_halo(mask, erode_px=erode_px)
        work_rgb = _denoise_for_clustering(rgb_array, clean_mask) if denoise else rgb_array

        ys, xs = np.where(clean_mask.astype(bool))
        pixels = work_rgb[ys, xs]
        if len(pixels) == 0:
            return []

        k_eff = min(k, len(pixels))
        kmeans = KMeans(n_clusters=k_eff, n_init=8, random_state=42).fit(pixels)
        labels_ = kmeans.labels_
        raw_centers = kmeans.cluster_centers_
        total = len(labels_)
        raw_counts = np.array([np.sum(labels_ == i) for i in range(k_eff)])

        # --- merge perceptually-identical (lighting-only) clusters ---
        group_ids = merge_similar_clusters(
            raw_centers, raw_counts,
            merge_distance=merge_distance,
            l_weight_chromatic=self.l_weight_chromatic,
            l_weight_neutral=self.l_weight_neutral,
            neutral_chroma_thresh=self.neutral_chroma_thresh,
        )

        groups = {}  # gid -> {center_sum, count, raw_label_ids}
        for i, gid in enumerate(group_ids):
            gid = int(gid)
            if gid not in groups:
                groups[gid] = {"center_sum": np.zeros(3), "count": 0, "raw_ids": []}
            groups[gid]["center_sum"] += raw_centers[i] * raw_counts[i]
            groups[gid]["count"] += raw_counts[i]
            groups[gid]["raw_ids"].append(i)

        h, w = clean_mask.shape[:2]

        def group_center(g):
            return g["center_sum"] / max(g["count"], 1)

        def group_spatial_mask(g):
            """2D boolean mask of pixels belonging to this merged group."""
            belongs = np.isin(labels_, g["raw_ids"])
            m2d = np.zeros((h, w), dtype=bool)
            m2d[ys[belongs], xs[belongs]] = True
            return m2d

        # --- split into keepers vs. candidates-for-absorption ---
        keepers = {}
        pending = []  # gid -> considered for absorption
        for gid, g in groups.items():
            pct = 100.0 * g["count"] / total
            if pct >= min_percent:
                keepers[gid] = g
                continue

            # Small cluster: is it a real compact design element, or
            # diffuse lighting/noise speckle?
            if g["count"] >= min_pixel_count:
                compactness = _largest_component_fraction(group_spatial_mask(g))
                if compactness >= compact_thresh:
                    keepers[gid] = g
                    continue
            pending.append((gid, g))

        # Guarantee at least one surviving colour (the largest group).
        if not keepers:
            biggest_gid = max(groups, key=lambda gid: groups[gid]["count"])
            keepers[biggest_gid] = groups[biggest_gid]
            pending = [(gid, g) for gid, g in groups.items() if gid != biggest_gid]

        # --- absorb every non-keeper into its nearest keeper (Lab space) ---
        keeper_labs = {gid: rgb_to_lab(group_center(g)) for gid, g in keepers.items()}
        for gid, g in pending:
            g_lab = rgb_to_lab(group_center(g))
            nearest_gid = min(
                keeper_labs,
                key=lambda kg: _lab_merge_distance(
                    g_lab, keeper_labs[kg],
                    l_weight_chromatic=self.l_weight_chromatic,
                    l_weight_neutral=self.l_weight_neutral,
                    neutral_chroma_thresh=self.neutral_chroma_thresh,
                ),
            )
            keepers[nearest_gid]["center_sum"] += g["center_sum"]
            keepers[nearest_gid]["count"] += g["count"]
            keeper_labs[nearest_gid] = rgb_to_lab(group_center(keepers[nearest_gid]))

        # --- name the surviving (now absorbed/updated) colours ---
        breakdown = []
        for gid, g in keepers.items():
            center = group_center(g)
            pct = 100.0 * g["count"] / total
            name, _ref_rgb, conf = self._closest_color_name(center)
            breakdown.append({
                "color_name": name,
                "rgb": tuple(int(v) for v in center),
                "percentage": round(float(pct), 2),
                "name_confidence": conf,
                "_lab": rgb_to_lab(center),
                "_count": int(g["count"]),
            })

        # --- de-dup pass: merge any two survivors that are still
        # essentially the same colour (full-weight Lab distance, no
        # neutral/chromatic split) -- catches cases like KMeans
        # splitting one real "orange-yellow" into two close shades that
        # the earlier adaptive-weight merge didn't quite catch. ---
        breakdown.sort(key=lambda d: d["_count"], reverse=True)
        deduped = []
        for entry in breakdown:
            merged_into = None
            for kept in deduped:
                d = float(np.linalg.norm(entry["_lab"] - kept["_lab"]))
                if d < final_dedup_distance:
                    merged_into = kept
                    break
            if merged_into is None:
                deduped.append(entry)
            else:
                merged_into["_count"] += entry["_count"]
                merged_into["percentage"] = round(merged_into["percentage"] + entry["percentage"], 2)

        # --- FINAL HARD FLOOR: fold any remaining sub-threshold colour
   
        deduped = apply_min_percent_floor(deduped, final_min_percent)

        for d in deduped:
            d.pop("_lab", None)
            d.pop("_count", None)

        # Renormalise (should already sum ~100 since we absorb rather
        # than drop, but rounding can drift slightly).
        total_pct = sum(d["percentage"] for d in deduped)
        if total_pct > 0:
            for d in deduped:
                d["percentage"] = round(d["percentage"] / total_pct * 100.0, 2)

        deduped.sort(key=lambda d: d["percentage"], reverse=True)
        return deduped

    # ---- public API (matches app.py's usage exactly) ----

    def analyze_image(self, image_rgb, has_person=False, sub_color_threshold=None,
                       **breakdown_overrides):
        """image_rgb: HxWx3 RGB uint8 numpy array.

        breakdown_overrides: optional per-call overrides for k /
        min_percent / merge_distance / final_min_percent / etc, e.g.
            analyzer.analyze_image(img, merge_distance=20.0, final_min_percent=1.5)
        without changing the analyzer's stored defaults.

        sub_color_threshold: optional per-call override (percent) for
        the single/dual/multi + "sub colour" cutoff. Defaults to
        self.sub_color_threshold (5.0%) when not given.
        """
        pil_img = Image.fromarray(image_rgb)

        mask = remove_background(image_rgb)
        if has_person:
            mask = exclude_skin(image_rgb, mask)
        mask = cleanup_mask(mask)

        base_color, base_conf = self._predict_base_color(pil_img)
        breakdown = self._color_breakdown(image_rgb, mask, **breakdown_overrides)

        threshold = self.sub_color_threshold if sub_color_threshold is None else sub_color_threshold
        color_type = classify_and_flag_colors(breakdown, sub_color_threshold=threshold)

        return {
            "base_color": base_color,
            "base_color_confidence": base_conf,
            "colors": breakdown,
            "num_colors": len(breakdown),
            "color_type": color_type,
        }

    def predict(self, image_path, has_person=False, sub_color_threshold=None,
                **breakdown_overrides):
        """image_path: path to an image file on disk. Returns (result, img_rgb)."""
        pil_img = Image.open(image_path)
        pil_img = ImageOps.exif_transpose(pil_img)
        pil_img = pil_img.convert("RGB")
        img_rgb = np.array(pil_img)

        result = self.analyze_image(
            img_rgb, has_person=has_person,
            sub_color_threshold=sub_color_threshold,
            **breakdown_overrides,
        )
        return result, img_rgb