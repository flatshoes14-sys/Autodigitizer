from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np


@dataclass
class AutoExtractResult:
    pixel_points: np.ndarray
    mask: np.ndarray
    warnings: list[str]
    confidence: float


def extract_curve_pixels(
    image_bgr: np.ndarray,
    roi: Optional[Tuple[int, int, int, int]] = None,
    hsv_lower: Tuple[int, int, int] = (0, 0, 0),
    hsv_upper: Tuple[int, int, int] = (180, 255, 255),
    min_component_area: int = 15,
) -> AutoExtractResult:
    """Conservative color-threshold extraction for simple clean graphs."""
    warnings: list[str] = []

    if roi is None:
        x, y, w, h = 0, 0, image_bgr.shape[1], image_bgr.shape[0]
    else:
        x, y, w, h = roi

    cropped = image_bgr[y : y + h, x : x + w]
    hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(hsv_lower), np.array(hsv_upper))

    kernel = np.ones((3, 3), np.uint8)
    clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(clean, connectivity=8)
    filtered = np.zeros_like(clean)
    kept_components = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_component_area:
            filtered[labels == i] = 255
            kept_components += 1

    ys, xs = np.where(filtered > 0)
    if len(xs) == 0:
        warnings.append("No line pixels found for this color range/ROI.")
        return AutoExtractResult(np.empty((0, 2)), filtered, warnings, confidence=0.0)

    points = np.column_stack([xs + x, ys + y]).astype(float)
    points = points[np.argsort(points[:, 0], kind="stable")]

    density = len(points) / max(w * h, 1)
    confidence = 0.85
    if density > 0.25:
        warnings.append("Very dense mask detected; likely includes text, axes, or multiple curves.")
        confidence -= 0.35
    if kept_components > 25:
        warnings.append("Many disconnected regions detected; graph may be complex/overlapping.")
        confidence -= 0.2
    if len(points) < 30:
        warnings.append("Few points extracted; consider semi-automatic mode for accuracy.")
        confidence -= 0.2

    confidence = max(0.0, min(1.0, confidence))
    if confidence < 0.6:
        warnings.append("Low confidence extraction. Recommended: semi-automatic clicking.")

    return AutoExtractResult(pixel_points=points, mask=filtered, warnings=warnings, confidence=confidence)
