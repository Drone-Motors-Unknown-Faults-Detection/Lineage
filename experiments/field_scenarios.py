"""Replay field-like stress scenarios without changing detector training data."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import hdbscan
import numpy as np
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.preprocessing import RobustScaler

from core.continual_protocol import build_protocol
from health.evaluation import evaluate_alarm_series
from health.index import CalibratedHealthIndex
from health.sensor_quality import assess_sensor_window
from health.thresholds import AlarmPolicy
from experiments.continual_learning import arrival_order, load_records


def _fit_baseline(healthy_train: list[dict], healthy_cal: list[dict]) -> CalibratedHealthIndex:
    return CalibratedHealthIndex.fit(
        np.asarray([item["features"] for item in healthy_train]),
        np.zeros(len(healthy_train), dtype=int),
        np.asarray([item["features"] for item in healthy_cal]),
        np.zeros(len(healthy_cal), dtype=int),
    )


def _purity(cluster_labels: np.ndarray, truth: np.ndarray) -> float:
    correct = 0
    for cluster in np.unique(cluster_labels):
        members = truth[cluster_labels == cluster]
        if len(members):
            correct += Counter(members.tolist()).most_common(1)[0][1]
    return float(correct / len(truth)) if len(truth) else 0.0


def _mixed_unknown(model: CalibratedHealthIndex, records: list[dict], *, seed: int) -> dict:
    by_condition: dict[str, list[dict]] = {}
    for record in records:
        if record["condition"] in {"3screws", "4screws"}:
            by_condition.setdefault(record["condition"], []).append(record)
    selected = []
    for index in range(100):
        for condition in ("3screws", "4screws"):
            if index < len(by_condition.get(condition, [])):
                selected.append(by_condition[condition][index])
    rng = np.random.default_rng(seed)
    if selected:
        selected = [selected[int(index)] for index in rng.permutation(len(selected))]
    features = np.asarray([item["features"] for item in selected])
    truth = np.asarray([item["condition"] for item in selected])
    scores = np.asarray([item.openset_score for item in model.predict(features, condition="mixed-unknown")])
    scaled = model.scaler.transform(features)
    cluster_labels = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=3).fit_predict(scaled)
    clusters = sorted(set(int(value) for value in cluster_labels if int(value) >= 0))
    return {
        "status": "completed",
        "source_sample_ids": [item["sample_id"] for item in selected],
        "n_samples": len(selected),
        "unknown_recall": float((scores > 1.0).mean()) if len(scores) else None,
        "cluster_count_excluding_noise": len(clusters),
        "noise_fraction": float((cluster_labels == -1).mean()) if len(cluster_labels) else None,
        "cluster_purity": _purity(cluster_labels, truth),
        "adjusted_rand_index": float(adjusted_rand_score(truth, cluster_labels)) if len(selected) else None,
        "normalized_mutual_info": float(normalized_mutual_info_score(truth, cluster_labels)) if len(selected) else None,
        "candidate_fragmentation": max(0, len(clusters) - len(set(truth))),
        "candidate_merging": len(clusters) < len(set(truth)),
    }


def _arrival_order_results(model: CalibratedHealthIndex, records: list[dict]) -> dict:
    output = {}
    for order in ("mild_to_severe", "severe_to_mild", "random"):
        ordered = arrival_order(records, order, seed=42)
        scores = [model.predict_one(item["features"], condition="arrival").openset_score for item in ordered]
        output[order] = {
            "first_unknown_index": next((index for index, score in enumerate(scores) if score > 1.0), None),
            "n_samples": len(scores),
            "simulated": True,
        }
    return output


def _condition_shift(model: CalibratedHealthIndex, healthy_test: list[dict]) -> dict:
    grouped: dict[str, list[dict]] = {}
    for item in healthy_test:
        grouped.setdefault(f"{item['motor_id']}|{item['rpm']}", []).append(item)
    result = {}
    for condition, items in sorted(grouped.items()):
        scores = np.asarray([item.openset_score for item in model.predict(np.asarray([row["features"] for row in items]), condition=condition)])
        result[condition] = {"n": len(items), "false_positive_rate": float((scores > 1.0).mean())}
    return result


def _contamination(model_factory, healthy_train: list[dict], healthy_test: list[dict], unknown_test: list[dict], mixed: list[dict]) -> dict:
    clean = np.asarray([item["features"] for item in healthy_train])
    clean_labels = np.zeros(len(clean), dtype=int)
    calibration = clean[: max(1, len(clean) // 5)]
    unknown = np.asarray([item["features"] for item in mixed])
    output = {}
    rng = np.random.default_rng(42)
    for ratio in (0.0, 0.01, 0.05, 0.10):
        train = clean.copy()
        n_replace = int(len(train) * ratio)
        if n_replace:
            indices = rng.choice(len(train), size=n_replace, replace=False)
            train[indices] = unknown[:n_replace]
        model = model_factory(train, clean_labels, calibration, np.zeros(len(calibration), dtype=int))
        healthy_scores = np.asarray([item.openset_score for item in model.predict(np.asarray([row["features"] for row in healthy_test]), condition="contaminated-healthy")])
        unknown_scores = np.asarray([item.openset_score for item in model.predict(np.asarray([row["features"] for row in unknown_test]), condition="contaminated-unknown")])
        output[str(ratio)] = {
            "contamination_fraction": ratio,
            "healthy_false_positive_rate": float((healthy_scores > 1.0).mean()),
            "unknown_recall": float((unknown_scores > 1.0).mean()),
            "n_replaced": n_replace,
        }
    return output


def _sensor_scenarios() -> dict:
    base = np.sin(np.linspace(0, 4 * np.pi, 100))[:, None] * np.ones((1, 3))
    scenarios = {
        "clean": (base, np.arange(100, dtype=float)),
        "missing_points": (base.copy(), np.arange(100, dtype=float)),
        "saturation": (base.copy(), np.arange(100, dtype=float)),
        "offset_drift": (base.copy(), np.arange(100, dtype=float)),
        "single_channel_failure": (base.copy(), np.arange(100, dtype=float)),
        "dropout": (base.copy(), np.arange(100, dtype=float)),
        "timestamp_gap": (base.copy(), np.arange(100, dtype=float)),
    }
    scenarios["missing_points"][0][10, 1] = np.nan
    scenarios["saturation"][0][20:30, 0] = 99.0
    scenarios["offset_drift"][0][50:, 2] += 10.0
    scenarios["single_channel_failure"][0][:, 1] = 0.0
    scenarios["dropout"][0][40:60, :] = np.nan
    scenarios["timestamp_gap"] = (base.copy(), np.concatenate([np.arange(50), np.arange(50) + 61.0]))
    reports = {}
    for name, (values, timestamps) in scenarios.items():
        reports[name] = assess_sensor_window(values, timestamps=timestamps, expected_interval=1.0, bounds=(-5.0, 5.0)).to_dict()
    return reports


def _transient_persistent() -> dict:
    scores_transient = np.full(100, 0.2)
    scores_transient[40] = 1.4
    labels_transient = np.zeros(100, dtype=int)
    scores_persistent = np.full(100, 0.2)
    scores_persistent[40:] = 1.4
    labels_persistent = np.zeros(100, dtype=int)
    labels_persistent[40:] = 1
    timestamps = list(range(100))
    return {
        "single_spike": evaluate_alarm_series(scores_transient, labels_transient, timestamps, threshold=1.0, policy=AlarmPolicy(kind="single")),
        "single_spike_consecutive": evaluate_alarm_series(scores_transient, labels_transient, timestamps, threshold=1.0, policy=AlarmPolicy(kind="consecutive", consecutive=2)),
        "persistent_event": evaluate_alarm_series(scores_persistent, labels_persistent, timestamps, threshold=1.0, policy=AlarmPolicy(kind="consecutive", consecutive=2)),
    }


def run(data_root: Path | str, output_root: Path | str) -> dict:
    data_path = Path(data_root).expanduser().resolve()
    output_path = Path(output_root).expanduser().resolve()
    protocol = build_protocol(data_path, output_path / "protocol", seed=42)
    healthy_train = load_records(protocol, data_path, "initial_known_train")
    healthy_cal = load_records(protocol, data_path, "healthy_calibration")
    test = load_records(protocol, data_path, "immutable_test")
    update = load_records(protocol, data_path, "human_confirmed_update_pool")
    model = _fit_baseline(healthy_train, healthy_cal)
    healthy_test = [item for item in test if item["condition"] == "8screws"]
    unknown_test = [item for item in test if item["condition"] != "8screws"]
    mixed_records = [item for item in test if item["condition"] in {"3screws", "4screws"}]
    scenarios = {
        "mixed_unknown_stream": _mixed_unknown(model, test, seed=42),
        "fault_arrival_orders": _arrival_order_results(model, update),
        "healthy_condition_shift": _condition_shift(model, healthy_test),
        "sensor_anomalies": _sensor_scenarios(),
        "transient_vs_persistent": _transient_persistent(),
    }
    scenarios["contaminated_healthy_initialization"] = _contamination(
        lambda train, labels, cal, cal_labels: CalibratedHealthIndex.fit(train, labels, cal, cal_labels),
        healthy_train,
        healthy_test,
        unknown_test,
        mixed_records,
    )
    result = {
        "schema_version": 1,
        "experiment": "field_scenarios",
        "protocol_fingerprint": protocol["protocol_fingerprint"],
        "seed": 42,
        "scenario_status": "simulation_replay_formal_data",
        "scenarios": scenarios,
        "ground_truth_policy": "only offline metrics use condition labels; detector fitting does not use immutable_test labels",
        "real_hardware_status": "pending_field_collection_protocol",
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
    print(json.dumps({"scenarios": list(result["scenarios"]), "status": result["scenario_status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
