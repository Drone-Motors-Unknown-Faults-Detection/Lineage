"""Exposure-bound final-test eligibility; no metadata-only claim of reliability.

Checksums detect recorded exposure/copies. They cannot authenticate physical
hardware claims: those require acquisition attestations and external review.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from core.formal_data import _sha256_file


class FinalTestBlocked(ValueError):
    pass


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def numeric_row_digest(row) -> str:
    # Tolerate ordinary CSV re-serialization, not arbitrary transformations.
    return hashlib.sha256("|".join(format(float(v), ".12g") for v in row).encode()).hexdigest()


def seal(value: dict, key: str) -> dict:
    result = {k: v for k, v in value.items() if k != key}
    result[key] = digest(result)
    return result


def verify_seal(value: dict, key: str) -> None:
    if value.get(key) != digest({k: v for k, v in value.items() if k != key}):
        raise FinalTestBlocked(f"{key} mismatch")


def build_exposure_ledger(records: list[dict], pools, *, test_ids: set[str], evidence: list[dict]) -> dict:
    if test_ids != {r["sample_id"] for r in records}:
        raise ValueError("expected exact full-catalog historical test coverage")
    values = pools.load(records)
    files = {r["source_file"]: r["source_sha256"] for r in records}
    return seal({"schema_version": 1, "historical_test_sample_count": len(test_ids),
        "files": files, "numeric_row_digests": sorted({numeric_row_digest(row) for row in values}),
        "sample_ids": sorted(test_ids), "motor_ids": sorted({r["t_code"] for r in records}),
        "raw_recording_sha256": [], "sessions": [], "runs": [], "evidence": evidence,
        "limitation": "All catalog rows exposed in historical final-test rotations; original raw session/recording IDs unknown."}, "ledger_checksum")


def _safe_file(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if root not in path.parents or not path.is_file():
        raise FinalTestBlocked("missing file or source path outside incoming root")
    return path


def record_final_exposure(ledger: dict, bundle: dict, *, evaluation_id: str) -> dict:
    """Append history BEFORE prediction, even if evaluation later fails.

    Caller must persist returned sealed ledger durably. A failed/retried test
    remains exposed; it may be resumed as a recorded evaluation, never fresh.
    """
    verify_seal(ledger, "ledger_checksum"); verify_seal(bundle, "data_version_checksum")
    if not evaluation_id:
        raise FinalTestBlocked("evaluation ID required")
    result = json.loads(json.dumps(ledger))
    records = bundle["records"]
    result["previous_ledger_checksum"] = ledger["ledger_checksum"]
    for key, field in (("numeric_row_digests", "numeric_row_digest"), ("sample_ids", "sample_id"),
                       ("motor_ids", "motor_id"), ("sessions", "session_id"), ("runs", "run_id"),
                       ("raw_recording_sha256", "raw_source_sha256")):
        result[key] = sorted(set(result.get(key, [])) | {str(r[field]) for r in records})
    result.setdefault("files", {}).update({f"{evaluation_id}:{r.get('feature_source', r['sample_id'])}": r["source_sha256"] for r in records})
    result.setdefault("evaluations", []).append({"evaluation_id": evaluation_id,
        "data_version_checksum": bundle["data_version_checksum"], "registered_before_prediction": True,
        "status": "exposed_even_if_later_evaluation_fails"})
    return seal(result, "ledger_checksum")


def ingest(root: Path | str, manifest: dict) -> dict:
    """Verify incoming files and row metadata; NEVER write/overwrite data.

    An input is evidence of a declared new acquisition, not automatic proof of
    the operator's physical claims. All acquisition facts carry attestations.
    """
    root = Path(root).resolve()
    verify_seal(manifest, "manifest_checksum")
    rows = []
    for source in manifest["feature_files"]:
        path = _safe_file(root, source["path"])
        if _sha256_file(path) != source["sha256"]:
            raise FinalTestBlocked("incoming feature checksum mismatch")
        frame = pd.read_csv(path)
        if frame.shape[1] != 105 or list(frame.select_dtypes(include="number").columns) != list(frame.columns):
            raise FinalTestBlocked("105 numeric features required")
        values = frame.to_numpy(float)
        if not np.isfinite(values).all():
            raise FinalTestBlocked("nonfinite feature values")
        metadata = source["windows"]
        if sorted(item["row_index"] for item in metadata) != list(range(len(values))):
            raise FinalTestBlocked("window metadata must cover each feature row exactly once")
        for item in metadata:
            row = dict(item)
            for key in ("motor_id", "session_id", "run_id", "label", "rpm", "acquisition_timestamp", "attestation"):
                if not row.get(key):
                    raise FinalTestBlocked(f"missing acquisition fact: {key}")
            stamp = datetime.fromisoformat(row["acquisition_timestamp"])
            if stamp.tzinfo is None:
                raise FinalTestBlocked("acquisition timestamp must carry timezone")
            raw_path = _safe_file(root, row["raw_source_file"])
            actual_raw_sha = _sha256_file(raw_path)
            if actual_raw_sha != row["raw_source_sha256"]:
                raise FinalTestBlocked("raw source checksum mismatch")
            start, end = row["source_interval"]
            if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                raise FinalTestBlocked("raw interval must be nonempty integer [start,end)")
            if row.get("raw_sample_count", 0) < end or row.get("sample_rate_hz", 0) <= 0:
                raise FinalTestBlocked("raw interval exceeds declared recording or invalid sampling rate")
            if row.get("physical_time_alignment_verified") is not True:
                raise FinalTestBlocked("cross-channel alignment must be verified by acquisition/extraction evidence")
            row.update({"source_sha256": source["sha256"], "feature_source": source["path"],
                "numeric_row_digest": numeric_row_digest(values[row["row_index"]]),
                "sample_id": digest([source["sha256"], row["row_index"], row["raw_source_sha256"], start, end])})
            rows.append(row)
    if not rows or len({r["sample_id"] for r in rows}) != len(rows):
        raise FinalTestBlocked("empty or duplicate incoming sample IDs")
    required = ("feature_version", "extractor_sha256", "physical_contract", "acquisition_evidence")
    if any(not manifest.get(key) for key in required):
        raise FinalTestBlocked("feature generation and physical-contract evidence required")
    physical = manifest["physical_contract"]
    if any(not physical.get(key) for key in ("sensor_units", "orientation", "calibration", "mounting", "load")):
        raise FinalTestBlocked("physical contract has unknown required facts")
    return seal({"schema_version": 1, "feature_version": manifest["feature_version"],
        "extractor_sha256": manifest["extractor_sha256"], "physical_contract": physical,
        "acquisition_evidence": manifest["acquisition_evidence"], "records": rows,
        "input_manifest_checksum": manifest["manifest_checksum"],
        "qualification_scope": "verified bytes and declared acquisition provenance; hardware facts require human attestation review"}, "data_version_checksum")


def guard_final_test(bundle: dict, ledger: dict, locked: dict, *, claim: str,
                     training_records: list[dict] = ()) -> dict:
    for value, key in ((bundle, "data_version_checksum"), (ledger, "ledger_checksum"), (locked, "locked_checksum")):
        verify_seal(value, key)
    if locked.get("status") != "locked" or not locked.get("selection_input_ids") or not locked.get("training_artifact_sha256"):
        raise FinalTestBlocked("configuration must be locked with fit artifact before final evaluation")
    if locked.get("feature_version") != bundle.get("feature_version"):
        raise FinalTestBlocked("feature-version mismatch")
    if locked.get("exposure_ledger_checksum") != ledger["ledger_checksum"]:
        raise FinalTestBlocked("locked configuration references a different exposure history")
    if "training_records" not in locked:
        raise FinalTestBlocked("locked configuration must bind training/calibration provenance")
    training_records = [*locked["training_records"], *training_records]
    if claim not in {"new_session", "new_motor"}:
        raise FinalTestBlocked("independence claim must be explicit")
    exposed_files = set(ledger["files"].values()) | set(ledger.get("raw_recording_sha256", []))
    exposed_rows = set(ledger["numeric_row_digests"])
    # A fit/cal/selection sample need not have appeared in a prior final ledger.
    # Check bound training provenance as well: changed names/CSV serialization
    # cannot turn those inputs into an independent final test.
    training_files = {str(r[field]) for r in training_records for field in
                      ("source_sha256", "raw_source_sha256") if r.get(field)}
    training_rows = {str(r["numeric_row_digest"]) for r in training_records if r.get("numeric_row_digest")}
    training_ids = {str(r["sample_id"]) for r in training_records if r.get("sample_id")}
    selection_ids = {str(sid) for sid in locked["selection_input_ids"]}
    protected_ids = training_ids | selection_ids
    old_sessions = set(ledger.get("sessions", [])) | {str(r.get("session_id")) for r in training_records if r.get("session_id")}
    old_runs = set(ledger.get("runs", [])) | {str(r.get("run_id")) for r in training_records if r.get("run_id")}
    old_motors = set(ledger["motor_ids"]) | {str(r.get("motor_id")) for r in training_records if r.get("motor_id")}
    by_raw = {}
    raw_owners, run_owners = {}, {}
    for row in bundle["records"]:
        owner = (row["motor_id"], row["session_id"], row["run_id"])
        raw_key, run_key = row["raw_source_sha256"], row["run_id"]
        if raw_key in raw_owners and raw_owners[raw_key] != owner:
            raise FinalTestBlocked("same recording cannot be relabeled as multiple motors/sessions/runs")
        if run_key in run_owners and run_owners[run_key] != owner[:2]:
            raise FinalTestBlocked("run crosses declared motor/session owners")
        raw_owners[raw_key] = owner; run_owners[run_key] = owner[:2]
        if (str(row.get("sample_id")) in protected_ids
                or row["source_sha256"] in training_files
                or row["raw_source_sha256"] in training_files
                or row["numeric_row_digest"] in training_rows):
            raise FinalTestBlocked("training/selection source or duplicate feature row enters final test")
        if row["source_sha256"] in exposed_files or row["raw_source_sha256"] in exposed_files or row["numeric_row_digest"] in exposed_rows:
            raise FinalTestBlocked("previously exposed source / duplicate semantic feature row")
        if row["session_id"] in old_sessions or row["run_id"] in old_runs:
            raise FinalTestBlocked("acquisition group already used")
        if claim == "new_motor" and row["motor_id"] in old_motors:
            raise FinalTestBlocked("new session of existing motor is not a new-motor test")
        by_raw.setdefault(row["raw_source_sha256"], []).append(tuple(row["source_interval"]))
        for previous in training_records:
            if row["raw_source_sha256"] == previous.get("raw_source_sha256"):
                a, b = row["source_interval"]
                c, d = previous["source_interval"]
                if max(a, c) < min(b, d):
                    raise FinalTestBlocked("training/final raw-window overlap")
                raise FinalTestBlocked("same recording already used even without window overlap")
    for intervals in by_raw.values():
        ordered = sorted(intervals)
        if any(right[0] < left[1] for left, right in zip(ordered, ordered[1:])):
            raise FinalTestBlocked("overlapping final windows cannot count as independent test windows")
    expected = set(locked["known_labels"]) | set(locked["unknown_labels"])
    if {r["label"] for r in bundle["records"]} != expected:
        raise FinalTestBlocked("declared class coverage mismatch")
    for label in expected:
        members = [r for r in bundle["records"] if r["label"] == label]
        if len(members) < locked.get("minimum_test_samples_per_class", 30):
            raise FinalTestBlocked("insufficient final-test samples")
        key = "motor_id" if claim == "new_motor" else "session_id"
        if len({r[key] for r in members}) < locked.get("minimum_test_groups_per_class", 2):
            raise FinalTestBlocked("insufficient independently attested groups for claim")
        if set(locked.get("expected_rpms", [])) - {r["rpm"] for r in members}:
            raise FinalTestBlocked("final-test operating-condition coverage incomplete")
    return {"status": "ELIGIBLE_WITH_ATTESTED_PROVENANCE", "claim": claim,
        "data_version_checksum": bundle["data_version_checksum"], "locked_checksum": locked["locked_checksum"],
        "limitations": ["No checksum can independently authenticate hardware attestations.",
            "Eligibility is not proof of model reliability or a population-level confidence guarantee."]}
