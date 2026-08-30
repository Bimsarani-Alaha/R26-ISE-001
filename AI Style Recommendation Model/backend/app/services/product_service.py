import pandas as pd
import json
from pathlib import Path
from typing import Optional
from ..config import (
    DATASET_PATH,
    OCCASION_MAPPING_PATH,
    REQUIRED_COLUMNS,
    VALID_SIZES,
    IMAGES_DIR,
)


class ProductService:
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.occasion_mapping: dict = {}
        self._load_occasion_mapping()

    def _load_occasion_mapping(self):
        if OCCASION_MAPPING_PATH.exists():
            with open(OCCASION_MAPPING_PATH, "r") as f:
                self.occasion_mapping = json.load(f)

    def load_dataset(self) -> pd.DataFrame:
        if self.df is not None:
            return self.df

        df = pd.read_csv(DATASET_PATH)
        self._validate_columns(df)
        self._normalize_sizes(df)
        self._validate_prices(df)
        self._validate_image_paths(df)
        self.df = df
        return df

    def _validate_columns(self, df: pd.DataFrame):
        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        extra = set(df.columns) - set(REQUIRED_COLUMNS)
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        if extra:
            print(f"Warning: extra columns found: {extra}")

    def _normalize_sizes(self, df: pd.DataFrame):
        def parse_sizes(val):
            if pd.isna(val):
                return []
            s = str(val).strip()
            if s.startswith("["):
                try:
                    sizes = json.loads(s.replace("'", '"'))
                    return [sz.strip().upper() for sz in sizes]
                except json.JSONDecodeError:
                    pass
            sizes = [sz.strip().upper() for sz in s.replace("/", ",").split(",") if sz.strip()]
            return sizes

        df["available_sizes"] = df["available_sizes"].apply(parse_sizes)

    def _validate_prices(self, df: pd.DataFrame):
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

    def _validate_image_paths(self, df: pd.DataFrame):
        def check_image(path):
            if pd.isna(path) or not path:
                return False
            full_path = IMAGES_DIR / str(path).replace("Images/", "").replace("images/", "")
            return full_path.exists()

        df["image_exists"] = df["image_path"].apply(check_image)

    def _ensure_loaded(self):
        if self.df is None:
            self.load_dataset()

    def get_all_products(self) -> pd.DataFrame:
        self._ensure_loaded()
        return self.df

    def get_product_by_id(self, product_id: str) -> Optional[dict]:
        self._ensure_loaded()
        row = self.df[self.df["product_id"] == product_id]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def get_unique_genders(self) -> list[str]:
        self._ensure_loaded()
        return sorted(self.df["gender"].dropna().unique().tolist())

    def get_unique_occasions(self) -> list[str]:
        self._ensure_loaded()
        occasions = set()
        for val in self.df["occasion"].dropna().unique():
            for part in str(val).replace("/", ",").split(","):
                occasions.add(part.strip())
        return sorted(occasions)

    def normalize_occasion(self, occasion: str) -> str:
        lower = occasion.lower().strip()
        if lower in self.occasion_mapping:
            return self.occasion_mapping[lower]
        return occasion.strip()

    def resolve_image_path(self, image_path: str) -> Optional[str]:
        if not image_path:
            return None
        cleaned = str(image_path).replace("Images/", "").replace("images/", "")
        full_path = IMAGES_DIR / cleaned
        if full_path.exists():
            return str(full_path)
        return None


product_service = ProductService()
