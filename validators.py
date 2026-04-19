from __future__ import annotations

from pathlib import Path
from typing import Iterable

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def validate_image_path(path: str) -> Path:
    image_path = Path(path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    if image_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Only PNG/JPG/JPEG images are supported.")
    return image_path


def validate_distinct_points(points: Iterable[tuple[float, float]], name: str) -> None:
    points_list = list(points)
    unique = set(points_list)
    if len(unique) != len(points_list):
        raise ValueError(f"{name}: duplicate points are not allowed.")


def validate_axis_value(scale: str, value: float, axis_name: str) -> None:
    if scale == "log" and value <= 0:
        raise ValueError(f"{axis_name}: log scale value must be > 0.")
