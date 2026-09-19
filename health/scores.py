"""Independent health, unknownness and direction-familiarity scores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from sklearn.preprocessing import RobustScaler

from core.mahalanobis import MahalanobisOpenSetDetector


def _matrix(value: np.ndarray, name: str) -> np.ndarray:
    matrix = np.asarray(value, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError(f"{name} must be a non-empty two-dimensional matrix")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{name} must contain finite values")
    return matrix


def bounded_unknown_score(openset_score: np.ndarray | float) -> np.ndarray:
    values = np.asarray(openset_score, dtype=float)
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("openset_score must be finite and non-negative")
    return np.clip(values / (1.0 + values), 0.0, 1.0)


@dataclass
class FixedHealthReference:
    """Immutable healthy-only Mahalanobis reference.

    A new known fault class may change the Open Set detector, but it does not
    mutate this object.  ``version`` changes only when a caller explicitly
    fits a replacement reference.
    """

    scaler: RobustScaler
    detector: MahalanobisOpenSetDetector
    version: str = "healthy-reference-v1"

    @classmethod
    def fit(
        cls,
        X_train_healthy: np.ndarray,
        X_calibration_healthy: np.ndarray,
        *,
        version: str = "healthy-reference-v1",
    ) -> "FixedHealthReference":
        train = _matrix(X_train_healthy, "X_train_healthy")
        calibration = _matrix(X_calibration_healthy, "X_calibration_healthy")
        if train.shape[1] != calibration.shape[1]:
            raise ValueError("healthy train/calibration dimensions must match")
        scaler = RobustScaler().fit(train)
        detector = MahalanobisOpenSetDetector(method="ledoit_wolf", confidence=0.95).fit(
            scaler.transform(train),
            np.zeros(len(train), dtype=int),
            scaler.transform(calibration),
            np.zeros(len(calibration), dtype=int),
        )
        return cls(scaler=scaler, detector=detector, version=str(version))

    def raw_deviation(self, X_raw: np.ndarray) -> np.ndarray:
        matrix = _matrix(X_raw, "X_raw")
        return np.asarray(self.detector.score_samples(self.scaler.transform(matrix)), dtype=float)

    def deviation(self, X_raw: np.ndarray) -> np.ndarray:
        return bounded_unknown_score(self.raw_deviation(X_raw))

    def metadata(self) -> dict:
        return {
            "health_reference_version": self.version,
            "estimator": "Mahalanobis Ledoit-Wolf",
            "score_direction": "higher_is_worse",
            "mutable": False,
        }


@dataclass
class DirectionFamiliarity:
    """Fixed healthy-whitened directions for known fault classes."""

    directions: dict[int, np.ndarray]
    label_names: Mapping[int, str]
    reference_version: str

    @classmethod
    def fit(
        cls,
        X_train: np.ndarray,
        y_train: np.ndarray,
        reference: FixedHealthReference,
        *,
        label_names: Mapping[int, str] | None = None,
    ) -> "DirectionFamiliarity":
        matrix = _matrix(X_train, "X_train")
        labels = np.asarray(y_train)
        if labels.ndim != 1 or len(labels) != len(matrix):
            raise ValueError("y_train must align with X_train")
        health = reference.detector.distributions_[0]
        whiten = np.linalg.cholesky(health.precision).T
        scaled = reference.scaler.transform(matrix)
        vectors = (scaled - health.location) @ whiten.T
        directions: dict[int, np.ndarray] = {}
        for raw_label in np.unique(labels):
            label = int(raw_label)
            if label == 0:
                continue
            vector = vectors[labels == raw_label].mean(axis=0)
            norm = float(np.linalg.norm(vector))
            if norm > np.finfo(float).eps:
                directions[label] = vector / norm
        names = {int(key): str(value) for key, value in (label_names or {}).items()}
        return cls(directions=directions, label_names=names, reference_version=reference.version)

    def score(self, X_raw: np.ndarray, reference: FixedHealthReference) -> tuple[np.ndarray, list[str | None]]:
        matrix = _matrix(X_raw, "X_raw")
        health = reference.detector.distributions_[0]
        whiten = np.linalg.cholesky(health.precision).T
        vectors = (reference.scaler.transform(matrix) - health.location) @ whiten.T
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        unit = vectors / np.maximum(norms, np.finfo(float).eps)
        if not self.directions:
            return np.zeros(len(matrix), dtype=float), [None] * len(matrix)
        labels = sorted(self.directions)
        cosine = np.column_stack([unit @ self.directions[label] for label in labels])
        indices = np.argmax(cosine, axis=1)
        familiarity = np.clip((cosine[np.arange(len(matrix)), indices] + 1.0) / 2.0, 0.0, 1.0)
        names = [self.label_names.get(labels[index], str(labels[index])) for index in indices]
        return familiarity, names

    def metadata(self) -> dict:
        return {
            "direction_reference_version": self.reference_version,
            "n_known_directions": len(self.directions),
            "geometry": "healthy-whitened Mahalanobis direction cosine",
        }
