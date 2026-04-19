import math

import pytest

from calibration import AxisCalibration, AxisReference, GraphCalibration


def test_linear_linear_pixel_to_data():
    x_axis = AxisCalibration(AxisReference(100, 0), AxisReference(300, 10), scale="linear")
    y_axis = AxisCalibration(AxisReference(400, 0), AxisReference(200, 20), scale="linear")
    cal = GraphCalibration(x_axis=x_axis, y_axis=y_axis)

    x, y = cal.pixel_to_data((200, 300))
    assert x == pytest.approx(5.0)
    assert y == pytest.approx(10.0)


def test_log_axis_mapping():
    x_axis = AxisCalibration(AxisReference(0, 1), AxisReference(100, 100), scale="log")
    mid = x_axis.pixel_to_value(50)
    assert mid == pytest.approx(10.0)


def test_reversed_axis_supported():
    x_axis = AxisCalibration(AxisReference(300, 0), AxisReference(100, 10), scale="linear")
    assert x_axis.pixel_to_value(200) == pytest.approx(5.0)


def test_log_scale_requires_positive_values():
    with pytest.raises(ValueError):
        AxisCalibration(AxisReference(0, -1), AxisReference(10, 10), scale="log")


def test_round_trip_data_pixel_data():
    x_axis = AxisCalibration(AxisReference(20, 0), AxisReference(220, 100), scale="linear")
    y_axis = AxisCalibration(AxisReference(300, 1e-2), AxisReference(100, 1e2), scale="log")
    cal = GraphCalibration(x_axis=x_axis, y_axis=y_axis)

    data = (25.0, 1.0)
    px = cal.data_to_pixel(data)
    data2 = cal.pixel_to_data(px)
    assert math.isclose(data[0], data2[0], rel_tol=1e-10)
    assert math.isclose(data[1], data2[1], rel_tol=1e-10)
