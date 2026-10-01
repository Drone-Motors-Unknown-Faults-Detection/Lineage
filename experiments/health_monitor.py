"""CLI for calibrated window inference and optional session health streaming."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from core.data import HEALTHY, discover_datasets, load_pools, make_split
from health.index import CalibratedHealthIndex
from health.trajectory import SessionTrajectoryMonitor


def _dataset(data_root: Path | str, motor: str, rpm: str) -> dict:
    rpm_name = str(rpm)
    if not rpm_name.endswith("rpm"):
        rpm_name = f"{rpm_name}rpm"
    matches = [
        row
        for row in discover_datasets(Path(data_root).expanduser().resolve())
        if row["motor"] == motor and row["rpm"] == rpm_name
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one dataset for {motor}/{rpm_name}, found {len(matches)}")
    return matches[0]


def run(
    data_root: Path | str,
    motor: str,
    rpm: str,
    config: str,
    *,
    seed: int = 42,
    openset_method: str = "mahalanobis",
    mahalanobis_method: str = "ledoit_wolf",
    knn_neighbors: int = 5,
    motor_id: str | None = None,
    session_id: str | None = None,
    max_windows: int | None = None,
    require_identity: bool = True,
) -> list[dict]:
    dataset = _dataset(data_root, motor, rpm)
    pools = load_pools(dataset["path"])
    if config not in pools:
        raise KeyError(f"configuration {config!r} is not available in {dataset['path']}")
    rng = np.random.default_rng(seed)
    healthy = pools[HEALTHY]
    split = make_split(len(healthy), rng)
    model = CalibratedHealthIndex.fit(
        healthy[split.train],
        np.zeros(len(split.train), dtype=int),
        healthy[split.cal],
        np.zeros(len(split.cal), dtype=int),
        openset_method=openset_method,
        mahalanobis_method=mahalanobis_method,
        knn_neighbors=knn_neighbors,
    )
    monitor = SessionTrajectoryMonitor(model, require_identity=require_identity)
    samples = pools[config][split.holdout]
    if max_windows is not None:
        if max_windows < 1:
            raise ValueError("max_windows must be positive")
        samples = samples[:max_windows]
    condition = f"{motor}/{dataset['rpm']}"
    output: list[dict] = []
    for index, sample in enumerate(samples):
        result = monitor.update(
            sample,
            motor_id=motor_id,
            session_id=session_id,
            timestamp=None,
            condition=condition,
        )
        payload = result.to_dict("full")
        payload["window_index"] = int(index)
        output.append(payload)
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default="data/formal_local")
    parser.add_argument("--motor", required=True)
    parser.add_argument("--rpm", required=True)
    parser.add_argument("--config", default=HEALTHY)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--openset-method", default="mahalanobis")
    parser.add_argument("--method", dest="mahalanobis_method", default="ledoit_wolf")
    parser.add_argument("--knn-neighbors", type=int, default=5)
    parser.add_argument("--motor-id")
    parser.add_argument("--session-id")
    parser.add_argument("--max-windows", type=int)
    parser.add_argument("--output-mode", choices=("binary", "health", "full"), default="full")
    parser.add_argument(
        "--allow-no-identity",
        action="store_true",
        help="allow output without temporal identity; trend remains insufficient_history when absent",
    )
    args = parser.parse_args(argv)
    results = run(
        args.data_root,
        args.motor,
        args.rpm,
        args.config,
        seed=args.seed,
        openset_method=args.openset_method,
        mahalanobis_method=args.mahalanobis_method,
        knn_neighbors=args.knn_neighbors,
        motor_id=args.motor_id,
        session_id=args.session_id,
        max_windows=args.max_windows,
        require_identity=not args.allow_no_identity,
    )
    for result in results:
        # ``to_dict`` is applied after stream state updates so the CLI and
        # programmatic API expose exactly the same contract.
        if args.output_mode == "binary":
            print(json.dumps({"is_fault": result["is_fault"]}, ensure_ascii=False))
        elif args.output_mode == "health":
            print(json.dumps({key: result[key] for key in (
                "is_fault", "health_index", "degradation_score", "severity_stage", "trend",
                "degradation_rate", "openset_method", "openset_score", "is_unknown_fault",
                "prediction_confidence", "uncertainty", "timestamp", "condition", "data_quality",
                "alarm_state", "alarm_reason", "severity_basis", "raw_health_index",
                "smoothed_health_index", "change_point_state", "window_index",
            )}, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
