SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"]

TRAINING_DATA = [
    ("women", 29.69, 25.01, "S"), ("women", 35.53, 30.19, "M"),
    ("women", 37.80, 31.70, "S"), ("women", 38.25, 30.21, "S"),
    ("women", 38.75, 31.16, "S"), ("women", 39.51, 31.41, "S"),
    ("women", 39.65, 33.38, "L"), ("women", 40.22, 34.92, "XL"),
    ("women", 40.71, 33.70, "L"), ("women", 40.93, 33.07, "M"),
    ("women", 41.21, 33.24, "S"), ("women", 41.34, 36.27, "XL"),
    ("women", 41.82, 37.02, "XXL"), ("women", 42.13, 35.47, "XL"),
    ("women", 42.15, 35.09, "S"), ("women", 42.53, 37.42, "M"),
    ("women", 42.60, 36.74, "L"), ("women", 43.28, 38.55, "L"),
    ("women", 43.40, 38.41, "3XL"), ("women", 43.93, 38.39, "XL"),
    ("women", 44.32, 36.59, "XL"), ("women", 44.46, 38.33, "L"),
    ("women", 45.33, 41.53, "3XL"), ("women", 45.48, 41.04, "4XL"),
    ("men", 40.84, 33.57, "M"), ("men", 41.90, 36.50, "M"),
    ("men", 43.00, 35.60, "M"), ("men", 43.39, 36.66, "M"),
    ("men", 43.59, 35.57, "M"), ("men", 43.92, 36.34, "M"),
    ("men", 44.15, 38.08, "M"), ("men", 44.46, 37.97, "M"),
    ("men", 44.76, 39.83, "XXL"), ("men", 45.57, 38.93, "L"),
    ("men", 47.57, 38.90, "M"), ("men", 47.63, 40.54, "XL"),
    ("men", 47.63, 40.15, "L"), ("men", 48.46, 42.09, "XXL"),
]


def _build_charts(data: list[tuple[str, float, float, str]]) -> dict[str, list[dict[str, float | str]]]:
    charts: dict[str, list[dict[str, float | str]]] = {"women": [], "men": []}
    for gender in charts:
        for size in SIZE_ORDER:
            rows = [(shoulder, hip) for row_gender, shoulder, hip, row_size in data
                    if row_gender == gender and row_size == size]
            if rows:
                shoulders, hips = zip(*rows)
                charts[gender].append({
                    "size": size,
                    "shoulder_min": min(shoulders), "shoulder_max": max(shoulders),
                    "hip_min": min(hips), "hip_max": max(hips),
                    "shoulder_center": sum(shoulders) / len(shoulders),
                    "hip_center": sum(hips) / len(hips),
                })
    return charts


CHARTS = _build_charts(TRAINING_DATA)


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


def _normalize_range(value: float, minimum: float, maximum: float) -> float:
    if maximum == minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def _estimate_closest_size(
    shoulder_cm: float,
    hip_cm: float,
    chart: list[dict[str, float | str]],
    gender: str,
) -> str:
    best_size = chart[0]["size"]
    best_score = float("inf")
    shoulder_min = min(entry["shoulder_min"] for entry in chart)
    shoulder_max = max(entry["shoulder_max"] for entry in chart)
    hip_min = min(entry["hip_min"] for entry in chart)
    hip_max = max(entry["hip_max"] for entry in chart)

    normalized_shoulder = _normalize_range(shoulder_cm, shoulder_min, shoulder_max)
    normalized_hip = _normalize_range(hip_cm, hip_min, hip_max)

    for row_gender, sample_shoulder, sample_hip, sample_size in TRAINING_DATA:
        if row_gender != gender:
            continue

        shoulder_distance = abs(
            normalized_shoulder
            - _normalize_range(sample_shoulder, shoulder_min, shoulder_max)
        )
        hip_distance = abs(
            normalized_hip
            - _normalize_range(sample_hip, hip_min, hip_max)
        )
        score = shoulder_distance + hip_distance

        if score < best_score:
            best_score = score
            best_size = sample_size
        elif score == best_score:
            current_index = SIZE_ORDER.index(sample_size)
            best_index = SIZE_ORDER.index(best_size)
            if current_index > best_index:
                best_size = sample_size

    return best_size


def _range_size(value: float, chart: list[dict[str, float | str]], min_key: str, max_key: str) -> str | None:
    for entry in chart:
        if entry[min_key] <= value <= entry[max_key]:
            return entry["size"]
    return None


def get_size_label(shoulder_cm: float, hip_cm: float, gender: str = "women") -> str:
    normalized_gender = normalize_gender(gender)
    chart = get_chart_for_gender(normalized_gender)
    return _estimate_closest_size(shoulder_cm, hip_cm, chart, normalized_gender)


if __name__ == "__main__":
    import pprint

    example = get_size_label(38.8, 35.2, "women")
    pprint.pp({"predicted_size": example})
