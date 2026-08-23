from __future__ import annotations

CHARTS = {
    "women": [
        {"size": "XS", "shoulder_min": 29.69, "shoulder_max": 37.79, "hip_min": 25.01, "hip_max": 30.20},
        {"size": "S", "shoulder_min": 37.80, "shoulder_max": 39.64, "hip_min": 30.21, "hip_max": 32.38},
        {"size": "M", "shoulder_min": 39.65, "shoulder_max": 41.33, "hip_min": 32.39, "hip_max": 35.00},
        {"size": "L", "shoulder_min": 41.34, "shoulder_max": 41.81, "hip_min": 35.01, "hip_max": 36.50},
        {"size": "XL", "shoulder_min": 41.82, "shoulder_max": 44.31, "hip_min": 36.51, "hip_max": 42.09},
        {"size": "XXL", "shoulder_min": 44.32, "shoulder_max": 45.32, "hip_min": 36.59, "hip_max": 40.99},
        {"size": "3XL", "shoulder_min": 45.33, "shoulder_max": 45.97, "hip_min": 41.04, "hip_max": 41.53},
        {"size": "4XL", "shoulder_min": 45.98, "shoulder_max": 55.50, "hip_min": 41.54, "hip_max": 58.00},
    ],
    "men": [
        {"size": "XS", "shoulder_min": 38.00, "shoulder_max": 40.83, "hip_min": 30.00, "hip_max": 33.56},
        {"size": "S", "shoulder_min": 40.84, "shoulder_max": 42.99, "hip_min": 33.57, "hip_max": 36.50},
        {"size": "M", "shoulder_min": 43.00, "shoulder_max": 44.75, "hip_min": 35.57, "hip_max": 38.08},
        {"size": "L", "shoulder_min": 44.76, "shoulder_max": 47.56, "hip_min": 38.09, "hip_max": 40.54},
        {"size": "XL", "shoulder_min": 47.57, "shoulder_max": 49.50, "hip_min": 40.55, "hip_max": 42.00},
        {"size": "XXL", "shoulder_min": 49.51, "shoulder_max": 53.50, "hip_min": 42.01, "hip_max": 46.00},
        {"size": "3XL", "shoulder_min": 53.51, "shoulder_max": 56.50, "hip_min": 46.01, "hip_max": 52.50},
        {"size": "4XL", "shoulder_min": 56.51, "shoulder_max": 60.00, "hip_min": 52.51, "hip_max": 56.00},
    ],
}

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"]


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
