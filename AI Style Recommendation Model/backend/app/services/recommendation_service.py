import pandas as pd
import re
from typing import Optional
from ..schemas.models import RequirementResponse
from .product_service import product_service

UNKNOWN_VALUES = {"", "unknown", "n/a", "na", "none", "null", "nan"}
ARTICLE_FAMILIES = {
    "lehenga": {"lehenga", "lehenga choli", "lehenga choli set", "lehenga set",
                "lehenga skirt", "lehenga skirt set"},
}
COLOUR_SHADES = {
    "blue": {"light blue", "dark blue", "navy blue", "sky blue", "royal blue",
             "powder blue", "dusty blue", "ice blue", "steel blue", "teal blue", "turquoise blue"},
    "red": {"dark red", "light red", "maroon", "burgundy", "burgundy maroon", "dark red maroon", "coral red"},
    "green": {"light green", "dark green", "olive green", "sage green", "mint green",
              "bottle green", "pista green", "sea green", "lime green", "teal green"},
    "pink": {"light pink", "dark pink", "hot pink", "blush pink", "dusty pink", "rose pink", "dusty rose pink"},
    "yellow": {"light yellow", "pale yellow", "mustard yellow", "bright yellow"},
    "purple": {"light purple", "dark purple", "lavender", "purple plum"},
    "grey": {"light grey", "dark grey", "charcoal grey", "dark charcoal", "silver grey"},
    "brown": {"light brown", "dark brown", "rust brown"},
    "white": {"off white", "ivory"},
    "orange": {"light orange", "dark orange", "rust orange"},
}

ARTICLE_SYNONYMS = {
    "pants": ["trousers", "trouser"],
    "trousers": ["pants", "trouser"],
    "trouser": ["pants", "trousers"],
    "t-shirt": ["tee", "teeshirt"],
    "shirt": ["top", "blouse"],
    "top": ["shirt", "blouse"],
    "blouse": ["shirt", "top"],
    "shorts": ["short"],
    "jeans": ["denim"],
    "skirt": ["mini skirt", "midi skirt", "maxi skirt"],
    "frock": ["dress", "gown", "frock dress"],
    "frock dress": ["dress", "gown", "frock"],
    "dress": ["frock", "gown", "frock dress"],
    "gown": ["dress", "frock", "frock dress"],
    "saree": ["sari"],
    "sari": ["saree"],
    "kurta": ["kurti", "kurta set"],
    "kurti": ["kurta", "kurta set"],
}

SIZE_ALIASES = {
    "2XL": ["XXL"],
    "3XL": ["XXXL"],
    "4XL": ["XXXXL"],
    "XXL": ["2XL"],
    "XXXL": ["3XL"],
    "XXXXL": ["4XL"],
}


