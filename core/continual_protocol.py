"""Immutable split and leakage checks for arrival-only experiments.

The formal Lineage CSVs do not carry a trusted motor-session timestamp.  This
module therefore treats each source CSV as an indivisible group and records
that limitation instead of pretending that windows from one file are
independent.  The protocol is deliberately independent of update budget: a
budget changes which *arrived* update rows are used, never the immutable test
manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from core.formal_data import CONFIGS, FEATURE_DIM


PROTOCOL_SCHEMA_VERSION = 1
SPLITS = (
    "initial_known_train",
    "healthy_calibration",
    "discovery_stream",
    "human_confirmed_update_pool",
    "validation",
    "immutable_test",
)
HEALTHY = "8screws"
DEFAULT_ASSIGNMENT: dict[tuple[str, str], str] = {
    ("1", HEALTHY): "initial_known_train",
    ("2", HEALTHY): "healthy_calibration",
    ("2", "7screws"): "validation",
    ("2", "6screws"): "discovery_stream",
    ("2", "5screws"): "discovery_stream",
    ("3", "6screws"): "human_confirmed_update_pool",
    ("3", "5screws"): "human_confirmed_update_pool",
    ("3", "8screws"): "immutable_test",
    ("3", "7screws"): "immutable_test",
    ("3", "4screws"): "immutable_test",
    ("3", "3screws"): "immutable_test",
    ("3", "2screws"): "immutable_test",
    ("3", "1screws"): "immutable_test",
    ("3", "3_14screws"): "immutable_test",
    ("3", "4_146screws"): "immutable_test",
}


class ProtocolError(ValueError):
    """Raised when a split or leakage contract is violated."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sample_id(file_sha256: str, row_index: int, row: np.ndarray) -> str:
    payload = file_sha256.encode("ascii") + b":" + str(row_index).encode("ascii") + b":" + row.tobytes()
    return _sha256_bytes(payload)


def _parse_file(path: Path, data_root: Path) -> tuple[dict, pd.DataFrame]:
    relative = path.relative_to(data_root)
    parts = relative.parts
    if len(parts) != 6 or parts[0] not in {"Step-1", "Step-2", "Step-3"}:
        raise ProtocolError(f"unexpected feature path: {relative}")
    stage = parts[0].split("-", 1)[1]
    motor, rpm, config = parts[2], parts[3], parts[4]
    if config not in CONFIGS:
        raise ProtocolError(f"unsupported config {config!r} in {relative}")
    frame = pd.read_csv(path)
    numeric = frame.select_dtypes(include="number")
    if list(numeric.columns) != list(frame.columns) or numeric.shape[1] != FEATURE_DIM:
        raise ProtocolError(
            f"{relative}: expected exactly {FEATURE_DIM} numeric columns in source order"
        )
    values = numeric.to_numpy(dtype=float)
    if len(values) == 0 or not np.isfinite(values).all():
        raise ProtocolError(f"{relative}: empty or non-finite feature rows")
    return {
        "source_file": relative.as_posix(),
        "source_sha256": _sha256_file(path),
        "stage": stage,
        "motor_id": motor,
        "session_id": None,
        "rpm": rpm,
        "condition": config,
        "rows": int(len(values)),
    }, frame


def _assignment_for(stage: str, config: str, assignment: Mapping[tuple[str, str], str]) -> str | None:
    return assignment.get((stage, config))


def validate_leakage(
    manifest: Mapping,
    *,
    replay_sample_ids: Iterable[str] = (),
    reference_sample_ids: Iterable[str] = (),
) -> dict[str, object]:
    """Validate file/group/sample disjointness and test exclusion contracts."""

    records = list(manifest.get("records", []))
    split_sets: dict[str, set[str]] = {name: set() for name in SPLITS}
    file_sets: dict[str, set[str]] = {name: set() for name in SPLITS}
    group_sets: dict[str, set[str]] = {name: set() for name in SPLITS}
    for record in records:
        split = record.get("split")
        if split not in split_sets:
            raise ProtocolError(f"invalid split {split!r}")
        split_sets[split].add(str(record["sample_id"]))
        file_sets[split].add(str(record["source_file"]))
        # No trusted session id is available; source_file is the conservative group.
        group_sets[split].add(str(record["group_id"]))

    def _pairwise_disjoint(groups: Mapping[str, set[str]]) -> list[str]:
        collisions: list[str] = []
        names = list(groups)
        for index, left in enumerate(names):
            for right in names[index + 1 :]:
                overlap = groups[left].intersection(groups[right])
                collisions.extend(f"{left}:{right}:{value}" for value in sorted(overlap))
        return collisions

    test_ids = split_sets["immutable_test"]
    replay = set(replay_sample_ids)
    reference = set(reference_sample_ids)
    checks = {
        "raw_file_overlap": _pairwise_disjoint(file_sets),
        "group_overlap": _pairwise_disjoint(group_sets),
        "duplicate_sample_fingerprint": sorted(
            sample_id for sample_id, count in Counter(record["sample_id"] for record in records).items() if count > 1
        ),
        "test_in_replay_memory": sorted(test_ids.intersection(replay)),
        "test_in_calibration": sorted(test_ids.intersection(split_sets["healthy_calibration"])),
        "test_in_detector_reference": sorted(test_ids.intersection(reference)),
    }
    failures = {name: values for name, values in checks.items() if values}
    if failures:
        raise ProtocolError(f"leakage checks failed: {json.dumps(failures, ensure_ascii=False)}")
    return {
        "status": "passed",
        "checks": {name: {"status": "passed", "count": len(values)} for name, values in checks.items()},
        "immutable_test_count": len(test_ids),
    }


