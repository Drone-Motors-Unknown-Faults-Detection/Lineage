"""Scenario-specific Open Set detector comparison on the fixed P1 protocol."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler
from sklearn.svm import OneClassSVM

from core.continual_protocol import build_protocol
from core.openset import create_openset_detector
from experiments.continual_learning import load_records
from health.thresholds import independent_percentile


def _fpr_at_95_tpr(labels: np.ndarray, scores: np.ndarray) -> float | None:
    if len(np.unique(labels)) != 2:
        return None
    fpr, tpr, _ = roc_curve(labels, scores)
    valid = fpr[tpr >= 0.95]
    return float(valid.min()) if len(valid) else None


def _metrics(labels: np.ndarray, scores: np.ndarray, threshold: float, latency: float, calibration_seconds: float) -> dict:
    predictions = scores > threshold
    healthy = labels == 0
    unknown = labels == 1
    return {
        "healthy_false_positive_rate": float(predictions[healthy].mean()) if healthy.any() else None,
        "unknown_recall": float(predictions[unknown].mean()) if unknown.any() else None,
        "auroc": float(roc_auc_score(labels, scores)) if len(np.unique(labels)) == 2 else None,
        "aupr_unknown": float(average_precision_score(labels, scores)) if len(np.unique(labels)) == 2 else None,
        "fpr_at_95_tpr": _fpr_at_95_tpr(labels, scores),
        "inference_latency_ms_per_sample": float(latency * 1000.0 / max(1, len(scores))),
        "calibration_time_seconds": float(calibration_seconds),
    }


def _fit_score(method: str, X_train: np.ndarray, X_cal: np.ndarray, X_test: np.ndarray, seed: int):
    start = time.perf_counter()
    if method == "mahalanobis_ledoit_wolf":
        detector = create_openset_detector("mahalanobis", confidence=0.95, mahalanobis_method="ledoit_wolf").fit(
            X_train, np.zeros(len(X_train), dtype=int), X_cal, np.zeros(len(X_cal), dtype=int)
        )
        cal_scores = detector.score_samples(X_cal)
        test_start = time.perf_counter()
        test_scores = detector.score_samples(X_test)
    elif method == "knn":
        detector = create_openset_detector("knn", confidence=0.95, knn_neighbors=5).fit(
            X_train, np.zeros(len(X_train), dtype=int), X_cal, np.zeros(len(X_cal), dtype=int)
        )
        cal_scores = detector.score_samples(X_cal)
        test_start = time.perf_counter()
        test_scores = detector.score_samples(X_test)
    elif method == "oc_svm":
        detector = OneClassSVM(nu=0.05, gamma="scale").fit(X_train)
        cal_scores = -detector.decision_function(X_cal)
        test_start = time.perf_counter()
        test_scores = -detector.decision_function(X_test)
    elif method == "isolation_forest":
        detector = IsolationForest(n_estimators=200, contamination="auto", random_state=seed, n_jobs=1).fit(X_train)
        cal_scores = -detector.score_samples(X_cal)
        test_start = time.perf_counter()
        test_scores = -detector.score_samples(X_test)
    elif method == "lof":
        detector = LocalOutlierFactor(n_neighbors=min(20, len(X_train) - 1), novelty=True).fit(X_train)
        cal_scores = -detector.score_samples(X_cal)
        test_start = time.perf_counter()
        test_scores = -detector.score_samples(X_test)
    elif method == "pca_reconstruction":
        detector = PCA(n_components=0.95, svd_solver="full", random_state=seed).fit(X_train)
        cal_projection = detector.inverse_transform(detector.transform(X_cal))
        cal_scores = np.mean((X_cal - cal_projection) ** 2, axis=1)
        test_start = time.perf_counter()
        test_projection = detector.inverse_transform(detector.transform(X_test))
        test_scores = np.mean((X_test - test_projection) ** 2, axis=1)
    else:
        raise ValueError(method)
    calibration_seconds = time.perf_counter() - start
    threshold = float(independent_percentile(cal_scores, quantile=0.95, scope="healthy_calibration").threshold)
    latency = time.perf_counter() - test_start
    return np.asarray(test_scores, dtype=float), threshold, latency, calibration_seconds


AVAILABLE_METHODS = (
    "mahalanobis_ledoit_wolf",
    "knn",
    "oc_svm",
    "isolation_forest",
    "lof",
    "pca_reconstruction",
)


def run(data_root: Path | str, output_root: Path | str, *, seeds=(42, 123, 2026)) -> dict:
    data_path = Path(data_root).expanduser().resolve()
    output_path = Path(output_root).expanduser().resolve()
    protocol = build_protocol(data_path, output_path / "protocol", seed=42)
    train = load_records(protocol, data_path, "initial_known_train")
    calibration = load_records(protocol, data_path, "healthy_calibration")
    test = load_records(protocol, data_path, "immutable_test")
    scaler = RobustScaler().fit(np.asarray([item["features"] for item in train]))
    X_train = scaler.transform(np.asarray([item["features"] for item in train]))
    X_cal = scaler.transform(np.asarray([item["features"] for item in calibration]))
    X_test = scaler.transform(np.asarray([item["features"] for item in test]))
    labels = np.asarray([int(item["condition"] != "8screws") for item in test], dtype=int)
    rows: list[dict] = []
    for seed in seeds:
        for method in AVAILABLE_METHODS:
            scores, threshold, latency, calibration_seconds = _fit_score(method, X_train, X_cal, X_test, int(seed))
            rows.append(
                {
                    "scenario": "healthy_only_cold_start",
                    "method": method,
                    "feature_type": "raw_105d",
                    "seed": int(seed),
                    "status": "completed",
                    "protocol_fingerprint": protocol["protocol_fingerprint"],
                    "calibration": "independent_95_percentile_healthy_only",
                    "threshold": threshold,
                    "metrics": _metrics(labels, scores, threshold, latency, calibration_seconds),
                }
            )
        rows.extend(
            {
                "scenario": "existing_multiclass_logits",
                "method": method,
                "feature_type": "logits",
                "seed": int(seed),
                "status": "not_applicable",
                "reason": "Lineage cold-start pipeline has no multiclass logits/activation layer; MSP, Energy and OpenMax cannot be fairly evaluated",
            }
            for method in ("msp", "energy", "openmax")
        )
        rows.append(
            {
                "scenario": "healthy_only_cold_start",
                "method": "deep_svdd",
                "feature_type": "neural_embedding",
                "seed": int(seed),
                "status": "blocked",
                "reason": "PyTorch/TensorFlow is not installed in the CPU Lineage environment; no neural representation or hyperparameter policy exists",
                "source": "Ruff et al., Deep One-Class Classification, PMLR 80 (2018)",
            }
        )
    summary = {
        "schema_version": 1,
        "experiment": "detector_comparison",
        "protocol_fingerprint": protocol["protocol_fingerprint"],
        "seeds": [int(seed) for seed in seeds],
        "feature_policy": "all completed rows use the same scaled raw 105D feature representation",
        "rows": rows,
        "not_claimed": [
            "Deep SVDD is not compared numerically without a neural feature policy and dependency.",
            "MSP/Energy/OpenMax are not compared because no suitable multiclass logits exist.",
            "This healthy-only experiment does not answer multimodal class-distribution questions.",
        ],
    }
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(args.data_root, args.output_root)
    print(json.dumps({"rows": len(summary["rows"]), "completed": sum(row["status"] == "completed" for row in summary["rows"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
