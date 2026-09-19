"""Sensor/data-quality gate used before motor diagnosis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class SensorQualityReport:
    status: str
    quality_score: float
    issues: tuple[str, ...]
    action: str

    def to_dict(self) -> dict:
        return asdict(self)


def assess_sensor_window(
    values: np.ndarray,
    *,
    timestamps: Sequence[float] | None = None,
    expected_interval: float | None = None,
    bounds: tuple[float, float] | None = None,
    flatline_std: float = 1e-12,
    drift_scale: float = 5.0,
) -> SensorQualityReport:
    """Return a quality warning; callers should skip motor diagnosis if invalid."""

    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        return SensorQualityReport("invalid", 0.0, ("empty_window",), "sensor_warning")
    issues: list[str] = []
    missing = ~np.isfinite(matrix)
    if missing.any():
        issues.append("missing_or_nonfinite")
    if bounds is not None:
        low, high = map(float, bounds)
        if np.any(matrix[np.isfinite(matrix)] < low) or np.any(matrix[np.isfinite(matrix)] > high):
            issues.append("saturation_or_out_of_range")
    finite = np.where(missing, np.nan, matrix)
    for channel in range(matrix.shape[1]):
        column = finite[:, channel]
        if np.isfinite(column).sum() >= 2 and float(np.nanstd(column)) <= flatline_std:
            issues.append(f"flatline_channel_{channel}")
        valid = column[np.isfinite(column)]
        if len(valid) >= 8:
            half = len(valid) // 2
            scale = max(float(np.nanstd(valid)), np.finfo(float).eps)
            if abs(float(np.mean(valid[-half:]) - np.mean(valid[:half]))) > drift_scale * scale:
                issues.append(f"drift_channel_{channel}")
    if timestamps is not None:
        time_values = np.asarray(timestamps, dtype=float).reshape(-1)
        if len(time_values) != matrix.shape[0] or not np.isfinite(time_values).all():
            issues.append("invalid_timestamps")
        elif np.any(np.diff(time_values) < 0):
            issues.append("out_of_order_timestamps")
        elif expected_interval is not None and len(time_values) > 1:
            gaps = np.diff(time_values)
            if np.any(gaps > float(expected_interval) * 1.5):
                issues.append("timestamp_gap")
    unique = tuple(dict.fromkeys(issues))
    if not unique:
        return SensorQualityReport("valid", 1.0, (), "diagnose_motor")
    severe = any(issue in {"empty_window", "missing_or_nonfinite", "invalid_timestamps", "out_of_order_timestamps"} for issue in unique)
    score = max(0.0, 1.0 - min(1.0, len(unique) / max(1.0, matrix.shape[1] / 2.0)))
    return SensorQualityReport("invalid" if severe else "warning", float(score), unique, "sensor_warning")
