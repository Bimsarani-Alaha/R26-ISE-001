"""Composition root: one dependency graph per FastAPI application."""
import logging
from starlette.concurrency import run_in_threadpool
from .config import load_settings
from .logging import configure_logging
from ..inference.qwen_service import QwenService
from ..inference.cartographer_service import CartographerService
from ..inference.fashionclip_service import FashionClipService
from ..repositories.catalog_repository import CatalogRepository
from ..repositories.result_repository import ResultRepository
from ..services.recommendation_service import RecommendationService
from ..services.ranking_service import RankingService
from ..services.requirement_service import RequirementService
from ..services.recommendation_pipeline import RecommendationPipeline
from ..services.stylist_service import StylistService

logger = logging.getLogger(__name__)


class Resources:
    def __init__(self, settings=None):
        self.settings = settings or load_settings()
        self.catalog = CatalogRepository(self.settings)
        self.qwen = QwenService(self.settings)
        self.fashionclip = FashionClipService(settings=self.settings)
        self.cartographer = CartographerService(settings=self.settings)
        self.candidates = RecommendationService(self.catalog)
        self.ranking = RankingService(self.catalog, self.candidates, self.fashionclip,
                                      self.cartographer, self.settings.ranker_candidates_per_group)
        self.requirements = RequirementService(self.qwen)
        self.results = ResultRepository(self.settings.results_dir)
        self.pipeline = RecommendationPipeline(self.requirements, self.catalog, self.candidates,
                                               self.ranking, self.results)
        self.stylist = StylistService(self.requirements, self.catalog, self.qwen)

    async def start(self):
        configure_logging()
        try:
            await run_in_threadpool(self.catalog.load_dataset)
        except Exception:
            logger.exception("Catalog initialization failed; backend is degraded")
        connected = await self.qwen.check_connection()
        logger.info("Ollama available: %s", connected)

    async def close(self):
        await run_in_threadpool(self.fashionclip.close)
