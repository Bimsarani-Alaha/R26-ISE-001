"""Test-only composition for existing rule/scenario tests, without model loading."""
from dataclasses import replace
from types import SimpleNamespace

from style_recommendation.core.config import load_settings
from style_recommendation.core.resources import Resources
from style_recommendation.repositories.catalog_repository import CatalogRepository as ProductService
from style_recommendation.services.ranking_service import RankingService as Ranking
from style_recommendation.services.terminal_progress import PipelineProgress
from style_recommendation.services import recommendation_pipeline as pipeline_module

resources = Resources(replace(load_settings(), ranker_enabled=False, fashionclip_enabled=False))
resources.catalog._load_occasion_mapping()
product_service = resources.catalog
qwen_service = resources.qwen
recommendation_service = resources.candidates
ranking_service = resources.ranking
fashionclip_service = resources.fashionclip
cartographer_service = resources.cartographer


def make_ranking():
    return Ranking(product_service, recommendation_service, fashionclip_service, cartographer_service)


api = SimpleNamespace(
    qwen_service=qwen_service, product_service=product_service, PipelineProgress=PipelineProgress,
    _export_results_to_json=lambda *args: None)


async def get_recommendations(request):
    # Existing endpoint tests exercise the extracted workflow; HTTP contracts
    # are exercised independently through TestClient in integration tests.
    class Results:
        def save(self, request, response):
            api._export_results_to_json(response, request.gender, request.size, request.requirements)
    pipeline = pipeline_module.RecommendationPipeline(
        resources.requirements, product_service, recommendation_service, ranking_service, Results())
    previous = pipeline_module.PipelineProgress
    try:
        pipeline_module.PipelineProgress = api.PipelineProgress
        return await pipeline.recommend(request)
    finally:
        pipeline_module.PipelineProgress = previous


api.get_recommendations = get_recommendations
