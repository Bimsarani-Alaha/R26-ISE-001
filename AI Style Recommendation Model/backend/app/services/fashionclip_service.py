"""Offline Marqo FashionSigLIP image/text retrieval using the supplied ONNX files."""

import hashlib
import atexit
import html
import io
import json
import logging
import os
from pathlib import Path
import string
import struct
import subprocess
import sys
import tempfile
from threading import Lock

import numpy as np
from PIL import Image, ImageOps
from .fashionclip_worker import read_exact

from ..config import (
    FASHIONCLIP_ENABLED, FASHIONCLIP_MODEL_PATH, FASHIONCLIP_CACHE_DIR,
    FASHIONCLIP_BATCH_SIZE, FASHIONCLIP_THREADS, IMAGES_DIR,
)

logger = logging.getLogger(__name__)


class FashionClipService:
    def __init__(self, model_path=FASHIONCLIP_MODEL_PATH, image_dir=IMAGES_DIR,
                 cache_dir=FASHIONCLIP_CACHE_DIR, enabled=FASHIONCLIP_ENABLED):
        self.model_path = Path(model_path)
        self.image_dir = Path(image_dir).resolve()
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self._worker = self._tokenizer = None
        self._memory = {}
        self._namespace = None
        self._failed = False
        self._lock = Lock()

    def status(self) -> str:
        # "unknown" until the first request, since encoders load lazily.
        if not self.enabled:
            return "disabled"
        if self._failed:
            return "unavailable"
        return "loaded" if self._worker is not None else "pending"

    def resolve_image(self, value: str) -> Path | None:
        value = str(value).replace("\\", "/").strip()
        if value.lower().startswith("images/"):
            value = value[7:]
        if not value or ":" in value:
            return None
        path = (self.image_dir / value).resolve()
        if not path.is_relative_to(self.image_dir):
            return None
        return path if path.is_file() else None

    def _load(self):
        if self._worker is not None:
            return
        for name in ("onnx/text_model.onnx", "onnx/vision_model.onnx", "tokenizer.json",
                     "preprocessor_config.json"):
            if not (self.model_path / name).is_file():
                raise FileNotFoundError(f"Missing local FashionSigLIP file: {name}")
        from tokenizers import Tokenizer

        # Explicit local paths: no Hub wrapper, remote code or network requests.
        tokenizer = Tokenizer.from_file(str(self.model_path / "tokenizer.json"))
        tokenizer.enable_truncation(max_length=64)
        tokenizer.enable_padding(length=64, pad_id=tokenizer.token_to_id("</s>"), pad_token="</s>")
        self._preprocess = json.loads((self.model_path / "preprocessor_config.json").read_text())
        self._tokenizer = tokenizer
        self._worker = subprocess.Popen(
            [sys.executable, "-u", str(Path(__file__).with_name("fashionclip_worker.py")),
             str(self.model_path.resolve()), str(FASHIONCLIP_THREADS)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        atexit.register(self.close)
        if self._worker.stdout.readline() != b"READY\n":
            raise RuntimeError("FashionSigLIP worker failed to initialize")
        logger.info("Loaded local FashionSigLIP ONNX encoders in CPU worker")

    def close(self):
        worker, self._worker = self._worker, None
        if worker is not None:
            if worker.poll() is None:
                worker.terminate()
                worker.wait()
            worker.stdin.close()
            worker.stdout.close()

    def _run(self, command, values):
        buffer = io.BytesIO()
        np.save(buffer, values, allow_pickle=False)
        payload = buffer.getvalue()
        self._worker.stdin.write(command + struct.pack("<Q", len(payload)) + payload)
        self._worker.stdin.flush()
        status = read_exact(self._worker.stdout, 1)
        size = struct.unpack("<Q", read_exact(self._worker.stdout, 8))[0]
        response = read_exact(self._worker.stdout, size)
        if status != b"O":
            raise RuntimeError(response.decode(errors="replace"))
        return np.load(io.BytesIO(response), allow_pickle=False)

    @staticmethod
    def _normalize(features):
        features = np.asarray(features, dtype=np.float32)
        norms = np.linalg.norm(features, axis=-1, keepdims=True)
        if not np.isfinite(features).all() or np.any(norms <= 0):
            raise ValueError("Invalid FashionSigLIP embedding")
        return features / norms

    def _encode_text(self, query):
        import ftfy

        # Match the canonical text cleaning in the supplied Marqo processor.
        query = html.unescape(html.unescape(ftfy.fix_text(query))).strip()
        query = query.replace("_", " ").translate(str.maketrans("", "", string.punctuation))
        query = " ".join(query.lower().split())
        ids = np.asarray([self._tokenizer.encode(query).ids], dtype=np.int64)
        return self._normalize(self._run(b"T", ids))[0]

    def _encode_images(self, images):
        cfg = self._preprocess
        size = (cfg["size"]["width"], cfg["size"]["height"])
        mean = np.asarray(cfg["image_mean"], dtype=np.float32)
        std = np.asarray(cfg["image_std"], dtype=np.float32)
        pixels = []
        for image in images:
            resized = image.resize(size, resample=Image.Resampling(cfg["resample"]))
            values = np.asarray(resized, dtype=np.float32) * cfg["rescale_factor"]
            pixels.append(((values - mean) / std).transpose(2, 0, 1))
        batch = np.stack(pixels).astype(np.float32)
        return self._normalize(self._run(b"I", batch))

    def _cache_key(self, path):
        if self._namespace is None:
            parts = ["fashion-siglip-preprocess-v1", str(self.model_path.resolve())]
            for name in ("onnx/vision_model.onnx", "preprocessor_config.json"):
                file = self.model_path / name
                if file.exists():
                    stat = file.stat()
                    parts.append(f"{name}:{stat.st_mtime_ns}:{stat.st_size}")
            self._namespace = "|".join(parts)
        stat = path.stat()
        value = f"{self._namespace}|{path}|{stat.st_mtime_ns}|{stat.st_size}"
        return hashlib.sha256(value.encode()).hexdigest()

    def _cached(self, key):
        if key in self._memory:
            return self._memory[key]
        try:
            feature = np.load(self.cache_dir / f"{key}.npy", allow_pickle=False)
            if feature.ndim != 1:
                return None
            feature = self._normalize(feature)
            self._memory[key] = feature
            return feature
        except (OSError, ValueError, EOFError):
            return None

    def _save(self, key, feature):
        self._memory[key] = feature
        temporary = None
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, suffix=".tmp", delete=False) as file:
                temporary = Path(file.name)
                np.save(file, feature, allow_pickle=False)
            os.replace(temporary, self.cache_dir / f"{key}.npy")
        except OSError:
            logger.warning("Cannot persist visual embedding; using in-memory cache")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def score(self, query, products) -> list[float | None] | None:
        if not self.enabled or not query.strip() or not products:
            return None
        with self._lock:
            if self._failed:
                return None
            try:
                paths = [self.resolve_image(p.image_path) for p in products]
                if not any(paths):
                    return None
                self._load()
                text = self._encode_text(query)
                features = [None] * len(products)
                pending = []
                for index, path in enumerate(paths):
                    if path is None:
                        continue
                    try:
                        key = self._cache_key(path)
                    except OSError:
                        continue
                    feature = self._cached(key)
                    if feature is not None and feature.shape == text.shape:
                        features[index] = feature
                    else:
                        pending.append((index, path, key))
                for start in range(0, len(pending), FASHIONCLIP_BATCH_SIZE):
                    images, entries = [], []
                    for index, path, key in pending[start:start + FASHIONCLIP_BATCH_SIZE]:
                        try:
                            with Image.open(path) as image:
                                images.append(ImageOps.exif_transpose(image).convert("RGB"))
                            entries.append((index, key))
                        except (OSError, ValueError):
                            logger.warning("Skipping unreadable product image: %s", path.name)
                    if not images:
                        continue
                    try:
                        encoded = self._encode_images(images)
                    finally:
                        for image in images:
                            image.close()
                    if encoded.shape != (len(entries), text.shape[0]):
                        raise ValueError("Unexpected visual embedding shape")
                    for (index, key), feature in zip(entries, encoded):
                        features[index] = feature
                        self._save(key, feature)
                scores = [None if feature is None else float(np.clip(feature @ text, -1, 1))
                          for feature in features]
                if not all(s is None or np.isfinite(s) for s in scores):
                    raise ValueError("Invalid visual similarity scores")
                return scores if any(s is not None for s in scores) else None
            except Exception:
                self._failed = True
                self.close()
                logger.warning("FashionSigLIP unavailable; fallback to text ranking. "
                               "Fix files/dependencies and restart to retry.", exc_info=True)
                return None


fashionclip_service = FashionClipService()
