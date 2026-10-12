from pathlib import Path
import re

import cv2
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font
from ultralytics import YOLO


ENGINE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = ENGINE_DIR / "Final Images"
ANNOTATED_IMAGE_DIR = ENGINE_DIR / "Final Images-Anno"
MODEL_PATH = ENGINE_DIR / "Y26sizeEnginev6.0.pt"
OUTPUT_PATH = ENGINE_DIR / "final_images_measurements.xlsx"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CONFIDENCE = 0.8


def image_sort_key(image_path: Path) -> tuple[int, int | str, str]:
    match = re.match(r"^\d+", image_path.stem)
    if match:
        return (0, int(match.group()), image_path.name.casefold())
    return (1, image_path.stem.casefold(), image_path.name.casefold())


def filename_labels(image_path: Path) -> tuple[str, str]:
    parts = image_path.stem.rsplit("-", 2)
    if len(parts) != 3 or not parts[0].isdigit():
        return "", ""

    size = parts[1].upper()
    gender = parts[2].lower()
    if size == "XXL":
        size = "2XL"

    if size not in {"XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL"}:
        return "", ""
    if gender not in {"m", "f"}:
        return "", ""
    return gender, size


def measure_person(keypoints: np.ndarray) -> tuple[float, float, float]:
    left_shoulder, right_shoulder = keypoints[5], keypoints[6]
    left_hip, right_hip = keypoints[11], keypoints[12]
    left_ankle, right_ankle = keypoints[15], keypoints[16]
    left_eye, right_eye = keypoints[1], keypoints[2]

    shoulder_width = float(np.linalg.norm(left_shoulder - right_shoulder))
    hip_width = float(np.linalg.norm(left_hip - right_hip))
    eye_midpoint = (left_eye + right_eye) / 2
    ankle_midpoint = (left_ankle + right_ankle) / 2
    pixel_height = float(np.linalg.norm(eye_midpoint - ankle_midpoint))
    return pixel_height, shoulder_width, hip_width


def main() -> None:
    if not IMAGE_DIR.is_dir():
        raise FileNotFoundError(f"Image folder not found: {IMAGE_DIR}")
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"YOLO model not found: {MODEL_PATH}")

    image_paths = sorted(
        (
            path
            for path in IMAGE_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=image_sort_key,
    )
    if not image_paths:
        raise FileNotFoundError(f"No supported images found in: {IMAGE_DIR}")

    ANNOTATED_IMAGE_DIR.mkdir(exist_ok=True)
    model = YOLO(str(MODEL_PATH))
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Measurements"
    worksheet.append(
        [
            "index Number",
            "pixel height",
            "pixel shoulder width",
            "pixel hip width",
            "gender",
            "size",
        ]
    )
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for index, image_path in enumerate(image_paths, start=1):
        result = model(str(image_path), conf=CONFIDENCE, verbose=False)[0]
        annotated_image = result.plot()
        annotated_path = ANNOTATED_IMAGE_DIR / image_path.name
        if not cv2.imwrite(str(annotated_path), annotated_image):
            raise OSError(f"Could not save annotated image: {annotated_path}")

        pixel_height = shoulder_width = hip_width = None
        if result.keypoints is not None:
            people = result.keypoints.xy.cpu().numpy()
            if len(people) > 0:
                pixel_height, shoulder_width, hip_width = measure_person(people[0])

        gender, size = filename_labels(image_path)
        worksheet.append(
            [index, pixel_height, shoulder_width, hip_width, gender, size]
        )

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    for column, width in {
        "A": 14,
        "B": 16,
        "C": 24,
        "D": 20,
        "E": 12,
        "F": 12,
    }.items():
        worksheet.column_dimensions[column].width = width

    for row in worksheet.iter_rows(min_row=2, min_col=2, max_col=4):
        for cell in row:
            if cell.value is not None:
                cell.number_format = "0.00"

    workbook.save(OUTPUT_PATH)
    print(f"Processed {len(image_paths)} images. Excel file saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
