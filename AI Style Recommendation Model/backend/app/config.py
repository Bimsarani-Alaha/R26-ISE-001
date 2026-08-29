import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"
CONFIG_DIR = BASE_DIR / "config"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

DATASET_PATH = DATA_DIR / "product_full_updated.csv"
OCCASION_MAPPING_PATH = CONFIG_DIR / "occasion_mapping.json"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen2.5:7b")

REQUIRED_COLUMNS = [
    "product_id",
    "gender",
    "category",
    "article_type",
    "base_colour",
    "occasion",
    "available_sizes",
    "pattern",
    "sleeve_type",
    "neck_type",
    "material",
    "style",
    "description",
    "price",
    "image_path",
]

VALID_SIZES = ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL"]

WEIGHTS_WITH_OCCASION = {
    "article_type": 0.20,
    "occasion": 0.30,
    "base_colour": 0.20,
    "style": 0.15,
    "pattern": 0.05,
    "material": 0.05,
    "sleeve_type": 0.025,
    "neck_type": 0.025,
}

WEIGHTS_WITHOUT_OCCASION = {
    "article_type": 0.30,
    "base_colour": 0.25,
    "style": 0.20,
    "pattern": 0.10,
    "material": 0.05,
    "sleeve_type": 0.05,
    "neck_type": 0.05,
}

TOP_K = 5
MIN_SCORE_THRESHOLD = 0.35
