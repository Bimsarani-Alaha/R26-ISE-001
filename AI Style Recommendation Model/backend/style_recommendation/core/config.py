"""Application settings; relative paths use the model project directory."""
import os
from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = PACKAGE_DIR.parent.parent

REQUIRED_COLUMNS = [
    "product_id", "gender", "category", "article_type", "base_colour", "occasion",
    "available_sizes", "pattern", "sleeve_type", "neck_type", "material", "style",
    "description", "price", "image_path",
]
VALID_SIZES = ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL"]
WEIGHTS_WITH_OCCASION = {
    "article_type": .20, "occasion": .30, "base_colour": .20, "style": .15,
    "pattern": .05, "material": .05, "sleeve_type": .025, "neck_type": .025,
}
WEIGHTS_WITHOUT_OCCASION = {
    "article_type": .30, "base_colour": .25, "style": .20, "pattern": .10,
    "material": .05, "sleeve_type": .05, "neck_type": .05,
}
TOP_K = 5
MIN_SCORE_THRESHOLD = .35


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    dataset_path: Path
    images_dir: Path
    occasion_mapping_path: Path
    results_dir: Path
    artifacts_dir: Path
    prompts_dir: Path
    ollama_base_url: str = "http://localhost:11434"
    qwen_model: str = "qwen2.5:7b"
    qwen_stylist_model: str = "qwen3-vl:8b"
    qwen_stylist_timeout: float = 600.0
    ranker_enabled: bool = True
    ranker_model_path: Path = Path("artifacts/ranker")
    ranker_batch_size: int = 16
    ranker_candidates_per_group: int = 50
    fashionclip_enabled: bool = True
    fashionclip_model_path: Path = Path("artifacts/fashionclip")
    fashionclip_cache_dir: Path = Path(".cache/fashionclip")
    fashionclip_batch_size: int = 8
    fashionclip_threads: int = 2


def load_settings() -> Settings:
    # Explicit paths avoid configuration changing when a server changes cwd.
    from dotenv import load_dotenv
    load_dotenv(PACKAGE_DIR.parent / ".env", override=False)
    load_dotenv(DEFAULT_BASE_DIR / ".env", override=False)
    base = Path(os.getenv("STYLE_BASE_DIR", str(DEFAULT_BASE_DIR))).expanduser()
    base = (base if base.is_absolute() else DEFAULT_BASE_DIR / base).resolve()

    def path(name, default):
        value = Path(os.getenv(name, str(default))).expanduser()
        return (value if value.is_absolute() else base / value).resolve()

    def flag(name):
        return os.getenv(name, "true").lower() in {"1", "true", "yes"}

    artifacts = path("ARTIFACTS_DIR", "artifacts")
    return Settings(
        base_dir=base,
        dataset_path=path("DATASET_PATH", "data/product_full_updated.csv"),
        images_dir=path("IMAGES_DIR", "Images"),
        occasion_mapping_path=path("OCCASION_MAPPING_PATH", "config/occasion_mapping.json"),
        results_dir=path("RESULTS_DIR", "results"), artifacts_dir=artifacts,
        prompts_dir=PACKAGE_DIR / "prompts",
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        qwen_model=os.getenv("QWEN_MODEL", "qwen2.5:7b"),
        qwen_stylist_model=os.getenv("QWEN_STYLIST_MODEL", "qwen3-vl:8b"),
        qwen_stylist_timeout=float(os.getenv("QWEN_STYLIST_TIMEOUT", "600")),
        ranker_enabled=flag("RANKER_ENABLED"),
        ranker_model_path=path("RANKER_MODEL_PATH", artifacts / "ranker"),
        ranker_batch_size=max(1, int(os.getenv("RANKER_BATCH_SIZE", "16"))),
        ranker_candidates_per_group=max(TOP_K, int(os.getenv("RANKER_CANDIDATES_PER_GROUP", "50"))),
        fashionclip_enabled=flag("FASHIONCLIP_ENABLED"),
        fashionclip_model_path=path("FASHIONCLIP_MODEL_PATH", artifacts / "fashionclip"),
        fashionclip_cache_dir=path("FASHIONCLIP_CACHE_DIR", ".cache/fashionclip"),
        fashionclip_batch_size=max(1, int(os.getenv("FASHIONCLIP_BATCH_SIZE", "8"))),
        fashionclip_threads=max(1, int(os.getenv("FASHIONCLIP_THREADS", "2"))),
    )
