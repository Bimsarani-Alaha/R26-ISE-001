from pydantic import BaseModel, Field
from typing import Literal, Optional


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
    match_category: Literal["exact", "alternative"] = "exact"
    unmatched_requirements: list[str] = Field(default_factory=list)
    unverified_requirements: list[str] = Field(default_factory=list)
    product_id: str
    image_path: str
    article_type: str
    base_colour: str
    occasion: Optional[str] = None
    style: str
    price: Optional[float] = None
    selected_size: str
    match_score: float
    reranker_score: Optional[float] = None
    visual_score: Optional[float] = None
    explanation: str
    category: str
    pattern: str
    material: str
    sleeve_type: str
    neck_type: str
    description: str


class RecommendationResponse(BaseModel):
    recommendations: list[ProductResult]
    alternatives: list[ProductResult] = Field(default_factory=list)
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
