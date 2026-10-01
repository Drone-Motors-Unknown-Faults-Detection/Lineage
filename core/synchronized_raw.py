"""Configured raw parser and shared-row windows; never compress the time axis.

Field mapping is informed by Ancestor Step1 at 1ef4a891 (see evidence registry).
No legacy code is imported; physical claims remain attested, not authenticated.
Separate channel files are deliberately unsupported without a clock bridge.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv
import numpy as np
import pandas as pd
from core.fault_type_final_guard import digest
from core.formal_data import _sha256_file

CHANNELS = ("current", "x", "y", "z", "delta_t")
ATTESTED = {"operator_attested", "file_verified", "fixture_attested"}


@dataclass
class RawRecording:
    path: Path
    sha256: str
    config: dict
    values: np.ndarray
    sample_indices: np.ndarray
    timestamps: np.ndarray | None
    original_lines_1_based: np.ndarray


@dataclass
class TimebaseAudit:
    summary: dict
    bad_edges: np.ndarray


@dataclass
class QualityMask:
    bad: np.ndarray
    reasons: dict
    config_checksum: str


@dataclass
class AlignedWindow:
    window_id: str
    source_interval: tuple[int, int]
    values: np.ndarray
    metadata: dict


def read_recording(path: Path | str, config: dict) -> RawRecording:
    path = Path(path).resolve()
    parser = config["parser"]
    if parser.get("layout") != "single_file_shared_rows":
        raise ValueError("separate-channel files require a verified clock/offset bridge; truncation is forbidden")
    header = parser.get("header_row_0_based")
    if isinstance(header, bool) or not isinstance(header, int) or header < 0:
        raise ValueError("explicit zero-based header row required; do not guess header=22")
    if parser.get("delimiter") not in {",", "\t"}:
        raise ValueError("explicit comma/tab delimiter required")
    with path.open(encoding=parser.get("encoding", "utf-8-sig"), newline="") as source:
        for _ in range(header):
            next(source)
        parsed = csv.reader(source, delimiter=parser["delimiter"])
        previous_line = 0
        for fields in parsed:
            if parsed.line_num != previous_line+1 or len(fields) != len(parser["expected_columns"]):
                raise ValueError("blank/multiline/ragged rows require a separate explicit parser contract")
            previous_line = parsed.line_num
    # Disable blank-line skipping so original row indices cannot shift silently.
    frame = pd.read_csv(path, sep=parser["delimiter"], header=header,
                        encoding=parser.get("encoding", "utf-8-sig"), skip_blank_lines=False)
    if list(frame.columns) != parser["expected_columns"] or frame.columns.duplicated().any():
        raise ValueError("header/column contract mismatch; confirm actual raw format")
    if len(frame) != config["raw_sample_count"] or not len(frame):
        raise ValueError("actual raw sample count differs from manifest")
    mapping = parser["channels"]
    columns = []
    for key in CHANNELS:
        if key == "delta_t" and key not in mapping:
            column = pd.to_numeric(frame[mapping["motor_temp"]], errors="raise") - pd.to_numeric(frame[mapping["room_temp"]], errors="raise")
        else:
            column = pd.to_numeric(frame[mapping[key]], errors="raise")
        columns.append(column.to_numpy(float))
    index_col = parser.get("sample_index_column")
    indices = pd.to_numeric(frame[index_col], errors="raise").to_numpy(float) if index_col else np.arange(len(frame), dtype=float)
    if not np.isfinite(indices).all() or np.any(indices != np.floor(indices)):
        raise ValueError("sample index must be finite integers")
    time_col = parser.get("time_column")
    timestamps = None
    if time_col:
        if parser.get("time_semantics") != "relative_seconds":
            raise ValueError("time field meaning must be confirmed; X_Value is not assumed time")
        timestamps = pd.to_numeric(frame[time_col], errors="raise").to_numpy(float)
    for key in ("recording_id", "motor_id", "session_id", "run_id"):
        if not config.get(key):
            raise ValueError(f"missing recording identity: {key}")
    return RawRecording(path, _sha256_file(path), config, np.column_stack(columns), indices,
                        timestamps, np.arange(len(frame)) + header + 2)


def audit_timebase(recording: RawRecording, *, relative_tolerance: float = .001) -> TimebaseAudit:
    cfg = recording.config
    fs = cfg.get("sample_rate_hz")
    if fs is not None and (not np.isfinite(fs) or fs <= 0):
        raise ValueError("invalid sample rate")
    index_edges = np.diff(recording.sample_indices)
    bad = index_edges != 1
    time = recording.timestamps
    delta = np.diff(time) if time is not None else None
    if delta is not None:
        bad |= ~np.isfinite(delta) | (delta <= 0)
        if fs:
            bad |= ~np.isclose(delta, 1/fs, rtol=relative_tolerance, atol=1e-12)
    evidence = cfg.get("evidence", {})
    fs_attested = evidence.get("sample_rate", {}).get("level") in ATTESTED and bool(evidence.get("sample_rate", {}).get("reference"))
    sync_attested = evidence.get("alignment", {}).get("level") in ATTESTED and bool(evidence.get("alignment", {}).get("reference"))
    uniform = bool(fs and fs_attested and not np.any(bad) and (time is None or np.isfinite(time).all()))
    verified = uniform and sync_attested
    return TimebaseAudit({"sample_count_actual": len(recording.values), "raw_sha256": recording.sha256,
        "fs_hz": fs, "fs_evidence": evidence.get("sample_rate", {"level": "unknown"}),
        "alignment_evidence": evidence.get("alignment", {"level": "unknown"}),
        "bad_edge_indices": np.flatnonzero(bad).tolist(),
        "timestamp_duplicates": int(np.sum(delta == 0)) if delta is not None else None,
        "timestamp_reversals": int(np.sum(delta < 0)) if delta is not None else None,
        "max_relative_jitter": float(np.max(np.abs(delta*fs-1))) if delta is not None and fs and np.isfinite(delta).all() and len(delta) else None,
        "uniform_sampling_attested": uniform, "physical_time_alignment_verified": verified,
        "time_scope": "recorded_relative_seconds" if time is not None else "relative_sample_time" if verified else "unknown",
        "absolute_acquisition_time_verified": False,
        "status": "ATTESTED_SHARED_ROW_ALIGNMENT" if verified else "INCOMPLETE",
        "scope": "synthetic_engineering" if cfg.get("synthetic") else "operator_attested_measurement",
        "limitations": ["Shared rows plus attestations do not independently authenticate DAQ hardware.",
                        "No interpolation, resampling, channel truncation or inter-recording concatenation."]}, bad)


def quality_mask(recording: RawRecording, config: dict, *, trained_quality_model: dict | None = None) -> QualityMask:
    x = recording.values
    reasons = {"nonfinite": ~np.isfinite(x)}
    bounds = config.get("absolute_bounds", {})
    bound_bad = np.zeros(x.shape, bool)
    for j, name in enumerate(CHANNELS):
        if name in bounds:
            lower, upper = bounds[name]
            if lower >= upper:
                raise ValueError("invalid configured absolute bound")
            bound_bad[:, j] = (x[:, j] < lower) | (x[:, j] > upper)
    reasons["fixed_bounds"] = bound_bad
    if trained_quality_model is not None:
        if trained_quality_model.get("fit_partition") != "train" or not trained_quality_model.get("fit_ids"):
            raise ValueError("estimated quality thresholds require train-only fit audit")
        lower = np.asarray(trained_quality_model["lower"], float)
        upper = np.asarray(trained_quality_model["upper"], float)
        if lower.shape != (5,) or upper.shape != (5,):
            raise ValueError("quality model must bind five-channel bounds")
        reasons["train_fitted_bounds"] = (x < lower) | (x > upper)
    bad = np.logical_or.reduce(list(reasons.values()))
    return QualityMask(bad, {name: np.argwhere(mask).tolist() for name, mask in reasons.items()},
                       digest({"rules": config, "trained_quality_model": trained_quality_model}))


def make_windows(recording: RawRecording, audit: TimebaseAudit, quality: QualityMask, settings: dict) -> tuple[list[AlignedWindow], list[dict]]:
    length, stride = settings["length"], settings["stride"]
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in (length, stride)):
        raise ValueError("positive integer length/stride required")
    if settings.get("gap_rule") != "reject" or settings.get("bad_point_rule") != "reject":
        raise ValueError("only explicit reject rules supported; no hidden interpolation/zero fill")
    accepted, rejected = [], []
    for start in range(0, len(recording.values)-length+1, stride):
        end = start + length
        reason = []
        if np.any(audit.bad_edges[start:end-1]): reason.append("time_gap_or_clock_error")
        if np.any(quality.bad[start:end]): reason.append("bad_point")
        window_id = digest([recording.sha256, recording.config["recording_id"], start, end, settings, quality.config_checksum])
        meta = {"window_id": window_id, "source_interval": [start, end], "sample_index_first": int(recording.sample_indices[start]),
            "original_line_first_1_based": int(recording.original_lines_1_based[start]),
            "raw_source_sha256": recording.sha256, "raw_sample_count": len(recording.values),
            "physical_time_alignment_verified": audit.summary["physical_time_alignment_verified"],
            "sample_rate_hz": audit.summary["fs_hz"], "time_scope": audit.summary["time_scope"],
            "relative_start_seconds": float(recording.timestamps[start]) if recording.timestamps is not None and np.isfinite(recording.timestamps[start]) else start/audit.summary["fs_hz"] if audit.summary["physical_time_alignment_verified"] else None,
            "quality_checksum": quality.config_checksum, "window_settings": settings, "bad_point_count": int(quality.bad[start:end].sum()),
            "synthetic": bool(recording.config.get("synthetic"))}
        if reason: rejected.append({**meta, "reasons": reason})
        else: accepted.append(AlignedWindow(window_id, (start, end), recording.values[start:end].copy(), meta))
    return accepted, rejected
