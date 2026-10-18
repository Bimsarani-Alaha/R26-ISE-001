"""Recommendation use case with independently replaceable collaborators."""
import logging
from starlette.concurrency import run_in_threadpool
from ..schemas.models import RecommendationRequest, RecommendationResponse
from .terminal_progress import PipelineProgress, new_request_id

logger = logging.getLogger(__name__)


class RecommendationPipeline:
    def __init__(self, requirements, catalog, candidates, ranking, results):
        self.requirements = requirements
        self.catalog = catalog
        self.candidates = candidates
        self.ranking = ranking
        self.results = results

    def _candidates(self, request, requirements):
        return self.candidates.generate_candidates(
            self.catalog.get_all_products(), request.gender, request.size, requirements)

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        progress = PipelineProgress(f"Rec {new_request_id()}", total_stages=3)
        try:
            with progress.stage("Analyzing requirements"):
                requirements = await self.requirements.analyze(request.requirements)
            with progress.stage("Filtering candidates"):
                candidates = await run_in_threadpool(self._candidates, request, requirements)
            count = len(candidates)
            if count == 0:
                response = RecommendationResponse(
                    recommendations=[], occasion_used=requirements.occasion, total_candidates=0,
                    message="No products match your requested clothing type, occasion, gender, size and budget.")
            else:
                with progress.stage("Scoring & ranking"):
                    exact, alternatives = await run_in_threadpool(
                        self.ranking.calculate_groups, candidates, requirements, request.size,
                        query=request.requirements)
                response = RecommendationResponse(
                    recommendations=exact, alternatives=alternatives,
                    occasion_used=requirements.occasion, total_candidates=count,
                    message=("No products match all your requirements. Similar alternatives are shown separately."
                             if not exact else None))
                try:
                    await run_in_threadpool(self.results.save, request, response)
                except Exception:
                    logger.warning("Failed to export recommendation results", exc_info=True)
            progress.finish()
            return response
        except BaseException:
            progress.fail()
            raise
        finally:
            progress.close()
