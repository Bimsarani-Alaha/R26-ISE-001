from pydantic import BaseModel
from typing import Optional


class RequirementRequest(BaseModel):
    requirements: str


class RequirementResponse(BaseModel):
    occasion: Optional[list[str]] = None
    preferred_colors: list[str] = []
    article_types: list[str] = []
    style_preferences: list[str] = []
    materials: list[str] = []
    patterns: list[str] = []
    sleeve_types: list[str] = []
    neck_types: list[str] = []
    other_requirements: list[str] = []
    price_preference: Optional[dict] = None


class RecommendationRequest(BaseModel):
    gender: str
    size: str
    requirements: str


class ProductResult(BaseModel):
    product_id: str
    image_path: str
    article_type: str
    base_colour: str
    occasion: Optional[str] = None
    style: str
    price: Optional[float] = None
    selected_size: str
    match_score: float
    explanation: str
    category: str
    pattern: str
    material: str
    sleeve_type: str
    neck_type: str
    description: str


class RecommendationResponse(BaseModel):
    recommendations: list[ProductResult]
    occasion_used: Optional[list[str]] = None
    total_candidates: int
    message: Optional[str] = None


class StylistRequest(BaseModel):
    gender: str
    size: str
    requirements: str
    product_id: str


class StylistResponse(BaseModel):
    summary: str
    accessories: list[str] = []
    footwear: list[str] = []
    color_combinations: list[str] = []
    layering: list[str] = []
    occasion_tip: str = ""
    complementary_items: list[str] = []
