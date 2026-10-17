import pandas as pd
from ..schemas.models import RequirementResponse, ProductResult
from ..config import WEIGHTS_WITH_OCCASION, WEIGHTS_WITHOUT_OCCASION
from ..services.recommendation_service import recommendation_service
from ..services.product_service import product_service
from ..services.cartographer_service import cartographer_service
from ..services.fashionclip_service import fashionclip_service
from ..config import RANKER_CANDIDATES_PER_GROUP


class RankingService:
    def __init__(self):
        pass

    def calculate_scores(
        self,
        candidates: pd.DataFrame,
        requirements: RequirementResponse,
        selected_size: str,
        query: str = "",
    ) -> list[ProductResult]:
        return self.calculate_groups(candidates, requirements, selected_size, query)[0]

    def calculate_groups(
        self,
        candidates: pd.DataFrame,
        requirements: RequirementResponse,
        selected_size: str,
        query: str = "",
    ) -> tuple[list[ProductResult], list[ProductResult]]:
        candidates = recommendation_service.filter_required_attributes(candidates, requirements)
        has_occasion = bool(requirements.occasion)
        weights = WEIGHTS_WITH_OCCASION if has_occasion else WEIGHTS_WITHOUT_OCCASION

        scored = []
        for _, row in candidates.iterrows():
            score_breakdown = {}
            total_score = 0.0

            at_score = float(recommendation_service.matches_article_type(
                row.get("article_type"), requirements.article_types,
            ))

            score_breakdown["article_type"] = at_score
            total_score += at_score * weights.get("article_type", 0)

            colour_match = recommendation_service.colour_match(row.get("base_colour"), requirements.preferred_colors)
            colour_score = {"exact": 1.0, "shade": 0.8}.get(colour_match, 0.0)
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

            mismatches, unverified = self._requirement_evidence(row, requirements)
            product_result = ProductResult(
                colour_match=colour_match,
                unmatched_requirements=mismatches,
                unverified_requirements=unverified,
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
            if mismatches or unverified:
                product_result.match_category = "alternative"
                parts = ["Similar alternative in your selected size."]
                if mismatches:
                    parts.append(f"Differs in: {', '.join(mismatches)}.")
                if unverified:
                    parts.append(f"Not verified: {', '.join(unverified)}.")
                product_result.explanation = " ".join(parts)
            scored.append(product_result)

        def colour_priority(product):
            return {"exact": 2, "shade": 1}.get(product.colour_match, 0)

        scored.sort(key=lambda p: (colour_priority(p), p.match_score), reverse=True)
        exact = [p for p in scored if p.match_category == "exact"]
        alternatives = [p for p in scored if p.match_category == "alternative" and p.match_score > 0]
        if query.strip():
            shortlist = exact[:RANKER_CANDIDATES_PER_GROUP] + alternatives[:RANKER_CANDIDATES_PER_GROUP]
            visual = fashionclip_service.score(query, shortlist)
            if visual is not None:
                for product, score in zip(shortlist, visual):
                    product.visual_score = score
                # Keep catalogue evidence authoritative. Missing images sort after
                # scored images within their group, retaining metadata order.
                def visual_key(product):
                    return (product.visual_score is not None,
                            product.visual_score if product.visual_score is not None else 0.0)
                exact.sort(key=lambda p: (colour_priority(p), *visual_key(p)), reverse=True)
                alternatives.sort(key=visual_key, reverse=True)
                return exact, alternatives
            relevance = cartographer_service.score(query, shortlist)
            if relevance is not None:
                for product, score in zip(shortlist, relevance):
                    product.reranker_score = score
                def relevance_key(product):
                    return (product.reranker_score is not None,
                            product.reranker_score if product.reranker_score is not None else 0.0)
                exact.sort(key=lambda p: (colour_priority(p), *relevance_key(p)), reverse=True)
                alternatives.sort(key=relevance_key, reverse=True)
        # Keep every eligible result so colours and occasion groups are not lost
        # behind a global top-five limit. AI inference remains bounded above.
        return exact, alternatives

    @staticmethod
    def _normalize(value: str, field: str) -> str:
        value = str(value).strip().casefold()
        if field == "clothing type":
            return recommendation_service.normalize_article_type(value)
        if field == "occasion":
            value = product_service.normalize_occasion(value).casefold()
        aliases = {
            "colour": {"gray": "grey"},
        }
        return aliases.get(field, {}).get(value, value)

    def _unmatched_requirements(self, row: pd.Series, requirements: RequirementResponse) -> list[str]:
        return self._requirement_evidence(row, requirements)[0]

    def _requirement_evidence(
        self, row: pd.Series, requirements: RequirementResponse
    ) -> tuple[list[str], list[str]]:
        """Separate known differences from requirements lacking catalogue evidence."""
        unmatched = []
        unverified = []
        for field, column, requested in (
            ("colour", "base_colour", requirements.preferred_colors),
            ("clothing type", "article_type", requirements.article_types),
            ("occasion", "occasion", requirements.occasion),
            ("style", "style", requirements.style_preferences),
            ("material", "material", requirements.materials),
            ("pattern", "pattern", requirements.patterns),
            ("sleeve type", "sleeve_type", requirements.sleeve_types),
            ("neckline", "neck_type", requirements.neck_types),
        ):
            if not requested:
                continue
            value = row.get(column)
            if field == "clothing type" and recommendation_service.matches_article_type(value, requested):
                continue
            if field == "colour" and recommendation_service.colour_match(value, requested) in {"exact", "shade"}:
                continue
            # Only occasion is a multi-value source field. Keep compound
            # material/garment labels intact rather than treating them as options.
            actual = [] if pd.isna(value) else (
                list(recommendation_service.occasion_values(value)) if field == "occasion" else [str(value)]
            )
            normalized = {self._normalize(v, field) for v in actual}
            normalized -= {"", "unknown", "n/a", "na", "none", "null", "nan"}
            if not normalized:
                unverified.append(field)
                continue
            if not any(self._normalize(v, field) in normalized for v in requested):
                unmatched.append(field)
        # Free-text needs have no dedicated supporting attributes in this schema.
        # A generated description or a material guess cannot verify them.
        for requirement in requirements.other_requirements:
            requirement = requirement.strip()
            if requirement and requirement not in unverified:
                unverified.append(requirement)
        return unmatched, unverified

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
