import pandas as pd
from typing import Optional
from ..schemas.models import RequirementResponse

ARTICLE_SYNONYMS = {
    "pants": ["trousers", "trouser"],
    "trousers": ["pants", "trouser"],
    "trouser": ["pants", "trousers"],
    "t-shirt": ["tee", "teeshirt"],
    "shirt": ["top"],
    "top": ["shirt"],
    "shorts": ["short"],
    "jeans": ["denim"],
    "skirt": ["mini skirt", "midi skirt", "maxi skirt"],
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
        return df[
            (df["gender"].str.lower() == gender.lower())
            | (df["gender"].str.lower() == "unisex")
        ].copy()

    def filter_by_size(self, df: pd.DataFrame, size: str) -> pd.DataFrame:
        size_upper = size.upper()
        aliases = [size_upper] + SIZE_ALIASES.get(size_upper, [])
        return df[df["available_sizes"].apply(
            lambda sizes: any(a in sizes for a in aliases)
        )].copy()

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
