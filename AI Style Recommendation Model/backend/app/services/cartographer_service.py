"""Local Cartographer inference; failures leave rule-based ranking available."""

import logging
import math
from pathlib import Path
from threading import Lock

from ..config import RANKER_ENABLED, RANKER_MODEL_PATH, RANKER_BATCH_SIZE
from ..schemas.models import ProductResult

logger = logging.getLogger(__name__)


class CartographerService:
    def __init__(self, model_path=RANKER_MODEL_PATH, enabled=RANKER_ENABLED):
        self.model_path = Path(model_path)
        self.enabled = enabled
        self._model = None
        self._tokenizer = None
        self._failed = False
        self._lock = Lock()

    @staticmethod
    def product_text(product: ProductResult) -> str:
        # The checkpoint was trained on titles. Use concise catalogue attributes,
        # not generated descriptions that may invent unsupported properties.
        values = [product.base_colour, product.material, product.pattern,
                  product.sleeve_type, product.neck_type, product.article_type,
                  product.style, product.occasion]
        return " ".join(str(v).strip() for v in values
                        if v is not None and str(v).strip().casefold()
                        not in {"", "nan", "none", "null", "unknown", "n/a", "na"})

    def _predict(self, query: str, texts: list[str]) -> list[float]:
        for filename in ("config.json", "model.safetensors", "tokenizer_config.json", "tokenizer.json"):
            if not (self.model_path / filename).is_file():
                raise FileNotFoundError(f"Missing local ranker file: {filename}")

        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        if self._model is None:
            tokenizer = AutoTokenizer.from_pretrained(str(self.model_path), local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path), local_files_only=True, use_safetensors=True)
            model.eval()
            self._tokenizer, self._model = tokenizer, model
            logger.info("Loaded Cartographer ranker from %s (CPU)", self.model_path)

        scores = []
        with torch.inference_mode():
            for start in range(0, len(texts), RANKER_BATCH_SIZE):
                batch = texts[start:start + RANKER_BATCH_SIZE]
                inputs = self._tokenizer([query] * len(batch), batch, padding=True,
                                         truncation=True, max_length=256, return_tensors="pt")
                scores.extend(self._model(**inputs).logits.reshape(-1).tolist())
        return scores

    def score(self, query: str, products: list[ProductResult]) -> list[float] | None:
        if not self.enabled or not query.strip() or not products:
            return None
        # Serialize loading/inference and do not repeatedly retry a broken model.
        with self._lock:
            if self._failed:
                return None
            try:
                scores = self._predict(query, [self.product_text(p) for p in products])
                if len(scores) != len(products) or not all(math.isfinite(s) for s in scores):
                    raise ValueError("Ranker returned invalid scores")
                return scores
            except Exception:
                self._failed = True
                logger.warning("Cartographer unavailable; fallback to rule-based ranking. "
                               "Fix the model/dependencies and restart to retry.", exc_info=True)
                return None


cartographer_service = CartographerService()
