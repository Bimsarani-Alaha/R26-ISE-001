import pandas as pd
from typing import Optional
from ..schemas.models import RequirementResponse, ProductResult
from ..config import WEIGHTS_WITH_OCCASION, WEIGHTS_WITHOUT_OCCASION, TOP_K, MIN_SCORE_THRESHOLD
from ..services.recommendation_service import recommendation_service
from ..services.product_service import product_service


class RankingService:
    def __init__(self):
        pass

    def calculate_scores(
        self,
        candidates: pd.DataFrame,
        requirements: RequirementResponse,
        selected_size: str,
    ) -> list[ProductResult]:
        has_occasion = bool(requirements.occasion)
        weights = WEIGHTS_WITH_OCCASION if has_occasion else WEIGHTS_WITHOUT_OCCASION
        has_article_filter = bool(requirements.article_types)

        scored = []
        for _, row in candidates.iterrows():
            score_breakdown = {}
            total_score = 0.0

            at_score = recommendation_service.match_field(
                str(row.get("article_type", "")),
                requirements.article_types,
                "article_type",
            )

            if has_article_filter and at_score == 0.0:
                continue

            score_breakdown["article_type"] = at_score
            total_score += at_score * weights.get("article_type", 0)

            colour_score = recommendation_service.match_field(
                str(row.get("base_colour", "")),
                requirements.preferred_colors,
                "base_colour",
            )
            score_breakdown["base_colour"] = colour_score
            total_score += colour_score * weights.get("base_colour", 0)

            style_score = recommendation_service.match_field(
                str(row.get("style", "")),
                requirements.style_preferences,
                "style",
            )
            score_breakdown["style"] = style_score
            total_score += style_score * weights.get("style", 0)

            pattern_score = recommendation_service.match_field(
                str(row.get("pattern", "")),
                requirements.patterns,
                "pattern",
            )
            score_breakdown["pattern"] = pattern_score
            total_score += pattern_score * weights.get("pattern", 0)

            material_score = recommendation_service.match_field(
                str(row.get("material", "")),
                requirements.materials,
                "material",
            )
            score_breakdown["material"] = material_score
            total_score += material_score * weights.get("material", 0)

            sleeve_score = recommendation_service.match_field(
                str(row.get("sleeve_type", "")),
                requirements.sleeve_types,
                "sleeve_type",
            )
            score_breakdown["sleeve_type"] = sleeve_score
            total_score += sleeve_score * weights.get("sleeve_type", 0)

            neck_score = recommendation_service.match_field(
                str(row.get("neck_type", "")),
                requirements.neck_types,
                "neck_type",
            )
            score_breakdown["neck_type"] = neck_score
            total_score += neck_score * weights.get("neck_type", 0)

            if has_occasion:
                occasion_score = self._score_occasion(
                    str(row.get("occasion", "")), requirements.occasion
                )
                score_breakdown["occasion"] = occasion_score
                total_score += occasion_score * weights.get("occasion", 0)

            desc_score = recommendation_service.match_description(
                str(row.get("description", "")), requirements
            )
            total_score += desc_score * 0.05

            explanation = self._build_explanation(
                row, requirements, score_breakdown, has_occasion
            )

            product_result = ProductResult(
                product_id=str(row["product_id"]),
                image_path=str(row.get("image_path", "")),
                article_type=str(row.get("article_type", "")),
                base_colour=str(row.get("base_colour", "")),
                occasion=str(row.get("occasion", "")) if pd.notna(row.get("occasion")) else None,
                style=str(row.get("style", "")),
                price=float(row["price"]) if pd.notna(row.get("price")) else None,
                selected_size=selected_size,
                match_score=round(total_score, 4),
                explanation=explanation,
                category=str(row.get("category", "")),
                pattern=str(row.get("pattern", "")),
                material=str(row.get("material", "")),
                sleeve_type=str(row.get("sleeve_type", "")),
                neck_type=str(row.get("neck_type", "")),
                description=str(row.get("description", "")),
            )
            scored.append(product_result)

        scored.sort(key=lambda x: x.match_score, reverse=True)
        filtered = [p for p in scored if p.match_score >= MIN_SCORE_THRESHOLD]
        return filtered[:TOP_K]

    def _score_occasion(
        self, product_occasion: str, requested_occasions: list[str]
    ) -> float:
        if not product_occasion or not requested_occasions:
            return 0.0

        product_occasions = [
            product_service.normalize_occasion(o.strip())
            for o in str(product_occasion).replace("/", ",").split(",")
            if o.strip()
        ]
        requested_normalized = [
            product_service.normalize_occasion(o) for o in requested_occasions
        ]

        max_score = 0.0
        for req in requested_normalized:
            req_lower = req.lower()
            for prod_occ in product_occasions:
                prod_lower = prod_occ.lower()
                if req_lower == prod_lower:
                    max_score = max(max_score, 1.0)
                elif req_lower in prod_lower or prod_lower in req_lower:
                    max_score = max(max_score, 0.8)
                elif any(word in prod_lower for word in req_lower.split()):
                    max_score = max(max_score, 0.5)

        if len(requested_occasions) > 1:
            matched_count = sum(
                1
                for req in requested_normalized
                if any(req.lower() in po.lower() for po in product_occasions)
            )
            if matched_count > 1:
                max_score = min(max_score + 0.1, 1.0)

        return max_score

    def _build_explanation(
        self,
        row: pd.Series,
        requirements: RequirementResponse,
        scores: dict,
        has_occasion: bool,
    ) -> str:
        parts = []
        parts.append(f"This {row.get('article_type', 'item')} matches your selected size")

        if requirements.preferred_colors:
            parts.append(f"{row.get('base_colour', '')} color")
        if requirements.article_types:
            parts.append(f"{row.get('article_type', '')} type")
        if requirements.style_preferences:
            parts.append(f"{row.get('style', '')} style")
        if has_occasion and requirements.occasion:
            occasion_str = " and ".join(requirements.occasion)
            parts.append(f"{occasion_str} occasion")

        return ", ".join(parts) + "."


ranking_service = RankingService()
