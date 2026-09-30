import pandas as pd
from typing import Optional
from ..schemas.models import RequirementResponse

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
        return candidates

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
