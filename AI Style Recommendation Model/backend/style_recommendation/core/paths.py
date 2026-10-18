"""Resolve catalog image references inside the configured image directory."""
from pathlib import Path


def image_path(directory: Path, value: str) -> Path | None:
    value = str(value).replace("\\", "/").strip()
    if value.lower().startswith("images/"):
        value = value[7:]
    if not value or ":" in value or value.startswith("/"):
        return None
    root = directory.resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        return None
    return path
