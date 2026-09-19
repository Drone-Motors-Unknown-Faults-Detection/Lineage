"""Independent and event-level calibration policies.

All fit functions in this module accept calibration scores explicitly.  They
do not know about test labels and therefore cannot silently tune a threshold
on the immutable test set.  The conformal implementation uses the finite
sample rank p-value ``(1 + # {calibration score >= score}) / (n + 1)`` for a
higher-is-more-anomalous score, with inclusive ties for deterministic output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np


def _scores(values: Sequence[float] | np.ndarray, name: str = "scores") -> np.ndarray:
    array = np.asarray(values, dtype=float).reshape(-1)
    if array.size == 0:
        raise ValueError(f"{name} must contain at least one value")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite values")
    return array


@dataclass(frozen=True)
class CalibrationResult:
    method: str
    threshold: float | None
    alpha: float | None
    quantile: float | None
    n_calibration: int
    scope: str
    calibration_version: str

    def to_dict(self) -> dict:
        return asdict(self)


def independent_percentile(
    calibration_scores: Sequence[float] | np.ndarray,
    *,
    quantile: float = 0.95,
    scope: str = "global",
    calibration_version: str = "percentile-v1",
) -> CalibrationResult:
    """Fit a threshold on an independent healthy calibration population."""

    scores = _scores(calibration_scores, "calibration_scores")
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be in (0, 1)")
    return CalibrationResult(
        method="independent_percentile",
        threshold=float(np.quantile(scores, quantile)),
        alpha=float(1.0 - quantile),
        quantile=float(quantile),
        n_calibration=int(scores.size),
        scope=str(scope),
        calibration_version=str(calibration_version),
    )


@dataclass(frozen=True)
class ConformalCalibrator:
    calibration_scores: tuple[float, ...]
    alpha: float = 0.05
    scope: str = "global"
    calibration_version: str = "conformal-v1"

    def __post_init__(self) -> None:
        if not self.calibration_scores:
            raise ValueError("calibration_scores must not be empty")
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        if not np.isfinite(np.asarray(self.calibration_scores, dtype=float)).all():
            raise ValueError("calibration_scores must be finite")

    @classmethod
    def fit(
        cls,
        calibration_scores: Sequence[float] | np.ndarray,
        *,
        alpha: float = 0.05,
        scope: str = "global",
        calibration_version: str = "conformal-v1",
    ) -> "ConformalCalibrator":
        scores = _scores(calibration_scores, "calibration_scores")
        return cls(tuple(float(value) for value in scores), float(alpha), str(scope), str(calibration_version))

    @property
    def result(self) -> CalibrationResult:
        return CalibrationResult(
            method="conformal",
            threshold=None,
            alpha=self.alpha,
            quantile=None,
            n_calibration=len(self.calibration_scores),
            scope=self.scope,
            calibration_version=self.calibration_version,
        )

    def p_values(self, scores: Sequence[float] | np.ndarray) -> np.ndarray:
        values = _scores(scores)
        calibration = np.asarray(self.calibration_scores, dtype=float)
        # Inclusive ties are conservative and reproducible.  The +1 finite-
        # sample correction prevents zero p-values.
        return np.asarray(
            [(1.0 + float(np.count_nonzero(calibration >= value))) / (len(calibration) + 1.0) for value in values],
            dtype=float,
        )

    def is_anomaly(self, scores: Sequence[float] | np.ndarray) -> np.ndarray:
        return self.p_values(scores) <= self.alpha


class ConditionAwareCalibrator:
    """Condition-specific percentile thresholds with deterministic fallback.

    Conditions are hierarchical strings separated by ``|``.  For example,
    ``T1|8000rpm|nominal`` falls back to ``T1|8000rpm`` and then ``global``.
    A scope is only used when it has ``min_samples`` calibration rows.
    """

    def __init__(
        self,
        thresholds: Mapping[str, CalibrationResult],
        *,
        quantile: float,
        min_samples: int,
        calibration_version: str,
    ) -> None:
        self.thresholds = dict(thresholds)
        self.quantile = float(quantile)
        self.min_samples = int(min_samples)
        self.calibration_version = str(calibration_version)

    @classmethod
    def fit(
        cls,
        scores_by_condition: Mapping[str, Sequence[float] | np.ndarray],
        *,
        quantile: float = 0.95,
        min_samples: int = 20,
        calibration_version: str = "condition-percentile-v1",
    ) -> "ConditionAwareCalibrator":
        if min_samples < 1:
            raise ValueError("min_samples must be positive")
        if not scores_by_condition:
            raise ValueError("scores_by_condition must not be empty")
        flattened = np.concatenate([_scores(values, str(key)) for key, values in scores_by_condition.items()])
        results: dict[str, CalibrationResult] = {
            "global": independent_percentile(
                flattened,
                quantile=quantile,
                scope="global",
                calibration_version=calibration_version,
            )
        }
        for condition, values in scores_by_condition.items():
            scores = _scores(values, str(condition))
            if len(scores) >= min_samples:
                results[str(condition)] = independent_percentile(
                    scores,
                    quantile=quantile,
                    scope=str(condition),
                    calibration_version=calibration_version,
                )
        return cls(results, quantile=quantile, min_samples=min_samples, calibration_version=calibration_version)

    @staticmethod
    def _fallback_chain(condition: str) -> list[str]:
        parts = [part for part in str(condition).split("|") if part]
        return ["|".join(parts[:index]) for index in range(len(parts), 0, -1)] + ["global"]

    def resolve(self, condition: str) -> CalibrationResult:
        for candidate in self._fallback_chain(condition):
            if candidate in self.thresholds:
                result = self.thresholds[candidate]
                return CalibrationResult(
                    method="condition_specific_percentile" if candidate != "global" else "global_fallback_percentile",
                    threshold=result.threshold,
                    alpha=result.alpha,
                    quantile=result.quantile,
                    n_calibration=result.n_calibration,
                    scope=candidate,
                    calibration_version=self.calibration_version,
                )
        raise RuntimeError("global calibration threshold is missing")

    def transform(
        self,
        scores: Sequence[float] | np.ndarray,
        conditions: Sequence[str],
    ) -> tuple[np.ndarray, tuple[str, ...]]:
        values = _scores(scores)
        if len(values) != len(conditions):
            raise ValueError("scores and conditions must have equal length")
        resolved = [self.resolve(condition) for condition in conditions]
        return np.asarray([item.threshold for item in resolved], dtype=float), tuple(item.scope for item in resolved)


@dataclass(frozen=True)
class AlarmPolicy:
    kind: str = "single"
    consecutive: int = 1
    window: int = 5
    required: int = 3
    ratio: float = 0.6
    enter_threshold: float | None = None
    exit_threshold: float | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"single", "consecutive", "k_of_n", "ratio", "hysteresis"}:
            raise ValueError(f"unsupported alarm policy: {self.kind}")
        if self.consecutive < 1 or self.window < 1 or self.required < 1:
            raise ValueError("alarm window parameters must be positive")
        if self.required > self.window:
            raise ValueError("required cannot exceed window")
        if not 0.0 < self.ratio <= 1.0:
            raise ValueError("ratio must be in (0, 1]")
        if self.kind == "hysteresis":
            if self.enter_threshold is None or self.exit_threshold is None:
                raise ValueError("hysteresis needs enter_threshold and exit_threshold")
            if self.exit_threshold >= self.enter_threshold:
                raise ValueError("exit_threshold must be lower than enter_threshold")


def apply_alarm_policy(scores: Sequence[float] | np.ndarray, threshold: float, policy: AlarmPolicy) -> np.ndarray:
    """Convert higher-is-worse scores to an event alarm series."""

    values = _scores(scores)
    if policy.kind == "hysteresis":
        alarm = np.zeros(len(values), dtype=bool)
        active = False
        for index, value in enumerate(values):
            if not active and value > float(policy.enter_threshold):
                active = True
            elif active and value <= float(policy.exit_threshold):
                active = False
            alarm[index] = active
        return alarm
    point = values > float(threshold)
    if policy.kind == "single":
        return point
    output = np.zeros(len(values), dtype=bool)
    if policy.kind == "consecutive":
        streak = 0
        for index, value in enumerate(point):
            streak = streak + 1 if value else 0
            output[index] = streak >= policy.consecutive
        return output
    for index in range(policy.window - 1, len(values)):
        window = point[index - policy.window + 1 : index + 1]
        count = int(window.sum())
        if policy.kind == "k_of_n":
            output[index] = count >= policy.required
        else:
            output[index] = count / policy.window >= policy.ratio
    return output