def build_protocol(
    data_root: Path | str,
    output_root: Path | str,
    *,
    seed: int = 42,
    assignment: Mapping[tuple[str, str], str] | None = None,
) -> dict:
    """Build and persist a deterministic file-grouped protocol manifest."""

    data_path = Path(data_root).expanduser().resolve()
    output_path = Path(output_root).expanduser().resolve()
    if not data_path.is_dir():
        raise ProtocolError(f"data root does not exist: {data_path}")
    if data_path == output_path or data_path in output_path.parents:
        raise ProtocolError("output root must not be inside the read-only data root")
    assignment_map = dict(assignment or DEFAULT_ASSIGNMENT)
    if any(value not in SPLITS for value in assignment_map.values()):
        raise ProtocolError(f"assignment contains an unknown split: {assignment_map}")

    files = sorted(data_path.glob("Step-*/myfeature/*/*/*/*_Group_feature_data_clean.csv"))
    if not files:
        raise ProtocolError(f"no formal feature CSVs found under {data_path}")
    records: list[dict] = []
    file_records: list[dict] = []
    excluded_files: list[str] = []
    for path in files:
        file_meta, frame = _parse_file(path, data_path)
        split = _assignment_for(file_meta["stage"], file_meta["condition"], assignment_map)
        if split is None:
            excluded_files.append(file_meta["source_file"])
            continue
        file_meta["split"] = split
        file_meta["group_id"] = file_meta["source_file"]
        file_records.append(file_meta)
        values = frame.select_dtypes(include="number").to_numpy(dtype=float)
        for row_index, row in enumerate(values):
            records.append(
                {
                    "sample_id": _sample_id(file_meta["source_sha256"], row_index, row),
                    "row_index": int(row_index),
                    "source_file": file_meta["source_file"],
                    "source_sha256": file_meta["source_sha256"],
                    "group_id": file_meta["group_id"],
                    "split": split,
                    "stage": file_meta["stage"],
                    "motor_id": file_meta["motor_id"],
                    "session_id": file_meta["session_id"],
                    "rpm": file_meta["rpm"],
                    "condition": file_meta["condition"],
                    "label": 0 if file_meta["condition"] == HEALTHY else file_meta["condition"],
                }
            )

    manifest = {
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_label": "formal_feature_csv",
        "source_root_label": "data/formal_local",
        "source_root_sha256": _sha256_bytes("\n".join(sorted(item["source_sha256"] for item in file_records)).encode()),
        "seed": int(seed),
        "assignment_policy": {f"{stage}/{config}": split for (stage, config), split in sorted(assignment_map.items())},
        "group_policy": "source_file_indivisible; session_id unavailable in formal CSV",
        "records": records,
        "files": file_records,
        "excluded_files": excluded_files,
    }
    validate_leakage(manifest)
    # Fingerprint the split identity, not wall-clock creation time or an
    # unused seed.  This lets a resume run prove that immutable_test stayed
    # byte-identical even when an update-budget experiment uses another seed.
    fingerprint_payload = {
        "schema_version": manifest["schema_version"],
        "assignment_policy": manifest["assignment_policy"],
        "group_policy": manifest["group_policy"],
        "files": manifest["files"],
        "records": manifest["records"],
    }
    canonical = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["protocol_fingerprint"] = _sha256_bytes(canonical)
    counts = Counter(record["split"] for record in records)
    manifest["summary"] = {
        "files_by_split": dict(Counter(item["split"] for item in file_records)),
        "samples_by_split": {split: int(counts.get(split, 0)) for split in SPLITS},
        "conditions_by_split": {
            split: sorted({item["condition"] for item in file_records if item["split"] == split})
            for split in SPLITS
        },
        "session_id_status": "unavailable; source-file grouping is the conservative fallback",
    }
    output_path.mkdir(parents=True, exist_ok=True)
    # Keep the committed artifact reviewable: file-level metadata contains
    # motor/RPM/condition, while each sample only needs its identity and row
    # location for leakage audits.  The full in-memory manifest remains useful
    # to callers that want the expanded fields.
    disk_manifest = dict(manifest)
    disk_manifest["records"] = [
        {
            "sample_id": item["sample_id"],
            "row_index": item["row_index"],
            "source_file": item["source_file"],
            "source_sha256": item["source_sha256"],
            "group_id": item["group_id"],
            "split": item["split"],
        }
        for item in records
    ]
    (output_path / "split_manifest.json").write_text(json.dumps(disk_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_path / "split_summary.json").write_text(json.dumps(manifest["summary"], ensure_ascii=False, indent=2), encoding="utf-8")
    (output_path / "split_fingerprints.json").write_text(
        json.dumps(
            {
                "protocol_fingerprint": manifest["protocol_fingerprint"],
                "immutable_test_sample_ids": sorted(
                    item["sample_id"] for item in records if item["split"] == "immutable_test"
                ),
                "immutable_test_file_ids": sorted(
                    item["source_file"] for item in file_records if item["split"] == "immutable_test"
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    manifest = build_protocol(args.data_root, args.output_root, seed=args.seed)
    print(json.dumps({"protocol_fingerprint": manifest["protocol_fingerprint"], "summary": manifest["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
