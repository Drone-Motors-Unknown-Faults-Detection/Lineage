"""Validate reproducible, group-separated fault-configuration test manifests.

``INVALID`` means a known leak or broken provenance and must stop a formal
run. ``INCOMPLETE`` means the split can be inspected but cannot support the
full independent-test claim. The latter is expected for scarce acquisition
groups; it must remain visible in exploratory results.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any


SPLITS = ("train", "validation", "calibration", "test")
MIN_TEST_SAMPLES_PER_CLASS = 30
MIN_TEST_GROUPS_PER_CLASS = 2
INVALID_CODES = frozenset(
    {
        "TEST_GROUP_LEAKAGE",
        "TEST_WINDOW_OVERLAP_LEAKAGE",
        "UNKNOWN_LABEL_LEAKAGE",
        "TEST_MANIFEST_MISMATCH",
        "TEST_USED_FOR_SELECTION",
        "TEST_EXCLUSION_UNDECLARED",
        "TEST_NOT_REPRODUCIBLE",
    }
)
INCOMPLETE_CODES = frozenset(
    {
        "TEST_MISSING_HEALTHY",
        "TEST_MISSING_KNOWN_CLASS",
        "TEST_MISSING_UNKNOWN_CLASS",
        "TEST_INSUFFICIENT_SAMPLES",
        "TEST_INSUFFICIENT_GROUPS",
        "TEST_CONDITION_COVERAGE_INCOMPLETE",
        "LABEL_SEMANTICS_MISMATCH",
        "EVENT_BOUNDARY_INCOMPLETE",
    }
)
ERROR_CODES = INVALID_CODES | INCOMPLETE_CODES


class SplitValidationError(ValueError):
    """An INVALID split cannot enter a formal result table."""

    def __init__(self, report: Mapping[str, Any]) -> None:
        self.report = dict(report)
        super().__init__("INVALID split manifest: " + ", ".join(self.report.get("error_codes", [])))


def compute_manifest_checksum(manifest: Mapping[str, Any]) -> str:
    """Hash all manifest content except the checksum itself, including validator.

    The writer first embeds a report from ``verify_checksum=False``, then
    stores this digest. A changed role, sample, provenance field, or embedded
    validation report necessarily changes the checksum.
    """

    content = {key: value for key, value in manifest.items() if key != "manifest_checksum"}
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _interval(value: object) -> tuple[float, float] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        start, end = value.get("start"), value.get("end")
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        start, end = value
    else:
        raise ValueError("source_interval must be [start,end] or {start,end}")
    start, end = float(start), float(end)
    if not math.isfinite(start) or not math.isfinite(end) or not start < end:
        raise ValueError("source_interval must have start < end")
    return start, end


def validate_split_manifest(
    manifest: Mapping[str, Any],
    *,
    paired_test_ids: Iterable[str] | None = None,
    paired_checksum: str | None = None,
    verify_checksum: bool = True,
) -> dict[str, Any]:
    """Return ``PASS``, ``INCOMPLETE``, or ``INVALID`` with stable error codes."""

    details: dict[str, list[str]] = defaultdict(list)
    warnings: list[str] = []

    def add(code: str, message: str) -> None:
        details[code].append(message)

    try:
        actual_checksum = compute_manifest_checksum(manifest)
    except (TypeError, ValueError, OverflowError) as error:
        actual_checksum = None
        add("TEST_NOT_REPRODUCIBLE", f"manifest is not canonical JSON: {error}")
    if verify_checksum and (not manifest.get("manifest_checksum") or manifest.get("manifest_checksum") != actual_checksum):
        add("TEST_NOT_REPRODUCIBLE", "manifest_checksum is missing or does not match canonical content")
    if not isinstance(manifest.get("schema_version"), int) or manifest.get("schema_version", 0) < 1:
        add("TEST_NOT_REPRODUCIBLE", "schema_version is missing or invalid")
    if not manifest.get("split_id") or not manifest.get("dataset_fingerprint"):
        add("TEST_NOT_REPRODUCIBLE", "split_id and dataset_fingerprint are required")

    roles = {
        "healthy": str(manifest.get("healthy_label") or ""),
        "known": tuple(manifest.get("known_fault_labels") or ()),
        "unknown_validation": tuple(manifest.get("unknown_validation_labels") or ()),
        "unknown_test": tuple(manifest.get("unknown_test_labels") or ()),
    }
    known = set(roles["known"])
    unknown_validation = set(roles["unknown_validation"])
    unknown_test = set(roles["unknown_test"])
    if not roles["healthy"] or not known:
        add("TEST_NOT_REPRODUCIBLE", "healthy and known-fault class roles are required")
    if known & unknown_validation or known & unknown_test or unknown_validation & unknown_test or roles["healthy"] in (known | unknown_validation | unknown_test):
        add("UNKNOWN_LABEL_LEAKAGE", "class-role label sets overlap")
    if len(roles["known"]) != len(known) or len(roles["unknown_validation"]) != len(unknown_validation) or len(roles["unknown_test"]) != len(unknown_test):
        add("TEST_NOT_REPRODUCIBLE", "class-role label lists contain duplicates")

    sample_ids = manifest.get("sample_ids") or {}
    if not isinstance(sample_ids, Mapping) or any(split not in sample_ids for split in SPLITS):
        add("TEST_NOT_REPRODUCIBLE", "sample_ids must list train, validation, calibration and test")
        sample_ids = {}
    split_sets: dict[str, set[str]] = {}
    for split in SPLITS:
        values = list(sample_ids.get(split, ()))
        if len(values) != len(set(values)):
            add("TEST_NOT_REPRODUCIBLE", f"duplicate sample IDs within {split}")
        split_sets[split] = {str(value) for value in values}
    shared_val_cal = bool(manifest.get("shared_validation_calibration", False))
    fixed_none = (manifest.get("schema_version") == 2 and
                  manifest.get("protocol_version") == "fixed_methods_motor_calibration_v1")
    if fixed_none:
        if (manifest.get("selection_policy") != "none" or split_sets["validation"] or
                manifest.get("selection_sample_ids") != [] or shared_val_cal or
                manifest.get("unknown_validation_labels") or "global_winner" in manifest or
                "selected_representation" in manifest):
            add("TEST_USED_FOR_SELECTION", "fixed no-selection requires empty validation/selection and no shared role/winner")
        motors = manifest.get("motor_roles", {})
        if set(motors) != {"train", "calibration", "test"} or len(set(motors.values())) != 3:
            add("TEST_GROUP_LEAKAGE", "fixed protocol requires three distinct motor roles")
        for split in ("train", "calibration", "test"):
            assigned = set(sample_ids.get(split, ()))
            if any(r.get("t_code") != motors.get(split) for r in manifest.get("records", ())
                   if r.get("sample_id") in assigned):
                add("TEST_GROUP_LEAKAGE", f"{split} record motor differs from fixed motor role")
    elif not split_sets["validation"]:
        add("TEST_NOT_REPRODUCIBLE", "legacy selection protocol requires validation; only explicit fixed v1 is N/A")
    for left_index, left in enumerate(SPLITS):
        for right in SPLITS[left_index + 1 :]:
            common = split_sets[left] & split_sets[right]
            if common and not (shared_val_cal and {left, right} == {"validation", "calibration"}):
                add("TEST_GROUP_LEAKAGE", f"{left}/{right} share {len(common)} sample IDs")
    if shared_val_cal:
        add("TEST_INSUFFICIENT_GROUPS", "validation and calibration are explicitly shared; independent four-way split unavailable")

    selected_ids = set().union(*split_sets.values())
    raw_records = list(manifest.get("records") or ())
    records: dict[str, Mapping[str, Any]] = {}
    for record in raw_records:
        if not isinstance(record, Mapping) or not record.get("sample_id"):
            add("TEST_NOT_REPRODUCIBLE", "record missing sample_id")
            continue
        sample_id = str(record["sample_id"])
        if sample_id in records:
            add("TEST_NOT_REPRODUCIBLE", f"duplicate sample record {sample_id}")
        records[sample_id] = record
        if not record.get("group_id") or not record.get("source_file") or not record.get("label"):
            add("TEST_NOT_REPRODUCIBLE", f"record {sample_id} lacks label/group_id/source_file")
    if set(records) != selected_ids:
        add("TEST_NOT_REPRODUCIBLE", f"sample_ids/records differ: missing_records={len(selected_ids - set(records))}, unassigned_records={len(set(records) - selected_ids)}")

    excluded = list(manifest.get("excluded") or ())
    excluded_ids: set[str] = set()
    for item in excluded:
        if not isinstance(item, Mapping) or not item.get("sample_id") or not item.get("reason"):
            add("TEST_EXCLUSION_UNDECLARED", "excluded sample needs sample_id and reason")
            continue
        sample_id = str(item["sample_id"])
        if sample_id in excluded_ids:
            add("TEST_EXCLUSION_UNDECLARED", f"duplicate excluded sample {sample_id}")
        excluded_ids.add(sample_id)
    if selected_ids & excluded_ids:
        add("TEST_EXCLUSION_UNDECLARED", f"{len(selected_ids & excluded_ids)} samples are selected and excluded")
    expected_total = manifest.get("dataset_sample_count")
    if not isinstance(expected_total, int) or expected_total < 1:
        add("TEST_NOT_REPRODUCIBLE", "dataset_sample_count must be a positive integer")
    elif len(selected_ids | excluded_ids) != expected_total:
        add("TEST_EXCLUSION_UNDECLARED", f"inventory has {expected_total} samples but selected+declared-excluded has {len(selected_ids | excluded_ids)}")

    source_files = list(manifest.get("source_files") or ())
    source_digests: dict[str, str] = {}
    if not source_files:
        add("TEST_NOT_REPRODUCIBLE", "source_files inventory is missing")
    else:
        source_names: set[str] = set()
        source_count = 0
        for item in source_files:
            if not isinstance(item, Mapping):
                add("TEST_NOT_REPRODUCIBLE", "source_files entry is malformed")
                continue
            source_name = str(item.get("source_file") or item.get("path") or "")
            rows = item.get("rows")
            if not source_name or not isinstance(rows, int) or rows < 0 or source_name in source_names:
                add("TEST_NOT_REPRODUCIBLE", f"source_files entry has invalid/duplicate path or rows: {source_name}")
                continue
            source_names.add(source_name)
            source_count += rows
            digest = str(item.get("source_sha256", ""))
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                add("TEST_NOT_REPRODUCIBLE", f"source checksum missing or malformed: {source_name}")
            else:
                source_digests[source_name] = digest
        if isinstance(expected_total, int) and source_count != expected_total:
            add("TEST_NOT_REPRODUCIBLE", f"source file row sum {source_count} differs from dataset_sample_count {expected_total}")
        unlisted = {str(record.get("source_file")) for record in records.values()} - source_names
        if unlisted:
            add("TEST_NOT_REPRODUCIBLE", f"{len(unlisted)} selected source files absent from inventory")
        for sample_id, record in records.items():
            declared = record.get("source_sha256")
            if declared is not None and declared != source_digests.get(str(record.get("source_file"))):
                add("TEST_NOT_REPRODUCIBLE", f"{sample_id}: record source checksum differs from inventory")

    record_splits: dict[str, set[str]] = defaultdict(set)
    for split, ids in split_sets.items():
        for sample_id in ids:
            record_splits[sample_id].add(split)
    group_splits: dict[str, set[str]] = defaultdict(set)
    campaign_splits: dict[str, set[str]] = defaultdict(set)
    source_splits: dict[str, set[str]] = defaultdict(set)
    source_digest_splits: dict[str, set[str]] = defaultdict(set)
    raw_identity_splits: dict[str, set[str]] = defaultdict(set)
    intervals: dict[str, list[tuple[float, float, str, str]]] = defaultdict(list)
    for sample_id, record in records.items():
        for split in record_splits.get(sample_id, ()):
            group_splits[str(record.get("group_id"))].add(split)
            if record.get("stage") is not None:
                campaign_splits[str(record["stage"])].add(split)
            source_splits[str(record.get("source_file"))].add(split)
            source_digest = source_digests.get(str(record.get("source_file")))
            if source_digest:
                source_digest_splits[source_digest].add(split)
            # Check all known aliases, not just the first name. Equal SHA binds
            # renamed recordings; equal IDs still bind records missing a SHA.
            raw_keys = [f"{field}:{record[field]}" for field in
                        ("raw_source_sha256", "raw_source_id", "raw_source_file") if record.get(field)]
            for raw_key in raw_keys:
                raw_identity_splits[raw_key].add(split)
            try:
                bounds = _interval(record.get("source_interval"))
            except (TypeError, ValueError, OverflowError) as error:
                add("TEST_NOT_REPRODUCIBLE", f"{sample_id}: {error}")
                bounds = None
            if bounds is not None:
                interval_keys = raw_keys or [f"source:{source_digest or record.get('source_file')}"]
                for raw_key in interval_keys:
                    intervals[raw_key].append((bounds[0], bounds[1], split, sample_id))
    assignments_to_check = [("group", group_splits), ("source_file", source_splits),
                            ("source_sha256", source_digest_splits), ("raw_identity", raw_identity_splits)]
    if manifest.get("group_key") == "acquisition_stage_campaign":
        assignments_to_check.append(("campaign", campaign_splits))
    for kind, assignments in assignments_to_check:
        for value, splits in assignments.items():
            if len(splits) > 1 and not (shared_val_cal and splits == {"validation", "calibration"}):
                add("TEST_GROUP_LEAKAGE", f"{kind} {value} spans {','.join(sorted(splits))}")
    for raw_source, windows in intervals.items():
        windows.sort(key=lambda item: (item[0], item[1]))
        for index, left in enumerate(windows):
            for right in windows[index + 1 :]:
                if right[0] >= left[1]:
                    break
                if left[2] != right[2] and not (shared_val_cal and {left[2], right[2]} == {"validation", "calibration"}):
                    add("TEST_WINDOW_OVERLAP_LEAKAGE", f"{raw_source}: {left[3]}({left[2]}) overlaps {right[3]}({right[2]})")
                    break

    for split in ("train", "validation", "calibration"):
        for sample_id in split_sets[split]:
            label = records.get(sample_id, {}).get("label")
            if label in unknown_test or (split != "validation" and label in unknown_validation):
                add("UNKNOWN_LABEL_LEAKAGE", f"{sample_id}: {label} enters {split}")
    for split, ids in split_sets.items():
        allowed = known | {roles["healthy"]}
        allowed |= unknown_test if split == "test" else unknown_validation if split == "validation" else set()
        if any(records.get(sid, {}).get("label") not in allowed for sid in ids):
            add("UNKNOWN_LABEL_LEAKAGE", f"undeclared class enters {split}")
    for kind in ("fit_sample_ids", "reference_sample_ids"):
        inputs = {str(value) for value in manifest.get(kind) or ()}
        test_used = inputs & split_sets["test"]
        unknown_used = {sample_id for sample_id in inputs if records.get(sample_id, {}).get("label") in (unknown_test | unknown_validation)}
        if test_used or unknown_used:
            add("UNKNOWN_LABEL_LEAKAGE", f"{kind} includes {len(test_used)} test and {len(unknown_used)} unknown-role samples")
        if inputs - split_sets["train"]:
            add("TEST_GROUP_LEAKAGE", f"{kind} contains samples outside train")
    if set(manifest.get("calibration_sample_ids", ())) - split_sets["calibration"]:
        add("UNKNOWN_LABEL_LEAKAGE", "threshold inputs contain samples outside calibration")
    if any(records.get(sid, {}).get("label") in unknown_validation for sid in split_sets["test"]):
        add("UNKNOWN_LABEL_LEAKAGE", "unknown-validation label enters final test")
    selection_ids = {str(value) for value in manifest.get("selection_sample_ids") or ()}
    if selection_ids & split_sets["test"]:
        add("TEST_USED_FOR_SELECTION", f"{len(selection_ids & split_sets['test'])} test samples used for selection")
    if paired_test_ids is not None and split_sets["test"] != {str(value) for value in paired_test_ids}:
        add("TEST_MANIFEST_MISMATCH", "paired methods have different test sample IDs")
    if paired_checksum is not None and manifest.get("manifest_checksum") != paired_checksum:
        add("TEST_MANIFEST_MISMATCH", "paired methods have different manifest checksums")

    def labels_in(split: str) -> set[str]:
        return {str(records[sample_id].get("label")) for sample_id in split_sets[split] if sample_id in records}

    if roles["healthy"] not in labels_in("test"):
        add("TEST_MISSING_HEALTHY", "healthy label is absent from test")
    for split in ("train", "calibration"):
        if roles["healthy"] not in labels_in(split):
            add("TEST_MISSING_HEALTHY", f"healthy label is absent from {split}")
    for label in roles["known"]:
        for split in ("train", "calibration", "test"):
            if label not in labels_in(split):
                add("TEST_MISSING_KNOWN_CLASS", f"{label} is absent from {split}")
    for label in roles["unknown_test"]:
        if label not in labels_in("test"):
            add("TEST_MISSING_UNKNOWN_CLASS", f"{label} is absent from test")
    for label in roles["unknown_validation"]:
        if label not in labels_in("validation"):
            add("TEST_MISSING_UNKNOWN_CLASS", f"unknown-validation label {label} is absent from validation")
    if not roles["unknown_test"] and len(roles["known"]) != 9:
        add("TEST_MISSING_UNKNOWN_CLASS", "unknown-test roles are empty outside the N=9 closed-set baseline")

    test_by_label: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for sample_id in split_sets["test"]:
        if sample_id in records:
            test_by_label[str(records[sample_id].get("label"))].append(records[sample_id])
    expected_rpms = {str(rpm) for rpm in manifest.get("expected_rpms") or ()}
    for label in (roles["healthy"], *roles["known"], *roles["unknown_test"]):
        items = test_by_label.get(label, [])
        if items and len(items) < MIN_TEST_SAMPLES_PER_CLASS:
            add("TEST_INSUFFICIENT_SAMPLES", f"{label}: {len(items)} test samples; minimum {MIN_TEST_SAMPLES_PER_CLASS}")
        group_field = "stage" if manifest.get("group_key") == "acquisition_stage_campaign" else "group_id"
        groups = {str(item.get(group_field)) for item in items if item.get(group_field) is not None}
        if items and len(groups) < MIN_TEST_GROUPS_PER_CLASS:
            add("TEST_INSUFFICIENT_GROUPS", f"{label}: {len(groups)} test groups; minimum {MIN_TEST_GROUPS_PER_CLASS}")
        if items and expected_rpms:
            observed = {str(item.get("rpm")) for item in items}
            missing = expected_rpms - observed
            if missing:
                add("TEST_CONDITION_COVERAGE_INCOMPLETE", f"{label}: missing test RPMs {','.join(sorted(missing))}")
    group_key = str(manifest.get("group_key") or manifest.get("group_key_kind") or "")
    if group_key in {"source_file", "raw_file"} and not manifest.get("independent_acquisition_verified", False):
        add("TEST_INSUFFICIENT_GROUPS", "file groups do not establish independent acquisition campaigns")
    if any(record.get("source_interval") is None for record in records.values()):
        warnings.append("source intervals unavailable for some samples; overlap cannot be excluded beyond group boundaries")
    for label, expected in (manifest.get("expected_counts", {}).get("test", {})).items():
        actual = len(test_by_label.get(label, []))
        if actual != expected:
            add("TEST_INSUFFICIENT_SAMPLES", f"{label}: expected {expected} final-test rows, observed {actual}")
    if manifest.get("claimed_label_semantics") != "configuration":
        add("LABEL_SEMANTICS_MISMATCH", "current screw labels support configuration, not verified physical fault type")
    if manifest.get("requested_event_metrics"):
        lacking = [
            item for items in test_by_label.values() for item in items
            if not item.get("event_id") or not item.get("event_boundary")
        ]
        if lacking:
            add("EVENT_BOUNDARY_INCOMPLETE", f"{len(lacking)} test records lack event IDs/boundaries")

    codes = sorted(details)
    status = "INVALID" if any(code in INVALID_CODES for code in codes) else "INCOMPLETE" if codes else "PASS"
    return {
        "status": status,
        "error_codes": codes,
        "details": {code: sorted(set(details[code])) for code in codes},
        "warnings": warnings,
        "test_sample_count": len(split_sets["test"]),
        "test_group_count": len({str(item.get("group_id")) for items in test_by_label.values() for item in items}),
    }


def assert_valid_for_formal(manifest: Mapping[str, Any], *, allow_incomplete: bool = False, **kwargs: Any) -> dict[str, Any]:
    """Formal runs require PASS; exploratory runs must opt into INCOMPLETE."""

    report = validate_split_manifest(manifest, **kwargs)
    if report["status"] == "INVALID":
        raise SplitValidationError(report)
    if report["status"] == "INCOMPLETE" and not allow_incomplete:
        raise ValueError("INCOMPLETE split requires explicit exploratory mode")
    return report
