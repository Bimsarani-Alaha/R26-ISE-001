from __future__ import annotations

CHARTS = {
    "women": [
        {"size": "XXS", "shoulder_min": 34.0, "shoulder_max": 35.5, "hip_min": 28.0, "hip_max": 30.0},
        {"size": "XS", "shoulder_min": 35.5, "shoulder_max": 37.0, "hip_min": 30.0, "hip_max": 32.0},
        {"size": "S", "shoulder_min": 37.0, "shoulder_max": 38.5, "hip_min": 32.0, "hip_max": 34.0},
        {"size": "M", "shoulder_min": 38.5, "shoulder_max": 40.5, "hip_min": 34.0, "hip_max": 36.5},
        {"size": "L", "shoulder_min": 40.5, "shoulder_max": 42.5, "hip_min": 36.5, "hip_max": 39.0},
        {"size": "XL", "shoulder_min": 42.5, "shoulder_max": 44.5, "hip_min": 39.0, "hip_max": 41.5},
        {"size": "XXL", "shoulder_min": 44.5, "shoulder_max": 46.5, "hip_min": 41.5, "hip_max": 44.0},
        {"size": "3XL", "shoulder_min": 46.5, "shoulder_max": 48.5, "hip_min": 44.0, "hip_max": 47.0},
        {"size": "4XL", "shoulder_min": 48.5, "shoulder_max": 51.0, "hip_min": 47.0, "hip_max": 50.0},
    ],
    "men": [
        {"size": "XXS", "shoulder_min": 38.0, "shoulder_max": 40.0, "hip_min": 30.0, "hip_max": 33.0},
        {"size": "XS", "shoulder_min": 40.0, "shoulder_max": 42.0, "hip_min": 33.0, "hip_max": 35.0},
        {"size": "S", "shoulder_min": 42.0, "shoulder_max": 44.0, "hip_min": 35.0, "hip_max": 37.0},
        {"size": "M", "shoulder_min": 44.0, "shoulder_max": 47.0, "hip_min": 37.0, "hip_max": 40.0},
        {"size": "L", "shoulder_min": 47.0, "shoulder_max": 50.0, "hip_min": 40.0, "hip_max": 43.0},
        {"size": "XL", "shoulder_min": 50.0, "shoulder_max": 53.0, "hip_min": 43.0, "hip_max": 46.0},
        {"size": "XXL", "shoulder_min": 53.0, "shoulder_max": 56.0, "hip_min": 46.0, "hip_max": 49.0},
        {"size": "3XL", "shoulder_min": 56.0, "shoulder_max": 59.0, "hip_min": 49.0, "hip_max": 52.0},
        {"size": "4XL", "shoulder_min": 59.0, "shoulder_max": 62.0, "hip_min": 52.0, "hip_max": 55.0},
    ],
}

SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"]


def normalize_gender(gender: str) -> str:
    if not gender:
        return "women"

    normalized = gender.strip().lower()
    if normalized.startswith("m"):
        return "men"
    if normalized.startswith("w"):
        return "women"
    if normalized.startswith("u"):
        return "women"
    return "women"


def get_chart_for_gender(gender: str) -> list[dict[str, float | str]]:
    return CHARTS.get(normalize_gender(gender), CHARTS["women"])


def _distance_to_range(value: float, minimum: float, maximum: float) -> float:
    if value < minimum:
        return minimum - value
    if value > maximum:
        return value - maximum
    return 0.0


def _estimate_closest_size(shoulder_cm: float, hip_cm: float, chart: list[dict[str, float | str]]) -> str:
    best_size = chart[0]["size"]
    best_score = float("inf")

    for entry in chart:
        shoulder_distance = _distance_to_range(shoulder_cm, entry["shoulder_min"], entry["shoulder_max"])
        hip_distance = _distance_to_range(hip_cm, entry["hip_min"], entry["hip_max"])
        score = shoulder_distance + hip_distance

        if score < best_score:
            best_score = score
            best_size = entry["size"]
        elif score == best_score:
            current_index = SIZE_ORDER.index(entry["size"])
            best_index = SIZE_ORDER.index(best_size)
            if current_index > best_index:
                best_size = entry["size"]

    return best_size


def _range_size(value: float, chart: list[dict[str, float | str]], min_key: str, max_key: str) -> str | None:
    for entry in chart:
        if entry[min_key] <= value <= entry[max_key]:
            return entry["size"]
    return None


def get_size_label(shoulder_cm: float, hip_cm: float, gender: str = "women") -> str:
    chart = get_chart_for_gender(gender)
    shoulder_size = _range_size(shoulder_cm, chart, "shoulder_min", "shoulder_max")
    hip_size = _range_size(hip_cm, chart, "hip_min", "hip_max")

    if shoulder_size and hip_size:
        if shoulder_size == hip_size:
            return shoulder_size
        shoulder_index = SIZE_ORDER.index(shoulder_size)
        hip_index = SIZE_ORDER.index(hip_size)
        return shoulder_size if shoulder_index >= hip_index else hip_size

    if shoulder_size:
        return shoulder_size
    if hip_size:
        return hip_size

    return _estimate_closest_size(shoulder_cm, hip_cm, chart)


if __name__ == "__main__":
    import pprint

    example = get_size_label(38.8, 35.2, "women")
    pprint.pp({"predicted_size": example})
