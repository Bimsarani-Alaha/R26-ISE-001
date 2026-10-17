import pandas as pd
import json
import re
import logging
from typing import Optional
from ..core.config import REQUIRED_COLUMNS, load_settings
from ..core.paths import image_path

logger = logging.getLogger(__name__)


class CatalogRepository:
    def __init__(self, settings=None):
        self.settings = settings or load_settings()
        self.df: Optional[pd.DataFrame] = None
        self.occasion_mapping: dict = {}

    def _load_occasion_mapping(self):
        if self.settings.occasion_mapping_path.exists():
            with open(self.settings.occasion_mapping_path, "r", encoding="utf-8") as f:
                self.occasion_mapping = json.load(f)

    def load_dataset(self) -> pd.DataFrame:
        if self.df is not None:
            return self.df

        self._load_occasion_mapping()
        df = pd.read_csv(self.settings.dataset_path)
        self._validate_columns(df)
        self._normalize_article_types(df)
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
            logger.warning("Extra catalog columns found: %s", sorted(extra))

    def _normalize_article_types(self, df: pd.DataFrame):
        def normalize(row):
            article = str(row["article_type"]).strip()
            description = str(row.get("description", "")).casefold()
            # Some catalog shirts have only the broad "Top" label. Refine it
            # from explicit garment metadata without treating every top as a shirt.
            if article.casefold() != "top":
                return article
            if re.search(r"\b(?:t[ -]?shirt|sweatshirt|polo shirt|shirt jacket|shirt dress)\b", description):
                return article
            if re.search(r"\bshirt\b", description) and re.search(
                r"\b(?:button[ -](?:front|down)|dress shirt)\b", description
            ):
                return "Shirt"
            return article

        df["article_type"] = df.apply(normalize, axis=1)

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
            full_path = image_path(self.settings.images_dir, path)
            return full_path is not None and full_path.is_file()

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
        from ..core.paths import image_path as resolve
        full_path = resolve(self.settings.images_dir, image_path)
        return str(full_path) if full_path is not None and full_path.is_file() else None
