"""PolarMap geometry with an explicitly fixed Mahalanobis base.

The Open Set detector used for rejection may be Mahalanobis or k-NN, but the
health-map geometry is intentionally independent of that switch.  It always
fits the shared Ledoit–Wolf Mahalanobis model on the monitor's known train and
calibration splits, so radius and ray direction remain comparable across
method experiments.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.data import HEALTHY
from core.mahalanobis import MahalanobisOpenSetDetector


@dataclass(frozen=True)
class Ray:
    config: str
    direction: np.ndarray
    radius: float
    tau: float


class PolarMap:
    """Health-centred polar geometry, always based on Mahalanobis distance."""

    polarmap_base_method = "mahalanobis"

    def __init__(self, monitor, tau_percentile: float = 5.0, healthy: str = HEALTHY):
        if monitor.scaler is None or not monitor.known:
            raise RuntimeError("OpenSetMonitor must be fitted before constructing PolarMap")
        self.healthy = healthy
        self.tau_percentile = float(tau_percentile)
        self._scaler = monitor.scaler

        X_train, y_train, X_calibration, y_calibration = [], [], [], []
        for config, label in monitor.known.items():
            pool = monitor.pools[config]
            split = monitor.splits[config]
            X_train.append(pool[split.train])
            y_train.append(np.full(len(split.train), label, dtype=int))
            X_calibration.append(pool[split.cal])
            y_calibration.append(np.full(len(split.cal), label, dtype=int))
        X_train_scaled = self._scaler.transform(np.vstack(X_train))
        X_calibration_scaled = self._scaler.transform(np.vstack(X_calibration))
        self._base_detector = MahalanobisOpenSetDetector(
            method="ledoit_wolf", confidence=monitor.confidence, random_state=monitor.seed
        ).fit(
            X_train_scaled,
            np.concatenate(y_train),
            X_calibration_scaled,
            np.concatenate(y_calibration),
        )
        distributions = {
            monitor._label_to_config[int(item.label)]: item
            for item in self._base_detector.distributions_
        }
        if healthy not in distributions:
            raise ValueError(f"healthy configuration {healthy!r} is not known")
        health = distributions[healthy]
        self._mu_h = health.location
        self._W = np.linalg.cholesky(health.precision).T
        self.rays: list[Ray] = []
        for config, distribution in distributions.items():
            if config == healthy:
                continue
            vector = self._whiten_scaled(distribution.location.reshape(1, -1))[0]
            radius = float(np.linalg.norm(vector))
            if radius <= np.finfo(float).eps:
                continue
            direction = vector / radius
            cos_own = self._cosines(monitor.holdout(config), [direction])[:, 0]
            tau = float(np.percentile(cos_own, self.tau_percentile))
            self.rays.append(Ray(config, direction, radius, tau))

    def _whiten_scaled(self, X_scaled: np.ndarray) -> np.ndarray:
        return (np.atleast_2d(X_scaled) - self._mu_h) @ self._W.T

    def whiten_raw(self, X_raw: np.ndarray) -> np.ndarray:
        return self._whiten_scaled(self._scaler.transform(np.atleast_2d(X_raw)))

    def radius(self, X_raw: np.ndarray) -> np.ndarray:
        """Raw Mahalanobis radius from the health distribution."""
        return np.linalg.norm(self.whiten_raw(X_raw), axis=1)

    def _cosines(self, X_raw: np.ndarray, directions: list[np.ndarray]) -> np.ndarray:
        whitened = self.whiten_raw(X_raw)
        norms = np.linalg.norm(whitened, axis=1, keepdims=True)
        unit = whitened / np.maximum(norms, np.finfo(float).eps)
        return unit @ np.column_stack(directions)

    def cosines(self, X_raw: np.ndarray) -> np.ndarray:
        if not self.rays:
            return np.zeros((len(np.atleast_2d(X_raw)), 0))
        return self._cosines(X_raw, [ray.direction for ray in self.rays])

    def analyze(self, X_raw: np.ndarray) -> list[dict]:
        X_raw = np.atleast_2d(X_raw)
        radii = self.radius(X_raw)
        if not self.rays:
            return [
                {
                    "radius": float(radius),
                    "best_ray": None,
                    "best_cos": None,
                    "verdict": "new_direction",
                    "severity": None,
                }
                for radius in radii
            ]
        cos = self.cosines(X_raw)
        output = []
        for index, radius in enumerate(radii):
            ray_index = int(np.argmax(cos[index]))
            ray = self.rays[ray_index]
            best_cos = float(cos[index, ray_index])
            same_ray = best_cos >= ray.tau
            output.append(
                {
                    "radius": float(radius),
                    "best_ray": ray.config,
                    "best_cos": round(best_cos, 4),
                    "verdict": "same_ray" if same_ray else "new_direction",
                    "severity": round(float(radius * best_cos / ray.radius), 4),
                }
            )
        return output

    def ray_cos_matrix(self) -> tuple[list[str], np.ndarray]:
        names = [ray.config for ray in self.rays]
        if not self.rays:
            return names, np.empty((0, 0))
        directions = np.column_stack([ray.direction for ray in self.rays])
        return names, directions.T @ directions

    def summary(self) -> dict:
        return {
            "polarmap_base_method": self.polarmap_base_method,
            "tau_percentile": self.tau_percentile,
            "rays": [
                {"config": ray.config, "radius": round(ray.radius, 6), "tau": round(ray.tau, 6)}
                for ray in self.rays
            ],
        }
