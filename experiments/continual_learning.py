"""Arrival-only continual-learning replay matrix.

This is an offline protocol runner, not a claim of real deployment time.  The
formal CSVs have no timestamps, so arrival orders are deterministic simulations
of source-file row order.  The immutable test split from P1 is never included
in any update or replay memory.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from core.continual_protocol import build_protocol, validate_leakage
from health.index import CalibratedHealthIndex


DEFAULT_BUDGETS = (10, 25, 50, 100)
DEFAULT_ORDERS = ("mild_to_severe", "severe_to_mild", "random")
DEFAULT_STRATEGIES = (
    "full_historical_replay",
    "fixed_capacity_random",
    "fixed_capacity_class_balanced",
    "new_class_only",
    "full_pool_oracle",
)


def load_records(manifest: dict, data_root: Path, split: str) -> list[dict]:
    """Load only rows named by a manifest split; no labels come from test data."""

    records = [item for item in manifest["records"] if item["split"] == split]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in records:
        grouped[item["source_file"]].append(item)
    loaded: list[dict] = []
    for source_file, items in sorted(grouped.items()):
        # nrows is bounded by the largest row requested from this file.  A
        # budget run never needs to materialise rows after its arrival prefix.
        max_row = max(item["row_index"] for item in items)
        frame = pd.read_csv(data_root / Path(source_file), nrows=max_row + 1)
        values = frame.select_dtypes(include="number").to_numpy(dtype=float)
        for item in sorted(items, key=lambda value: value["row_index"]):
            row = dict(item)
            row["features"] = values[item["row_index"]]
            loaded.append(row)
    return loaded


def arrival_order(records: Sequence[dict], order: str, *, seed: int) -> list[dict]:
    if order not in {"mild_to_severe", "severe_to_mild", "random", "interleaved"}:
        raise ValueError(f"unsupported arrival order: {order}")
    by_condition: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_condition[str(record["condition"])].append(record)
    conditions = sorted(by_condition)
    if order == "mild_to_severe":
        conditions = sorted(conditions, reverse=True)
        return [record for condition in conditions for record in by_condition[condition]]
    if order == "severe_to_mild":
        conditions = sorted(conditions)
        return [record for condition in conditions for record in by_condition[condition]]
    if order == "random":
        rng = np.random.default_rng(seed)
        indices = rng.permutation(len(records))
        return [records[int(index)] for index in indices]
    output: list[dict] = []
    for index in range(max(len(by_condition[condition]) for condition in conditions)):
        for condition in conditions:
            if index < len(by_condition[condition]):
                output.append(by_condition[condition][index])
    return output


def nested_arrivals(records: Sequence[dict], budgets: Sequence[int]) -> dict[int, list[dict]]:
    ordered = list(records)
    if any(int(budget) < 1 for budget in budgets):
        raise ValueError("budgets must be positive")
    if list(budgets) != sorted(budgets):
        raise ValueError("budgets must be sorted")
    if max(budgets) > len(ordered):
        raise ValueError("largest budget exceeds arrival stream")
    prefixes = {int(budget): ordered[: int(budget)] for budget in budgets}
    for previous, current in zip(budgets, budgets[1:]):
        if [item["sample_id"] for item in prefixes[previous]] != [item["sample_id"] for item in prefixes[current]][:previous]:
            raise AssertionError("arrival budgets are not nested")
    return prefixes


def select_replay(records: Sequence[dict], *, capacity: int, strategy: str, seed: int) -> list[dict]:
    if capacity < 1:
        raise ValueError("capacity must be positive")
    if strategy == "full_historical_replay":
        return list(records)
    if strategy == "full_pool_oracle":
        return list(records)
    if strategy == "new_class_only":
        latest = str(records[-1]["condition"])
        return [item for item in records if str(item["condition"]) == latest]
    if len(records) <= capacity:
        return list(records)
    if strategy == "fixed_capacity_random":
        rng = np.random.default_rng(seed)
        indices = sorted(int(value) for value in rng.choice(len(records), size=capacity, replace=False))
        return [records[index] for index in indices]
    if strategy == "fixed_capacity_class_balanced":
        by_condition: dict[str, list[dict]] = defaultdict(list)
        for item in records:
            by_condition[str(item["condition"])].append(item)
        output: list[dict] = []
        index = 0
        conditions = sorted(by_condition)
        while len(output) < capacity:
            added = False
            for condition in conditions:
                rows = by_condition[condition]
                if index < len(rows) and len(output) < capacity:
                    output.append(rows[index])
                    added = True
            if not added:
                break
            index += 1
        return output
    raise ValueError(f"unsupported replay strategy: {strategy}")


def _fit_model(healthy_train: list[dict], healthy_cal: list[dict], update: list[dict], strategy: str, *, seed: int):
    replay = select_replay(update, capacity=50, strategy=strategy, seed=seed)
    conditions = sorted({str(item["condition"]) for item in replay})
    label_map = {condition: index + 1 for index, condition in enumerate(conditions)}
    train_features = [item["features"] for item in healthy_train]
    train_labels = [0] * len(train_features)
    cal_features = [item["features"] for item in healthy_cal]
    cal_labels = [0] * len(cal_features)
    for condition in conditions:
        class_rows = [item for item in replay if str(item["condition"]) == condition]
        if len(class_rows) < 2:
            raise ValueError(f"class {condition} has fewer than two arrived samples")
        split_at = max(1, int(len(class_rows) * 0.8))
        if split_at >= len(class_rows):
            split_at = len(class_rows) - 1
        train_features.extend(item["features"] for item in class_rows[:split_at])
        train_labels.extend([label_map[condition]] * split_at)
        cal_features.extend(item["features"] for item in class_rows[split_at:])
        cal_labels.extend([label_map[condition]] * (len(class_rows) - split_at))
    model = CalibratedHealthIndex.fit(
        np.asarray(train_features),
        np.asarray(train_labels, dtype=int),
        np.asarray(cal_features),
        np.asarray(cal_labels, dtype=int),
        label_to_fault_type={label: condition for condition, label in label_map.items()},
    )
    return model, replay, label_map


def _evaluate(model: CalibratedHealthIndex, test: list[dict], update_eval: list[dict], label_map: dict[str, int]) -> dict:
    test_features = np.asarray([item["features"] for item in test])
    test_results = model.predict(test_features, condition="formal-test")
    healthy = np.asarray([item["condition"] == "8screws" for item in test], dtype=bool)
    unknown = ~healthy
    test_unknown = np.asarray([item.is_unknown_fault for item in test_results], dtype=bool)
    binary_expected = unknown
    binary_accuracy = float((test_unknown == binary_expected).mean())
    healthy_fpr = float(test_unknown[healthy].mean()) if healthy.any() else None
    unknown_recall = float(test_unknown[unknown].mean()) if unknown.any() else None
    eval_features = np.asarray([item["features"] for item in update_eval])
    eval_results = model.predict(eval_features, condition="formal-arrival-eval")
    expected_labels = np.asarray([label_map.get(str(item["condition"]), -1) for item in update_eval], dtype=int)
    predicted_labels = np.asarray([
        label_map.get(result.predicted_class, -1) if result.predicted_class is not None else -1
        for result in eval_results
    ], dtype=int)
    known = expected_labels >= 0
    new_recall = float((predicted_labels[known] == expected_labels[known]).mean()) if known.any() else None
    return {
        "healthy_false_positive_rate": healthy_fpr,
        "unknown_recall": unknown_recall,
        "average_binary_accuracy": binary_accuracy,
        "new_class_macro_f1": float(f1_score(expected_labels[known], predicted_labels[known], average="macro", zero_division=0)) if known.any() else None,
        "new_class_recall": new_recall,
        "known_classes": sorted(label_map),
    }


def run(
    data_root: Path | str,
    output_root: Path | str,
    *,
    seeds: Iterable[int] = (42, 123, 2026),
    budgets: Sequence[int] = DEFAULT_BUDGETS,
) -> dict:
    data_path = Path(data_root).expanduser().resolve()
    output_path = Path(output_root).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    manifest = build_protocol(data_path, output_path / "protocol", seed=42)
    healthy_train = load_records(manifest, data_path, "initial_known_train")
    healthy_cal = load_records(manifest, data_path, "healthy_calibration")
    arrival_records = load_records(manifest, data_path, "human_confirmed_update_pool")
    immutable_test = load_records(manifest, data_path, "immutable_test")
    validate_leakage(manifest, replay_sample_ids=[], reference_sample_ids=[item["sample_id"] for item in healthy_train + healthy_cal])
    rows: list[dict] = []
    for seed in seeds:
        for order in (*DEFAULT_ORDERS, "interleaved"):
            ordered = arrival_order(arrival_records, order, seed=int(seed))
            prefixes = nested_arrivals(ordered, budgets)
            for strategy in DEFAULT_STRATEGIES:
                prior_metrics: dict[str, dict] = {}
                prior_versions: dict[str, str] = {}
                for budget in budgets:
                    arrived = prefixes[int(budget)]
                    if strategy == "full_pool_oracle":
                        update_source = ordered
                    else:
                        update_source = arrived
                    start = time.perf_counter()
                    model, replay, label_map = _fit_model(healthy_train, healthy_cal, update_source, strategy, seed=int(seed))
                    update_seconds = time.perf_counter() - start
                    metrics_after = _evaluate(model, immutable_test, arrival_records, label_map)
                    parent = prior_versions.get(strategy)
                    metrics_before = prior_metrics.get(strategy)
                    version = f"cl-{seed}-{order}-{strategy}-{budget}"
                    sample_ids = [item["sample_id"] for item in arrived]
                    replay_ids = [item["sample_id"] for item in replay]
                    validate_leakage(manifest, replay_sample_ids=replay_ids, reference_sample_ids=[item["sample_id"] for item in healthy_train + healthy_cal])
                    replay_fingerprint = hashlib.sha256("\n".join(replay_ids).encode()).hexdigest()
                    row = {
                        "run_id": version,
                        "status": "completed",
                        "seed": int(seed),
                        "arrival_order": order,
                        "strategy": strategy,
                        "budget": int(budget),
                        "is_oracle": strategy == "full_pool_oracle",
                        "model_version": version,
                        "parent_model_version": parent,
                        "rollback_pointer": parent,
                        "samples_used": sample_ids if not strategy == "full_pool_oracle" else [item["sample_id"] for item in ordered],
                        "replay_memory": {
                            "capacity": 50,
                            "strategy": strategy,
                            "n_samples": len(replay),
                            "fingerprint": replay_fingerprint,
                        },
                        "calibration_version": "health-index-calibration-v1",
                        "health_reference_version": "healthy-reference-v1",
                        "metrics_before": metrics_before,
                        "metrics_after": metrics_after,
                        "update_seconds": float(update_seconds),
                        "memory_samples": len(replay),
                        "protocol_fingerprint": manifest["protocol_fingerprint"],
                        "future_samples_read": False,
                        "data_status": "simulated_arrival_order_no_timestamp",
                    }
                    rows.append(row)
                    prior_metrics[strategy] = metrics_after
                    prior_versions[strategy] = version
    sample_ids_by_run = {row["run_id"]: row.pop("samples_used") for row in rows}
    for row in rows:
        row["samples_used_artifact"] = "sample_ids.json.gz"
        row["samples_used_count"] = len(sample_ids_by_run[row["run_id"]])
    summary = {
        "schema_version": 1,
        "experiment": "arrival_only_continual_learning",
        "protocol_fingerprint": manifest["protocol_fingerprint"],
        "budgets": [int(item) for item in budgets],
        "seeds": [int(item) for item in seeds],
        "orders": [*DEFAULT_ORDERS, "interleaved"],
        "strategies": list(DEFAULT_STRATEGIES),
        "immutable_test_samples": len(immutable_test),
        "rows": rows,
        "status": "completed",
    }
    (output_path / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with gzip.open(output_path / "sample_ids.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(sample_ids_by_run, handle, ensure_ascii=False, separators=(",", ":"))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(args.data_root, args.output_root)
    print(json.dumps({"rows": len(summary["rows"]), "status": summary["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
