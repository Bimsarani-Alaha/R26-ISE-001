"""Optional recommendation exports, kept outside HTTP request handling."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..schemas.models import RecommendationRequest, RecommendationResponse


class ResultRepository:
    def __init__(self, results_dir: Path):
        self.results_dir = Path(results_dir)

    def save(self, request: RecommendationRequest, response: RecommendationResponse) -> Path:
        self.results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc)
        path = self.results_dir / f"recommendation_{timestamp:%Y%m%d_%H%M%S}_{uuid4().hex}.json"
        data = {"timestamp": timestamp.isoformat(), "request": request.model_dump(),
                "response": response.model_dump()}
        with path.open("x", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False, allow_nan=False)
        return path
