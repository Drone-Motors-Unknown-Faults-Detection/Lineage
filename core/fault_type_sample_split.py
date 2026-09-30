"""Campaign-held-out sample splits for fault-configuration open-set studies.

The formal archive has three acquisition-stage codes (T1/T2/T3), but no
verified physical motor or session identifiers.  A campaign is kept whole in
each fold.  This is deliberately stricter than splitting source-file windows,
although it cannot prove independence between physical motors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path

from core.continual_protocol import ProtocolError, _parse_file, _sample_id


CAMPAIGNS = ("1", "2", "3")


class SampleSplitError(ValueError):
    """The input cannot support a deterministic campaign-held-out split."""


def load_formal_catalog(data_root: Path | str) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Index every formal clean CSV without retaining feature vectors.

    File parsing and sample IDs deliberately use the P1 protocol's rules.
    ``physical_motor_id`` and other unverified acquisition provenance remain
    null; the T-code and stage are only path-level campaign identifiers.
    """

    root = Path(data_root).expanduser().resolve()
    if not root.is_dir():
        raise SampleSplitError(f"formal data root does not exist: {root}")
    paths = sorted(root.glob("Step-*/myfeature/*/*/*/*_Group_feature_data_clean.csv"))
    if not paths:
        raise SampleSplitError(f"no formal clean feature CSVs under {root}")

    records: list[dict[str, object]] = []
    files: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for path in paths:
        try:
            meta, frame = _parse_file(path, root)
        except ProtocolError as exc:
            raise SampleSplitError(f"invalid formal source {path}: {exc}") from exc
        source = str(meta["source_file"])
        sha256 = str(meta["source_sha256"])
        file_info: dict[str, object] = {
            "source_file": source,
            "source_sha256": sha256,
            "group_id": source,
            "stage": str(meta["stage"]),
            "t_code": str(meta["motor_id"]),
            "rpm": str(meta["rpm"]),
            "label": str(meta["condition"]),
            "rows": int(meta["rows"]),
            "feature_dim": int(frame.shape[1]),
        }
        files.append(file_info)
        for row_index, row in enumerate(frame.to_numpy(dtype=float)):
            sample_id = _sample_id(sha256, row_index, row)
            if sample_id in seen_ids:
                raise SampleSplitError(f"duplicate formal sample_id: {sample_id}")
            seen_ids.add(sample_id)
            records.append({
                "sample_id": sample_id,
                "row_index": row_index,
                "label": file_info["label"],
                "stage": file_info["stage"],
                "t_code": file_info["t_code"],
                "rpm": file_info["rpm"],
                "source_file": source,
                "source_sha256": sha256,
                "group_id": source,
                "physical_motor_id": None,
                "session_id": None,
                "run_id": None,
                "acquisition_timestamp": None,
                "raw_source_file": None,
                "source_interval": None,
                "event_id": None,
                "load": None,
                "environment_temperature": None,
            })

    fingerprint_payload = json.dumps(
        sorted(str(item["source_sha256"]) for item in files),
        separators=(",", ":"),
    ).encode("utf-8")
    summary: dict[str, object] = {
        "dataset_fingerprint_method": "sha256(compact_json(sorted(source_sha256 for all files)))",
        "dataset_fingerprint": hashlib.sha256(fingerprint_payload).hexdigest(),
        "file_count": len(files),
        "sample_count": len(records),
        "feature_dim": 105,
        "group_key": "acquisition_stage_campaign; source_file subgroup",
        "provenance_status": "physical motor, session, run, timestamp, raw interval and event unavailable",
        "files": files,
    }
    return records, summary


def _stage(value: object) -> str:
    token = str(value)
    if token.startswith("Step-"):
        token = token[5:]
    if token not in CAMPAIGNS:
        raise SampleSplitError(f"unsupported stage {value!r}; expected 1, 2 or 3")
    return token


def _label_set(values: Iterable[object]) -> set[str]:
    labels = {str(value) for value in values}
    if "" in labels:
        raise SampleSplitError("class-role labels must not be empty")
    return labels


