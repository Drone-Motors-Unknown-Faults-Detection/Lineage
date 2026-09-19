"""Formal-data calibration and event-alarm ablation.

The detector is fitted only on ``initial_known_train`` and its calibration
population.  Validation/test labels are read after fitting solely for offline
metrics.  This script intentionally reports the covariance and threshold
effects as separate rows; it must not be read as evidence that Ledoit--Wolf
alone explains a legacy-versus-independent difference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import RobustScaler

from core.continual_protocol import build_protocol
from core.openset import create_openset_detector
from health.evaluation import evaluate_alarm_series
from health.thresholds import AlarmPolicy, ConformalCalibrator, independent_percentile


METHODS = (
    [("legacy", "legacy_self_threshold", None)]
    + [(covariance, "independent_percentile", quantile) for covariance in ("legacy", "ledoit_wolf") for quantile in (0.90, 0.95, 0.975, 0.99)]
    + [(covariance, "conformal", alpha) for covariance in ("legacy", "ledoit_wolf") for alpha in (0.01, 0.05, 0.10)]
)


def _commit_sha() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _load_split(manifest: dict, data_root: Path, split: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    records = [item for item in manifest["records"] if item["split"] == split]
    if not records:
        raise ValueError(f"protocol has no records for {split}")
    grouped: dict[str, list[dict]] = {}
    for record in records:
        grouped.setdefault(record["source_file"], []).append(record)
    features: list[np.ndarray] = []
    labels: list[int] = []
    conditions: list[str] = []
    for source_file, items in sorted(grouped.items()):
        frame = pd.read_csv(data_root / Path(source_file))
        numeric = frame.select_dtypes(include="number").to_numpy(dtype=float)
        for item in sorted(items, key=lambda value: value["row_index"]):
            features.append(numeric[item["row_index"]])
            labels.append(int(item["label"] != 0))
            conditions.append(f"{item['motor_id']}|{item['rpm']}|{item['condition']}")
    return np.asarray(features, dtype=float), np.asarray(labels, dtype=int), conditions


def _metrics(scores: np.ndarray, labels: np.ndarray, alarm: np.ndarray) -> dict:
    healthy = labels == 0
    unknown = labels == 1
    return {
        "n_windows": int(len(scores)),
        "healthy_false_positive_rate": float(alarm[healthy].mean()) if healthy.any() else None,
        "unknown_recall": float(alarm[unknown].mean()) if unknown.any() else None,
        "auroc": float(roc_auc_score(labels, scores)) if len(np.unique(labels)) == 2 else None,
        "aupr_unknown": float(average_precision_score(labels, scores)) if len(np.unique(labels)) == 2 else None,
    }


def run(data_root: Path | str, output_root: Path | str, *, seeds: Iterable[int] = (42, 123, 2026)) -> dict:
    data_path = Path(data_root).expanduser().resolve()
    output_path = Path(output_root).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for seed in seeds:
        protocol_dir = output_path / f"protocol_seed_{seed}"
        manifest = build_protocol(data_path, protocol_dir, seed=int(seed))
        X_train, y_train, _ = _load_split(manifest, data_path, "initial_known_train")
        X_cal, y_cal, _ = _load_split(manifest, data_path, "healthy_calibration")
        X_val, y_val, val_conditions = _load_split(manifest, data_path, "validation")
        X_test, y_test, test_conditions = _load_split(manifest, data_path, "immutable_test")
        # Validation and immutable test are never passed into fit/calibration.
        X_eval = np.vstack([X_val, X_test])
        y_eval = np.concatenate([y_val, y_test])
        conditions = val_conditions + test_conditions
        timestamps = list(range(len(X_eval)))
        scaler = RobustScaler().fit(X_train)
        train_scaled = scaler.transform(X_train)
        cal_scaled = scaler.transform(X_cal)
        eval_scaled = scaler.transform(X_eval)
        for covariance_method, calibration_method, calibration_parameter in METHODS:
            detector = create_openset_detector(
                "mahalanobis",
                confidence=0.95,
                mahalanobis_method=covariance_method,  # type: ignore[arg-type]
            ).fit(train_scaled, np.zeros(len(train_scaled), dtype=int), cal_scaled, np.zeros(len(cal_scaled), dtype=int))
            scores_cal = np.asarray(detector.score_samples(cal_scaled), dtype=float)
            scores_eval = np.asarray(detector.score_samples(eval_scaled), dtype=float)
            if calibration_method == "legacy_self_threshold":
                threshold = 1.0
                alarm = scores_eval > threshold
                calibration_version = "legacy-self-threshold"
                event_scores = scores_eval
                event_threshold = threshold
            elif calibration_method == "independent_percentile":
                fitted = independent_percentile(scores_cal, quantile=float(calibration_parameter), scope="healthy_calibration")
                threshold = float(fitted.threshold)
                alarm = scores_eval > threshold
                calibration_version = f"percentile-q{float(calibration_parameter):g}"
                event_scores = scores_eval
                event_threshold = threshold
            else:
                fitted_conformal = ConformalCalibrator.fit(scores_cal, alpha=float(calibration_parameter), scope="healthy_calibration")
                p_values = fitted_conformal.p_values(scores_eval)
                threshold = float(fitted_conformal.alpha)
                alarm = p_values <= fitted_conformal.alpha
                calibration_version = fitted_conformal.calibration_version
                event_scores = 1.0 - p_values
                event_threshold = 1.0 - fitted_conformal.alpha
            metrics = _metrics(scores_eval, y_eval, alarm)
            event = evaluate_alarm_series(
                event_scores,
                y_eval,
                timestamps,
                threshold=event_threshold,
                policy=AlarmPolicy(kind="single"),
            )
            rows.append(
                {
                    "seed": int(seed),
                    "covariance": covariance_method,
                    "calibration": calibration_method,
                    "calibration_parameter": calibration_parameter,
                    "calibration_version": calibration_version,
                    "protocol_fingerprint": manifest["protocol_fingerprint"],
                    "n_train": int(len(X_train)),
                    "n_calibration": int(len(X_cal)),
                    "n_validation": int(len(X_val)),
                    "n_immutable_test": int(len(X_test)),
                    "metrics": metrics,
                    "event_metrics": {
                        key: event[key]
                        for key in (
                            "false_alarms_per_hour",
                            "false_alarm_events",
                            "event_unknown_recall",
                            "detection_delay_seconds_mean",
                            "alarm_flapping_count",
                        )
                    },
                    "threshold": threshold,
                }
            )
    summary = {
        "schema_version": 1,
        "experiment": "calibration_ablation",
        "commit": _commit_sha(),
        "data_root_label": "data/formal_local",
        "rows": rows,
        "methods": [
            {"covariance": covariance, "calibration": calibration, "parameter": parameter}
            for covariance, calibration, parameter in METHODS
        ],
        "test_policy": "validation and immutable_test labels are evaluation-only",
    }
    payload = json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    summary["result_fingerprint"] = hashlib.sha256(payload).hexdigest()
    (output_path / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(args.data_root, args.output_root)
    print(json.dumps({"rows": len(summary["rows"]), "result_fingerprint": summary["result_fingerprint"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