class RecommendationService:
    def __init__(self):
        pass

    @staticmethod
    def normalize_article_type(value) -> str:
        value = str(value).strip().casefold()
        return {
            "pants": "trousers", "trouser": "trousers",
            "tee": "t-shirt", "teeshirt": "t-shirt", "tshirt": "t-shirt",
            "sari": "saree", "frock": "dress", "frock dress": "dress",
        }.get(value, value)

    def matches_article_type(self, value, requested: list[str]) -> bool:
        actual = self.normalize_article_type(value)
        if actual in UNKNOWN_VALUES:
            return False
        # General requests include known catalogue variants. Specific requests
        # remain specific; do not use substring matching across garment types.
        return any(
            actual in ARTICLE_FAMILIES.get(wanted, {wanted})
            for wanted in (self.normalize_article_type(v) for v in requested)
            if wanted not in UNKNOWN_VALUES
        )

    @staticmethod
    def normalize_colour(value) -> str:
        value = re.sub(r"\s+", " ", str(value).strip().casefold().replace("-", " "))
        value = re.sub(r"\bgray\b", "grey", value)
        return {"navy": "navy blue", "charcoal": "charcoal grey",
                "mustard": "mustard yellow", "olive": "olive green"}.get(value, value)

    def colour_match(self, value, requested: list[str]) -> str:
        if not requested:
            return "unspecified"
        actual = self.normalize_colour(value)
        if actual in UNKNOWN_VALUES:
            return "unknown"
        wanted = {self.normalize_colour(v) for v in requested} - UNKNOWN_VALUES
        if actual in wanted:
            return "exact"
        # Only broaden a base colour to its known shades. Compound/multicolour
        # labels are not accepted just because they contain the requested word.
        if any(actual in COLOUR_SHADES.get(v, set()) for v in wanted):
            return "shade"
        return "different"

    @staticmethod
    def occasion_values(value) -> set[str]:
        if str(value).strip().casefold() in UNKNOWN_VALUES:
            return set()
        return {
            product_service.normalize_occasion(part).casefold()
            for part in re.split(r"[,/;]|\band\b|&", str(value), flags=re.IGNORECASE)
            if part.strip().casefold() not in UNKNOWN_VALUES
        }

    def filter_required_attributes(self, df: pd.DataFrame, requirements: RequirementResponse) -> pd.DataFrame:
        if df.empty:
            return df
        if requirements.article_types:
            mask = df["article_type"].map(
                lambda v: self.matches_article_type(v, requirements.article_types)
            ).astype(bool)
            df = df.loc[mask]
        if requirements.occasion:
            wanted = set().union(*(self.occasion_values(v) for v in requirements.occasion))
            mask = df["occasion"].map(lambda v: bool(self.occasion_values(v) & wanted)).astype(bool)
            df = df.loc[mask]
        return df.copy()

    def filter_by_gender(self, df: pd.DataFrame, gender: str) -> pd.DataFrame:
        # Normalize client values (Male/Female from frontend GENDERS) to dataset values (Men/Women)
        g = gender.strip().lower()
        if g in ("female", "women", "woman"):
            target = "women"
        elif g in ("male", "men", "man"):
            target = "men"
        elif g in ("unisex",):
            target = "unisex"
        else:
            target = g
        return df[
            (df["gender"].str.lower() == target)
            | (df["gender"].str.lower() == "unisex")
        ].copy()

    def filter_by_size(self, df: pd.DataFrame, size: str) -> pd.DataFrame:
        size_upper = size.upper()
        aliases = [size_upper] + SIZE_ALIASES.get(size_upper, [])

        # Sarees etc use "FREE SIZE" / "ONE SIZE" which should match any requested size
        UNIVERSAL_TOKENS = ("FREE SIZE", "ONE SIZE")

        def _matches(sizes: list[str]) -> bool:
            if not sizes:
                return False
            # Universal / one-size products match any size
            if any(any(tok in s for tok in UNIVERSAL_TOKENS) for s in sizes):
                return True
            return any(a in sizes for a in aliases)

        return df[df["available_sizes"].apply(_matches)].copy()

    def filter_by_price(
        self, df: pd.DataFrame, price_preference: Optional[dict]
    ) -> pd.DataFrame:
        if not price_preference:
            return df
        if "max" in price_preference:
            df = df[df["price"] <= price_preference["max"]]
        if "min" in price_preference:
            df = df[df["price"] >= price_preference["min"]]
        return df

    def generate_candidates(
        self,
        df: pd.DataFrame,
        gender: str,
        size: str,
        requirements: RequirementResponse,
    ) -> pd.DataFrame:
        candidates = self.filter_by_gender(df, gender)
        candidates = self.filter_by_size(candidates, size)
        candidates = self.filter_by_price(candidates, requirements.price_preference)
        return self.filter_required_attributes(candidates, requirements)

    def match_field(
        self, product_val: str, requested_vals: list[str], field_name: str
    ) -> float:
        if not requested_vals or not product_val:
            return 0.0
        product_lower = str(product_val).lower()
        max_score = 0.0
        for req in requested_vals:
            req_lower = req.lower()
            if req_lower == product_lower:
                max_score = max(max_score, 1.0)
            elif req_lower in product_lower or product_lower in req_lower:
                max_score = max(max_score, 0.7)
            elif any(word in product_lower for word in req_lower.split()):
                max_score = max(max_score, 0.4)
            elif field_name == "article_type":
                synonyms = ARTICLE_SYNONYMS.get(req_lower, [])
                for syn in synonyms:
                    if syn == product_lower:
                        max_score = max(max_score, 0.9)
                        break
                    elif syn in product_lower or product_lower in syn:
                        max_score = max(max_score, 0.6)
                        break
        return max_score

    def match_description(self, description: str, requirements: RequirementResponse) -> float:
        if not description:
            return 0.0
        desc_lower = description.lower()
        score = 0.0
        all_terms = (
            requirements.preferred_colors
            + requirements.article_types
            + requirements.style_preferences
            + requirements.materials
            + requirements.patterns
        )
        if not all_terms:
            return 0.0
        matches = sum(1 for term in all_terms if term.lower() in desc_lower)
        score = matches / len(all_terms) if all_terms else 0.0
        return min(score, 1.0)


recommendation_service = RecommendationService()