def _records_by_id(records: Iterable[Mapping[str, object]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    source_owners: dict[str, tuple[str, str, str]] = {}
    group_owners: dict[str, tuple[str, str, str]] = {}
    for index, record in enumerate(records):
        try:
            sample_id = str(record["sample_id"])
            label = str(record["label"])
            stage = _stage(record["stage"])
            source = str(record["source_file"]).replace("\\", "/")
            group = str(record["group_id"])
        except KeyError as exc:
            raise SampleSplitError(f"record {index} lacks required field {exc.args[0]}") from exc
        if not all((sample_id, label, source, group)):
            raise SampleSplitError(f"record {index} has an empty required field")
        if sample_id in seen_ids:
            raise SampleSplitError(f"duplicate sample_id: {sample_id}")
        seen_ids.add(sample_id)

        path_stages = {part[5:] for part in source.split("/") if part.startswith("Step-")}
        if path_stages and path_stages != {stage}:
            raise SampleSplitError(f"stage/source_file mismatch for {sample_id}: {stage}, {source}")

        owner = (stage, source, label)
        if source in source_owners and source_owners[source] != (stage, group, label):
            raise SampleSplitError(f"source_file crosses stage, group or label: {source}")
        if group in group_owners and group_owners[group] != owner:
            raise SampleSplitError(f"group_id crosses source_file, stage or label: {group}")
        source_owners[source] = (stage, group, label)
        group_owners[group] = owner
        normalized.append(
            {
                "sample_id": sample_id,
                "label": label,
                "stage": stage,
                "source_file": source,
                "group_id": group,
            }
        )

    if not normalized:
        raise SampleSplitError("no records")
    present = {item["stage"] for item in normalized}
    if present != set(CAMPAIGNS):
        raise SampleSplitError(f"all three campaigns are required; present={sorted(present)}")
    return sorted(normalized, key=lambda item: item["sample_id"])


def generate_campaign_folds(
    records: Iterable[Mapping[str, object]],
    *,
    healthy_label: object,
    known_fault_labels: Iterable[object],
    unknown_validation_labels: Iterable[object] = (),
    unknown_test_labels: Iterable[object] = (),
) -> list[dict[str, object]]:
    """Rotate train / shared validation-calibration / test over three campaigns.

    The validation and calibration lists intentionally contain the *same*
    healthy/known samples from one campaign.  Unknown-validation samples are
    validation-only.  Unknown-test samples are final-test-only.  Consumers
    must carry ``shared_validation_calibration`` into validation and reports.
    """

    healthy = str(healthy_label)
    known = _label_set(known_fault_labels)
    unknown_val = _label_set(unknown_validation_labels)
    unknown_test = _label_set(unknown_test_labels)
    if not healthy or not known:
        raise SampleSplitError("healthy_label and at least one known fault are required")
    role_sets = {
        "healthy": {healthy},
        "known_fault": known,
        "unknown_validation": unknown_val,
        "unknown_test": unknown_test,
    }
    for left_index, (left, left_labels) in enumerate(role_sets.items()):
        for right, right_labels in list(role_sets.items())[left_index + 1 :]:
            collision = left_labels & right_labels
            if collision:
                raise SampleSplitError(f"class roles {left}/{right} overlap: {sorted(collision)}")

    source_records = _records_by_id(records)
    known_labels = {healthy} | known
    folds: list[dict[str, object]] = []
    for index, train_stage in enumerate(CAMPAIGNS):
        valcal_stage = CAMPAIGNS[(index + 1) % len(CAMPAIGNS)]
        test_stage = CAMPAIGNS[(index + 2) % len(CAMPAIGNS)]
        stages = {
            "train": train_stage,
            "validation": valcal_stage,
            "calibration": valcal_stage,
            "test": test_stage,
        }
        selected: dict[str, list[dict[str, str]]] = {name: [] for name in stages}
        excluded: list[dict[str, str]] = []
        for item in source_records:
            stage, label = item["stage"], item["label"]
            destinations: tuple[str, ...]
            if label in known_labels:
                if stage == train_stage:
                    destinations = ("train",)
                elif stage == valcal_stage:
                    destinations = ("validation", "calibration")
                else:
                    destinations = ("test",)
            elif label in unknown_val:
                destinations = ("validation",) if stage == valcal_stage else ()
                reason = "UNKNOWN_VALIDATION_OUTSIDE_VALIDATION"
            elif label in unknown_test:
                destinations = ("test",) if stage == test_stage else ()
                reason = "UNKNOWN_TEST_OUTSIDE_FINAL_TEST"
            else:
                destinations = ()
                reason = "LABEL_NOT_IN_CLASS_ROLE"

            if destinations:
                for destination in destinations:
                    selected[destination].append(item)
            else:
                excluded.append({
                    "sample_id": item["sample_id"],
                    "label": label,
                    "stage": stage,
                    "source_file": item["source_file"],
                    "group_id": item["group_id"],
                    "reason": reason,
                })

        folds.append({
            "fold_id": f"train{train_stage}-valcal{valcal_stage}-test{test_stage}",
            "campaigns": stages,
            "group_key": "acquisition_stage_campaign",
            "shared_validation_calibration": True,
            "sample_ids": {
                name: [item["sample_id"] for item in members]
                for name, members in selected.items()
            },
            "group_ids": {
                name: sorted({item["group_id"] for item in members})
                for name, members in selected.items()
            },
            "source_files": {
                name: sorted({item["source_file"] for item in members})
                for name, members in selected.items()
            },
            "excluded": excluded,
            "limitations": [
                "T1/T2/T3 are path/stage codes, not verified physical motor identities.",
                "Each fold has only one campaign in test; two independent test campaigns per class are unavailable.",
                "Validation and calibration reuse the same healthy/known samples and are statistically dependent.",
                "Original source intervals and window overlap metadata are unavailable.",
            ],
        })
    return folds


def _compact_fold(fold: Mapping[str, object], records_by_id: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    ids_by_split = fold["sample_ids"]
    if not isinstance(ids_by_split, dict):
        raise SampleSplitError("fold sample_ids must be a split mapping")
    counts: dict[str, dict[str, int]] = {}
    group_counts: dict[str, dict[str, int]] = {}
    for split, sample_ids in ids_by_split.items():
        members = [records_by_id[sample_id] for sample_id in sample_ids]
        counts[split] = dict(sorted(Counter(str(item["label"]) for item in members).items()))
        labels = sorted(counts[split])
        group_counts[split] = {
            label: len({str(item["group_id"]) for item in members if str(item["label"]) == label})
            for label in labels
        }
    excluded = fold["excluded"]
    return {
        "fold_id": fold["fold_id"],
        "campaigns": fold["campaigns"],
        "group_key": fold["group_key"],
        "shared_validation_calibration": fold["shared_validation_calibration"],
        "counts_by_split_label": counts,
        "group_counts_by_split_label": group_counts,
        "group_ids": fold["group_ids"],
        "excluded_counts_by_reason": dict(sorted(Counter(str(item["reason"]) for item in excluded).items())),
        "excluded_count": len(excluded),
        "limitations": fold["limitations"],
    }


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize formal campaign-held-out class-role folds")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--healthy-label", default="8screws")
    parser.add_argument("--known", action="append", required=True, metavar="LABEL")
    parser.add_argument("--unknown-test", action="append", required=True, metavar="LABEL")
    parser.add_argument("--unknown-validation", action="append", default=[], metavar="LABEL")
    args = parser.parse_args(argv)

    data_root = args.data_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    if output_root == data_root or data_root in output_root.parents:
        raise SampleSplitError("output-root must stay outside the read-only formal data root")
    records, catalog = load_formal_catalog(data_root)
    folds = generate_campaign_folds(
        records,
        healthy_label=args.healthy_label,
        known_fault_labels=args.known,
        unknown_validation_labels=args.unknown_validation,
        unknown_test_labels=args.unknown_test,
    )
    by_id = {str(item["sample_id"]): item for item in records}
    result = {
        "schema_version": 1,
        "catalog": catalog,
        "class_roles": {
            "healthy": args.healthy_label,
            "known_faults": sorted(set(args.known)),
            "unknown_validation": sorted(set(args.unknown_validation)),
            "unknown_test": sorted(set(args.unknown_test)),
        },
        "folds": [_compact_fold(fold, by_id) for fold in folds],
        "note": "Full per-sample split manifests are created in the subsequent manifest phase.",
    }
    payload = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    destination = output_root / "campaign_split_summary.json"
    if destination.exists():
        if destination.read_bytes() != payload:
            raise SampleSplitError(f"refusing to change existing split summary: {destination}")
    else:
        output_root.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    print(json.dumps({
        "summary_path": str(destination),
        "dataset_fingerprint": catalog["dataset_fingerprint"],
        "sample_count": catalog["sample_count"],
        "fold_count": len(folds),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
