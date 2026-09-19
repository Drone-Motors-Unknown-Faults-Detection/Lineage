"""Formal regression for independent health/unknown/direction scores."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from core.continual_protocol import build_protocol
from health.index import CalibratedHealthIndex


def _load_records(manifest: dict, data_root: Path, split: str, *, class_labels: dict[str, int] | None = None):
    records = [item for item in manifest["records"] if item["split"] == split]
    grouped: dict[str, list[dict]] = {}
    for item in records:
        grouped.setdefault(item["source_file"], []).append(item)
    features, labels, conditions = [], [], []
    mapping = class_labels or {}
    for source_file, items in sorted(grouped.items()):
        frame = pd.read_csv(data_root / Path(source_file))
        values = frame.select_dtypes(include="number").to_numpy(dtype=float)
        for item in sorted(items, key=lambda value: value["row_index"]):
            features.append(values[item["row_index"]])
            condition = str(item["condition"])
            labels.append(mapping.get(condition, 0 if condition == "8screws" else 1))
            conditions.append(condition)
    return np.asarray(features), np.asarray(labels, dtype=int), conditions


def run(data_root: Path | str, output_root: Path | str) -> dict:
    data_path = Path(data_root).expanduser().resolve()
    output_path = Path(output_root).expanduser().resolve()
    protocol = build_protocol(data_path, output_path / "protocol", seed=42)
    X_train, y_train, _ = _load_records(protocol, data_path, "initial_known_train", class_labels={"8screws": 0})
    X_cal, y_cal, _ = _load_records(protocol, data_path, "healthy_calibration", class_labels={"8screws": 0})
    X_update, _, update_conditions = _load_records(protocol, data_path, "human_confirmed_update_pool")
    labels_by_condition = {condition: index + 1 for index, condition in enumerate(sorted(set(update_conditions)))}
    y_update = np.asarray([labels_by_condition[condition] for condition in update_conditions], dtype=int)
    # The same first 100 arrival samples are scored before and after learning;
    # no future rows are used to choose the sample or threshold.
    n_probe = min(100, len(X_update))
    X_probe, y_probe = X_update[:n_probe], y_update[:n_probe]
    before = CalibratedHealthIndex.fit(X_train, y_train, X_cal, y_cal)
    after_train = np.vstack([X_train, X_update[: min(50, len(X_update))]])
    after_labels = np.concatenate([y_train, y_update[: min(50, len(y_update))]])
    after_cal = np.vstack([X_cal, X_update[: min(20, len(X_update))]])
    after_cal_labels = np.concatenate([y_cal, y_update[: min(20, len(y_update))]])
    after = CalibratedHealthIndex.fit(
        after_train,
        after_labels,
        after_cal,
        after_cal_labels,
        label_to_fault_type={label: condition for condition, label in labels_by_condition.items()},
    )
    before_results = before.predict(X_probe, condition="T1/8000rpm")
    after_results = after.predict(X_probe, condition="T1/8000rpm")
    before_deviation = np.asarray([item.health_deviation_score for item in before_results], dtype=float)
    after_deviation = np.asarray([item.health_deviation_score for item in after_results], dtype=float)
    before_unknown = np.asarray([item.unknown_score for item in before_results], dtype=float)
    after_unknown = np.asarray([item.unknown_score for item in after_results], dtype=float)
    result = {
        "schema_version": 1,
        "experiment": "score_separation_regression",
        "protocol_fingerprint": protocol["protocol_fingerprint"],
        "probe_samples": int(n_probe),
        "health_deviation_max_abs_change": float(np.max(np.abs(before_deviation - after_deviation))),
        "health_deviation_mean_before": float(before_deviation.mean()),
        "health_deviation_mean_after": float(after_deviation.mean()),
        "unknown_score_mean_before": float(before_unknown.mean()),
        "unknown_score_mean_after": float(after_unknown.mean()),
        "unknown_score_decreased": bool(after_unknown.mean() < before_unknown.mean()),
        "predicted_classes_before": sorted(set(item.predicted_class for item in before_results), key=lambda value: str(value)),
        "predicted_classes_after": sorted(set(item.predicted_class for item in after_results), key=lambda value: str(value)),
        "direction_familiarity_mean_before": float(np.mean([item.direction_familiarity for item in before_results])),
        "direction_familiarity_mean_after": float(np.mean([item.direction_familiarity for item in after_results])),
        "rul_status": "unavailable_no_run_to_failure_data",
        "data_status": "formal_replay; update arrival order simulated by source-file row order",
    }
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run(args.data_root, args.output_root)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
