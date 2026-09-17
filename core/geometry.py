"""極座標健康地圖（實驗四核心）：方向 = 故障類型、半徑 = 嚴重度。

幾何全部定義在**健康類的白化空間**：以健康類 Ledoit–Wolf precision P_H 的
Cholesky 分解取白化矩陣 W = chol(P_H)^T，對任意樣本（已標準化空間）x：

    z(x) = W (x − μ_H)            白化座標（健康中心為原點）
    r(x) = ‖z(x)‖                 半徑 = 到健康分布的馬氏距離（嚴重度的原始量）
    u_c  = z(μ_c) / ‖z(μ_c)‖      已知故障類 c 的「射線」方向
    cos_c(x) = ⟨z/‖z‖, u_c⟩       方向相似度

三分判定（疊在現行「已知/未知」之上）：
    - same_ray：max_c cos_c ≥ τ_c（該類 holdout cos 的低百分位校準）
      → 疑似已知故障 c 的惡化/變體；嚴重度 severity = r·cos_c / ‖z(μ_c)‖
      （= 沿射線投影長相對類中心半徑；類中心處 ≈ 1、健康 ≈ 0、更嚴重 > 1）
    - new_direction：所有 cos 皆低 → 走新類發現（隔離區）
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.data import HEALTHY


@dataclass(frozen=True)
class Ray:
    config: str
    direction: np.ndarray  # 白化空間單位向量
    radius: float          # 類中心到健康中心的白化距離
    tau: float             # same-ray 判定門檻（該類自身 holdout cos 的低百分位）


class PolarMap:
    """由已擬合的 OpenSetMonitor 建立極座標幾何。

    monitor 需已 fit（任意已知類數）；healthy 之外的每個已知類各成一條射線。
    僅健康一類時沒有射線：所有異常樣本判 new_direction、severity 為 None。
    """

    def __init__(self, monitor, tau_percentile: float = 5.0, healthy: str = HEALTHY):
        self.healthy = healthy
        self.tau_percentile = tau_percentile
        dist = {monitor._label_to_config[int(d.label)]: d
                for d in monitor.detector.distributions_}
        h = dist[healthy]
        self._scaler = monitor.scaler
        self._mu_h = h.location
        # W = chol(P)^T：使 ‖W(x−μ)‖ 恰為馬氏距離
        self._W = np.linalg.cholesky(h.precision).T

        self.rays: list[Ray] = []
        for config, d in dist.items():
            if config == healthy:
                continue
            v = self._whiten(d.location.reshape(1, -1))[0]
            radius = float(np.linalg.norm(v))
            direction = v / radius
            cos_own = self._cosines(monitor.holdout(config), [direction])[:, 0]
            tau = float(np.percentile(cos_own, tau_percentile))
            self.rays.append(Ray(config, direction, radius, tau))

    # -- 基本轉換 --------------------------------------------------------------

    def _whiten(self, X_scaled: np.ndarray) -> np.ndarray:
        return (np.atleast_2d(X_scaled) - self._mu_h) @ self._W.T

    def whiten_raw(self, X_raw: np.ndarray) -> np.ndarray:
        return self._whiten(self._scaler.transform(np.atleast_2d(X_raw)))

    def radius(self, X_raw: np.ndarray) -> np.ndarray:
        """到健康分布的馬氏距離（未以任何閾值正規化）。"""
        return np.linalg.norm(self.whiten_raw(X_raw), axis=1)

    def _cosines(self, X_raw: np.ndarray, directions) -> np.ndarray:
        Z = self.whiten_raw(X_raw)
        norms = np.linalg.norm(Z, axis=1, keepdims=True)
        unit = Z / np.maximum(norms, np.finfo(float).eps)
        return unit @ np.column_stack([d for d in directions])

    def cosines(self, X_raw: np.ndarray) -> np.ndarray:
        """n × n_rays 的方向相似度矩陣（射線順序同 self.rays）。"""
        if not self.rays:
            return np.zeros((len(np.atleast_2d(X_raw)), 0))
        return self._cosines(X_raw, [r.direction for r in self.rays])

    # -- 判定 ------------------------------------------------------------------

    def analyze(self, X_raw: np.ndarray) -> list[dict]:
        """逐樣本極座標判讀（不含「是否異常」——那由 monitor 的開集分數決定）。

        回傳欄位：radius、best_ray（config 或 None）、best_cos、
        verdict（"same_ray"/"new_direction"）、severity（無射線時為 None）。
        """
        X_raw = np.atleast_2d(X_raw)
        radii = self.radius(X_raw)
        if not self.rays:
            return [
                {"radius": float(r), "best_ray": None, "best_cos": None,
                 "verdict": "new_direction", "severity": None}
                for r in radii
            ]
        cos = self.cosines(X_raw)
        out = []
        for i, r in enumerate(radii):
            j = int(np.argmax(cos[i]))
            ray = self.rays[j]
            best_cos = float(cos[i, j])
            same = best_cos >= ray.tau
            out.append({
                "radius": float(r),
                "best_ray": ray.config,
                "best_cos": round(best_cos, 4),
                "verdict": "same_ray" if same else "new_direction",
                "severity": round(float(r * best_cos / ray.radius), 4),
            })
        return out

    def ray_cos_matrix(self) -> tuple[list[str], np.ndarray]:
        """射線兩兩之間的 cos（星狀假設的直接量測）。"""
        names = [r.config for r in self.rays]
        D = np.column_stack([r.direction for r in self.rays])
        return names, D.T @ D

    def summary(self) -> dict:
        return {
            "tau_percentile": self.tau_percentile,
            "rays": [
                {"config": r.config, "radius": round(r.radius, 2), "tau": round(r.tau, 4)}
                for r in self.rays
            ],
        }
