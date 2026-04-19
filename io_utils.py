from __future__ import annotations

from pathlib import Path
from typing import Iterable

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def ensure_output_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_curve_csv(df: pd.DataFrame, output_dir: Path, dataset_name: str) -> Path:
    csv_path = output_dir / f"{dataset_name}.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def save_overlay_image(
    image_bgr: np.ndarray,
    points: Iterable[tuple[float, float]],
    output_dir: Path,
    filename: str,
    color: tuple[int, int, int] = (0, 0, 255),
) -> Path:
    canvas = image_bgr.copy()
    for x, y in points:
        cv2.circle(canvas, (int(round(x)), int(round(y))), 2, color, -1)
    out_path = output_dir / filename
    cv2.imwrite(str(out_path), canvas)
    return out_path


def save_replot(df: pd.DataFrame, output_dir: Path, filename: str) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["x"], df["y"], marker="o", linestyle="-", markersize=2)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out_path = output_dir / filename
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def save_markdown_report(
    output_dir: Path,
    image_name: str,
    mode: str,
    datasets: list[str],
    warnings: list[str],
    confidence: float | None = None,
) -> Path:
    report_path = output_dir / "summary_report.md"
    lines = [
        "# Digitization Summary",
        "",
        f"- Source image: `{image_name}`",
        f"- Mode: `{mode}`",
        f"- Datasets: {', '.join(datasets) if datasets else 'none'}",
    ]
    if confidence is not None:
        lines.append(f"- Auto extraction confidence (heuristic): `{confidence:.2f}`")
    if warnings:
        lines.extend(["", "## Warnings / Notes"] + [f"- {w}" for w in warnings])
    lines.extend(
        [
            "",
            "## Data interpretation note",
            "Digitized points are approximate reconstructions from an image and are not equivalent to original raw experimental data.",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
