import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pandas as pd
from app.config import DATASET_PATH, REQUIRED_COLUMNS, IMAGES_DIR


def validate_dataset():
    print("=" * 60)
    print("DATASET VALIDATION")
    print("=" * 60)

    if not DATASET_PATH.exists():
        print(f"FAIL: Dataset not found at {DATASET_PATH}")
        return False

    df = pd.read_csv(DATASET_PATH)
    print(f"\nDataset loaded: {len(df)} rows, {len(df.columns)} columns")

    print("\n--- Column Validation ---")
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    extra = set(df.columns) - set(REQUIRED_COLUMNS)
    if missing:
        print(f"FAIL: Missing columns: {missing}")
        return False
    if extra:
        print(f"WARN: Extra columns: {extra}")
    print("PASS: All 15 required columns present")

    print("\n--- Product ID Validation ---")
    null_ids = df["product_id"].isna().sum()
    dup_ids = df["product_id"].duplicated().sum()
    if null_ids > 0:
        print(f"FAIL: {null_ids} null product IDs")
        return False
    if dup_ids > 0:
        print(f"FAIL: {dup_ids} duplicate product IDs")
        return False
    print(f"PASS: All {len(df)} product IDs are unique and valid")

    print("\n--- Size Normalization ---")
    sample_sizes = df["available_sizes"].head(5).tolist()
    print(f"Sample raw sizes: {sample_sizes}")

    def parse_sizes(val):
        if pd.isna(val):
            return []
        import json
        s = str(val).strip()
        if s.startswith("["):
            try:
                sizes = json.loads(s.replace("'", '"'))
                return [sz.strip().upper() for sz in sizes]
            except json.JSONDecodeError:
                pass
        return [sz.strip().upper() for sz in s.replace("/", ",").split(",") if sz.strip()]

    df["available_sizes"] = df["available_sizes"].apply(parse_sizes)
    normalized = df["available_sizes"].head(5).tolist()
    print(f"Normalized: {normalized}")
    print("PASS: Sizes normalized")

    print("\n--- Price Validation ---")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    null_prices = df["price"].isna().sum()
    print(f"Prices range: {df['price'].min()} - {df['price'].max()}")
    if null_prices > 0:
        print(f"WARN: {null_prices} null/invalid prices")
    else:
        print("PASS: All prices valid")

    print("\n--- Image Path Validation ---")
    existing = 0
    missing_images = 0
    for _, row in df.iterrows():
        path = str(row.get("image_path", ""))
        if path and path != "nan":
            cleaned = path.replace("Images/", "").replace("images/", "")
            full = IMAGES_DIR / cleaned
            if full.exists():
                existing += 1
            else:
                missing_images += 1
        else:
            missing_images += 1

    print(f"Images found: {existing}/{existing + missing_images}")
    if missing_images > 0:
        print(f"WARN: {missing_images} images not found (expected with mismatched names)")
    print("PASS: Image path validation complete")

    print("\n--- Occasion Values ---")
    occasions = set()
    for val in df["occasion"].dropna().unique():
        for part in str(val).replace("/", ",").split(","):
            occasions.add(part.strip())
    print(f"Unique occasions: {sorted(occasions)}")

    print("\n--- Gender Values ---")
    genders = df["gender"].dropna().unique().tolist()
    print(f"Unique genders: {sorted(genders)}")

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = validate_dataset()
    sys.exit(0 if success else 1)
