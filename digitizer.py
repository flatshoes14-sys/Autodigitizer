from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import pandas as pd

from calibration import GraphCalibration


@dataclass
class CurveDataset:
    name: str
    pixel_points: List[Tuple[float, float]] = field(default_factory=list)

    def to_dataframe(self, calibration: GraphCalibration) -> pd.DataFrame:
        data_points = [calibration.pixel_to_data(pt) for pt in self.pixel_points]
        df = pd.DataFrame(data_points, columns=["x", "y"])
        df.insert(0, "dataset", self.name)
        return df.sort_values(by="x", kind="stable").reset_index(drop=True)


def convert_pixels_to_dataframe(
    name: str,
    pixel_points: List[Tuple[float, float]],
    calibration: GraphCalibration,
) -> pd.DataFrame:
    return CurveDataset(name=name, pixel_points=pixel_points).to_dataframe(calibration)
