from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple
import math

Scale = Literal["linear", "log"]


@dataclass
class AxisReference:
    pixel: float
    value: float


@dataclass
class AxisCalibration:
    """Maps a pixel axis to a data axis using two-point calibration."""

    p1: AxisReference
    p2: AxisReference
    scale: Scale = "linear"

    def __post_init__(self) -> None:
        if self.p1.pixel == self.p2.pixel:
            raise ValueError("Axis calibration requires two distinct pixel points.")
        if self.scale == "log":
            if self.p1.value <= 0 or self.p2.value <= 0:
                raise ValueError("Log-scale axis values must be > 0.")

    def _to_axis_space(self, value: float) -> float:
        if self.scale == "linear":
            return value
        if value <= 0:
            raise ValueError("Cannot map non-positive value on log scale.")
        return math.log10(value)

    def _from_axis_space(self, value: float) -> float:
        if self.scale == "linear":
            return value
        return 10 ** value

    def pixel_to_value(self, pixel: float) -> float:
        v1 = self._to_axis_space(self.p1.value)
        v2 = self._to_axis_space(self.p2.value)
        ratio = (pixel - self.p1.pixel) / (self.p2.pixel - self.p1.pixel)
        mapped = v1 + ratio * (v2 - v1)
        return self._from_axis_space(mapped)

    def value_to_pixel(self, value: float) -> float:
        v1 = self._to_axis_space(self.p1.value)
        v2 = self._to_axis_space(self.p2.value)
        v = self._to_axis_space(value)
        ratio = (v - v1) / (v2 - v1)
        return self.p1.pixel + ratio * (self.p2.pixel - self.p1.pixel)


@dataclass
class GraphCalibration:
    """Full 2D graph calibration for converting image pixels to data coordinates."""

    x_axis: AxisCalibration
    y_axis: AxisCalibration

    def pixel_to_data(self, pixel_xy: Tuple[float, float]) -> Tuple[float, float]:
        x_px, y_px = pixel_xy
        return self.x_axis.pixel_to_value(x_px), self.y_axis.pixel_to_value(y_px)

    def data_to_pixel(self, data_xy: Tuple[float, float]) -> Tuple[float, float]:
        x_val, y_val = data_xy
        return self.x_axis.value_to_pixel(x_val), self.y_axis.value_to_pixel(y_val)
