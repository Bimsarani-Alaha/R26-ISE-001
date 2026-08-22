import numpy as np
import pandas as pd
from skimage import color
from skimage.color import deltaE_ciede2000

def rgb_to_lab(rgb):
    arr = np.array(rgb, dtype=float) / 255.0
    return color.rgb2lab(arr.reshape(1, 1, 3))[0][0]

def calculate_delta_e(rgb1, rgb2):
    return round(float(deltaE_ciede2000(rgb_to_lab(rgb1), rgb_to_lab(rgb2))), 2)

def match_label(delta_e):
    if delta_e >= 50:
        return "Good"
    elif delta_e >= 25:
        return "Moderate"
    else:
        return "Poor"

np.random.seed(42)
rows = []

for _ in range(1000):
    top_rgb    = np.random.randint(0, 256, 3).tolist()
    bottom_rgb = np.random.randint(0, 256, 3).tolist()
    de         = calculate_delta_e(top_rgb, bottom_rgb)
    label      = match_label(de)

    rows.append({
        "top_R":    top_rgb[0],    "top_G":    top_rgb[1],    "top_B":    top_rgb[2],
        "bot_R":    bottom_rgb[0], "bot_G":    bottom_rgb[1], "bot_B":    bottom_rgb[2],
        "delta_e":  de,
        "match":    label
    })

df = pd.DataFrame(rows)
df.to_csv("dataset.csv", index=False)
print(f"Dataset saved: {len(df)} rows")
print(df["match"].value_counts())