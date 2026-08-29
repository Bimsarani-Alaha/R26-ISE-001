import json
import logging
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..schemas.models import (
    RecommendationRequest,
    RecommendationResponse,
    RequirementResponse,
    ProductResult,
)
from ..services.qwen_service import qwen_service
from ..services.product_service import product_service
from ..services.recommendation_service import recommendation_service
from ..services.ranking_service import ranking_service
from ..services.terminal_progress import PipelineProgress, new_request_id

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _export_results_to_json(
    response: RecommendationResponse,
    gender: str,
    size: str,
    requirements: str,
) -> None:
    results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "results")
    os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recommendation_{timestamp}_{gender}_{size}.json"
    filepath = os.path.join(results_dir, filename)

    data = {
        "timestamp": datetime.now().isoformat(),
        "request": {
            "gender": gender,
            "size": size,
            "requirements": requirements,
        },
        "response": {
            "recommendations": [
                {
                    "product_id": r.product_id,
                    "article_type": r.article_type,
                    "base_colour": r.base_colour,
                    "occasion": r.occasion,
                    "style": r.style,
                    "price": r.price,
                    "selected_size": r.selected_size,
                    "match_score": r.match_score,
                    "explanation": r.explanation,
                    "category": r.category,
                    "pattern": r.pattern,
                    "material": r.material,
                    "sleeve_type": r.sleeve_type,
                    "neck_type": r.neck_type,
                    "description": r.description,
                    "image_path": r.image_path,
                }
                for r in response.recommendations
            ],
            "occasion_used": response.occasion_used,
            "total_candidates": response.total_candidates,
            "message": response.message,
        },
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Results exported to {filepath}")


@router.post("", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    if not request.requirements.strip():
        raise HTTPException(status_code=400, detail="Requirements text is required")
    if not request.gender.strip():
        raise HTTPException(status_code=400, detail="Gender is required")
    if not request.size.strip():
        raise HTTPException(status_code=400, detail="Size is required")

    valid_sizes = ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL"]
    if request.size.upper() not in valid_sizes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid size. Must be one of: {', '.join(valid_sizes)}",
        )

    req_id = new_request_id()
    progress = PipelineProgress(f"Rec {req_id}", total_stages=3)

    try:
        with progress.stage("Analyzing requirements"):
            requirements = await qwen_service.analyze_requirements(request.requirements)
        if "error" in requirements:
            raise HTTPException(status_code=500, detail=requirements["error"])

        logger.info(f"AI extracted requirements: {requirements}")

        occasion = requirements.get("occasion")
        if occasion is None:
            occasion = None
        elif isinstance(occasion, str):
            occasion = [occasion] if occasion.strip() else None
        elif isinstance(occasion, list):
            occasion = [o for o in occasion if o.strip()] if occasion else None

        req_model = RequirementResponse(
            occasion=occasion,
            preferred_colors=requirements.get("preferred_colors", []),
            article_types=requirements.get("article_types", []),
            style_preferences=requirements.get("style_preferences", []),
            materials=requirements.get("materials", []),
            patterns=requirements.get("patterns", []),
            sleeve_types=requirements.get("sleeve_types", []),
            neck_types=requirements.get("neck_types", []),
            other_requirements=requirements.get("other_requirements", []),
            price_preference=requirements.get("price_preference"),
        )

        with progress.stage("Filtering candidates"):
            df = product_service.get_all_products()
            candidates = recommendation_service.generate_candidates(
                df, request.gender, request.size, req_model
            )

        logger.info(f"Total candidates after filtering: {len(candidates)}")
        if len(candidates) > 0:
            article_types = candidates["article_type"].unique().tolist()
            logger.info(f"Article types in candidates: {article_types}")
            colors = candidates["base_colour"].unique().tolist()[:10]
            logger.info(f"Colors in candidates (first 10): {colors}")

        total_candidates = len(candidates)
        message = None

        if total_candidates == 0:
            gender_filtered = recommendation_service.filter_by_gender(df, request.gender)
            size_filtered = recommendation_service.filter_by_size(gender_filtered, request.size)

            if len(size_filtered) > 0:
                candidates = size_filtered
                total_candidates = len(candidates)
                message = "No exact match was found. Here are the closest available options in your selected size."
            else:
                progress.finish()
                return RecommendationResponse(
                    recommendations=[],
                    occasion_used=occasion,
                    total_candidates=0,
                    message="No products found matching your gender and size.",
                )

        with progress.stage("Scoring & ranking"):
            logger.info(f"AI extracted article_types: {req_model.article_types}")
            logger.info(f"AI extracted preferred_colors: {req_model.preferred_colors}")
            logger.info(f"AI extracted occasion: {req_model.occasion}")
            ranked = ranking_service.calculate_scores(candidates, req_model, request.size)

        logger.info(f"Recommendations (after threshold filter):")
        for i, product in enumerate(ranked, 1):
            logger.info(f"  {i}. {product.product_id}: {product.article_type}, {product.base_colour}, "
                       f"Occasion: {product.occasion}, Score: {product.match_score}")

        if len(ranked) == 0 and total_candidates > 0:
            message = "No products strongly matching your requirements were found. Try broadening your search."

        response = RecommendationResponse(
            recommendations=ranked,
            occasion_used=occasion,
            total_candidates=total_candidates,
            message=message,
        )

        try:
            _export_results_to_json(response, request.gender, request.size, request.requirements)
        except Exception as export_err:
            logger.warning(f"Failed to export results to JSON: {export_err}")

        progress.finish()
        return response
    except Exception:
        progress.fail()
        raise
