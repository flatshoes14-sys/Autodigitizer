from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np

from auto_extract import extract_curve_pixels
from calibration import AxisCalibration, AxisReference, GraphCalibration
from digitizer import convert_pixels_to_dataframe
from io_utils import (
    ensure_output_dir,
    save_curve_csv,
    save_markdown_report,
    save_overlay_image,
    save_replot,
)
from validators import validate_axis_value, validate_image_path


def _ask_scale(axis_name: str) -> str:
    while True:
        value = input(f"{axis_name}-axis scale [linear/log]: ").strip().lower() or "linear"
        if value in {"linear", "log"}:
            return value
        print("Please enter 'linear' or 'log'.")


def _ask_float(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("Please enter a numeric value.")


def _get_clicks(image_rgb: np.ndarray, n: int, title: str) -> list[Tuple[float, float]]:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(image_rgb)
    ax.set_title(title)
    pts = plt.ginput(n=n, timeout=-1)
    plt.close(fig)
    return [(float(x), float(y)) for x, y in pts]


def calibrate_graph(image_rgb: np.ndarray) -> GraphCalibration:
    print("Calibration step: click two x-axis reference points on the plot area.")
    x_pts = _get_clicks(image_rgb, 2, "Click 2 points on X axis (left then right).")
    x_scale = _ask_scale("X")
    x1 = _ask_float("Real X value for first clicked point: ")
    x2 = _ask_float("Real X value for second clicked point: ")
    validate_axis_value(x_scale, x1, "X")
    validate_axis_value(x_scale, x2, "X")

    print("Now click two y-axis reference points on the plot area.")
    y_pts = _get_clicks(image_rgb, 2, "Click 2 points on Y axis (bottom then top).")
    y_scale = _ask_scale("Y")
    y1 = _ask_float("Real Y value for first clicked point: ")
    y2 = _ask_float("Real Y value for second clicked point: ")
    validate_axis_value(y_scale, y1, "Y")
    validate_axis_value(y_scale, y2, "Y")

    x_axis = AxisCalibration(
        AxisReference(pixel=x_pts[0][0], value=x1),
        AxisReference(pixel=x_pts[1][0], value=x2),
        scale=x_scale,
    )
    y_axis = AxisCalibration(
        AxisReference(pixel=y_pts[0][1], value=y1),
        AxisReference(pixel=y_pts[1][1], value=y2),
        scale=y_scale,
    )
    return GraphCalibration(x_axis=x_axis, y_axis=y_axis)


def run_semi_automatic(image_bgr: np.ndarray, calibration: GraphCalibration, output_dir: Path) -> list[str]:
    dataset_names: list[str] = []
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    while True:
        dataset_name = input("Dataset name (or blank to finish): ").strip()
        if not dataset_name:
            break

        print("Click curve points. Close plot window or press Enter when done.")
        points = _get_clicks(image_rgb, -1, f"Click points for '{dataset_name}'")
        if not points:
            print("No points clicked; skipping dataset.")
            continue

        df = convert_pixels_to_dataframe(dataset_name, points, calibration)
        save_curve_csv(df, output_dir, dataset_name)
        save_overlay_image(image_bgr, points, output_dir, f"{dataset_name}_overlay.png")
        save_replot(df, output_dir, f"{dataset_name}_replot.png")
        dataset_names.append(dataset_name)
        print(f"Saved dataset '{dataset_name}' ({len(df)} points).")

    return dataset_names


def _pick_color_hsv(image_bgr: np.ndarray) -> tuple[int, int, int]:
    color = {"hsv": None}

    def on_mouse(event, x, y, *_):
        if event == cv2.EVENT_LBUTTONDOWN:
            hsv = cv2.cvtColor(np.uint8([[image_bgr[y, x]]]), cv2.COLOR_BGR2HSV)[0, 0]
            color["hsv"] = (int(hsv[0]), int(hsv[1]), int(hsv[2]))

    cv2.namedWindow("Pick Color")
    cv2.setMouseCallback("Pick Color", on_mouse)
    while color["hsv"] is None:
        cv2.imshow("Pick Color", image_bgr)
        if cv2.waitKey(20) & 0xFF == 27:
            break
    cv2.destroyWindow("Pick Color")

    if color["hsv"] is None:
        raise RuntimeError("Color selection aborted.")
    return color["hsv"]


def run_auto_mode(image_bgr: np.ndarray, calibration: GraphCalibration, output_dir: Path) -> tuple[list[str], list[str], float]:
    print("Auto mode: select an ROI in the OpenCV window and press ENTER.")
    roi = cv2.selectROI("Select ROI", image_bgr, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Select ROI")

    print("Click one representative curve pixel to select target color.")
    h, s, v = _pick_color_hsv(image_bgr)
    tol_h = int(_ask_float("Hue tolerance (recommended 8-15): "))
    tol_s = int(_ask_float("Saturation tolerance (recommended 40-80): "))
    tol_v = int(_ask_float("Value tolerance (recommended 40-80): "))

    lower = (max(0, h - tol_h), max(0, s - tol_s), max(0, v - tol_v))
    upper = (min(180, h + tol_h), min(255, s + tol_s), min(255, v + tol_v))

    result = extract_curve_pixels(image_bgr, roi=tuple(map(int, roi)), hsv_lower=lower, hsv_upper=upper)

    names: list[str] = []
    if result.pixel_points.size > 0:
        dataset_name = input("Name for auto-extracted dataset [auto_curve]: ").strip() or "auto_curve"
        points = [(float(x), float(y)) for x, y in result.pixel_points]
        df = convert_pixels_to_dataframe(dataset_name, points, calibration)
        save_curve_csv(df, output_dir, dataset_name)
        save_overlay_image(image_bgr, points, output_dir, f"{dataset_name}_overlay.png")
        save_replot(df, output_dir, f"{dataset_name}_replot.png")
        cv2.imwrite(str(output_dir / f"{dataset_name}_mask.png"), result.mask)
        names.append(dataset_name)

    return names, result.warnings, result.confidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Local scientific graph digitizer")
    parser.add_argument("--image", required=True, help="Path to PNG/JPG/JPEG graph image")
    parser.add_argument("--output", default="sample_output", help="Output directory")
    args = parser.parse_args()

    image_path = validate_image_path(args.image)
    output_dir = ensure_output_dir(args.output)

    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        raise RuntimeError(f"Failed to read image: {image_path}")
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    calibration = calibrate_graph(image_rgb)

    mode = input("Mode [semi/auto] (default semi): ").strip().lower() or "semi"
    warnings: list[str] = []
    confidence = None

    if mode == "auto":
        datasets, warnings, confidence = run_auto_mode(image_bgr, calibration, output_dir)
    else:
        datasets = run_semi_automatic(image_bgr, calibration, output_dir)

    report_path = save_markdown_report(
        output_dir=output_dir,
        image_name=image_path.name,
        mode=mode,
        datasets=datasets,
        warnings=warnings,
        confidence=confidence,
    )
    print(f"Done. Outputs in: {output_dir}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
