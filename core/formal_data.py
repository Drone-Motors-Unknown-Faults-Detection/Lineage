"""Materialise the formal motor dataset from the read-only raw archive.

The public Lineage contract consumes 105-dimensional clean feature CSV files
under ``data/Step-*/myfeature``.  The local formal source is distributed as
nested ZIP archives instead of an extracted directory.  This module is the
small, deterministic adapter between those two contracts:

* Stage 1 and Stage 3 already contain clean feature CSVs; they are copied
  without changing their bytes.
* Stage 2 contains the five-channel, 10 kHz windows.  We reproduce the
  documented Ancestor Step 2 feature extraction (15 statistics per channel,
  plus ten harmonic FFT features for each vibration axis), then apply the
  observed feature-level 1.5-IQR clean rule used by the existing files.

The source is opened read-only.  ``materialize`` refuses an output directory
inside the source tree, and all paths are supplied by the caller or CLI; no
developer-specific path is embedded in the implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence
from zipfile import ZipFile, ZipInfo

import numpy as np
import pandas as pd
from scipy.fftpack import fft
from scipy.stats import kurtosis, skew


FEATURE_DIM = 105
STAGES = ("1", "2", "3")
MOTORS = ("T1", "T2", "T3")
RPMS = ("6000rpm", "8000rpm", "11000rpm")
CONFIGS = (
    "1screws",
    "2screws",
    "3screws",
    "3_14screws",
    "4screws",
    "4_146screws",
    "5screws",
    "6screws",
    "7screws",
    "8screws",
)
BASE_FREQUENCY = {"6000rpm": 100, "8000rpm": 133, "11000rpm": 183}
HARMONIC_BANDWIDTHS = (5, 8, 10, 12, 12, 12, 15, 15, 15, 15)
RAW_LENGTH = 10_000
SAMPLE_RATE = 10_000


def _feature_names() -> list[str]:
    stats = (
        "rms", "mean", "kurtosis", "std", "skewness", "peak2peak",
        "crest_indicator", "clearance_indicator", "shape_indicator",
        "impulse_indicator", "max", "min", "msa", "variance",
        "mean_amplitude",
    )
    names: list[str] = []
    offsets = {"Current": 0, "Vibration_X": 15, "Vibration_Y": 40, "Vibration_Z": 65, "Delta_T": 90}
    for prefix in ("Current", "Vibration_X", "Vibration_Y", "Vibration_Z", "Delta_T"):
        offset = offsets[prefix]
        for index, name in enumerate(stats, start=1):
            # These two names are lower-case in the historical CSV contract.
            label = name
            if prefix == "Current" and name in {"msa", "variance", "mean_amplitude"}:
                label = name
            names.append(f"{offset + index}-{prefix}-{label}")
        if prefix.startswith("Vibration"):
            axis = prefix.rsplit("_", 1)[-1]
            fft_offset = offset + 15
            names.extend(f"{fft_offset + i}-{prefix}-FFT{i}{axis}" for i in range(1, 11))
    if len(names) != FEATURE_DIM:
        raise AssertionError(f"feature-name contract produced {len(names)} columns")
    return names


FEATURE_NAMES = _feature_names()


class FormalDataError(RuntimeError):
    """Raised when the formal source cannot satisfy the Lineage contract."""


@dataclass(frozen=True)
class MaterializedFile:
    stage: str
    motor: str
    rpm: str
    config: str
    output: str
    source_member: str
    source_sha256: str
    rows_before_clean: int
    rows_after_clean: int
    columns: int
    mode: str


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _find_outer_archive(source_root: Path, stage: str) -> Path:
    expected = source_root / f"階段{stage}.zip"
    if expected.is_file():
        return expected
    candidates = sorted(source_root.glob(f"*{stage}*.zip"))
    if len(candidates) == 1:
        return candidates[0]
    raise FormalDataError(
        f"cannot locate the unique stage-{stage} archive under {source_root}"
    )


def discover_stage_archives(source_root: Path | str, stages: Iterable[str] = STAGES) -> dict[str, Path]:
    """Return stage archive paths after validating the read-only source root."""
    root = Path(source_root).expanduser().resolve()
    if not root.is_dir():
        raise FormalDataError(f"formal source root does not exist: {root}")
    return {stage: _find_outer_archive(root, stage) for stage in stages}


def _find_member(archive: ZipFile, *, suffix: str) -> str:
    matches = [name for name in archive.namelist() if name.lower().endswith(suffix.lower())]
    if len(matches) != 1:
        raise FormalDataError(
            f"expected one {suffix!r} member, found {len(matches)}: {matches[:5]}"
        )
    return matches[0]


def _safe_relative_member(name: str, prefix: str) -> Path:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise FormalDataError(f"unsafe archive member: {name}")
    try:
        return path.relative_to(prefix)
    except ValueError as exc:
        raise FormalDataError(f"unexpected member {name!r}; expected prefix {prefix!r}") from exc


def _ensure_output_not_source(source_root: Path, output_root: Path) -> None:
    source = source_root.resolve()
    output = output_root.resolve()
    if output == source or source in output.parents:
        raise FormalDataError(
            "refusing to write materialised data inside the read-only formal source"
        )


def _write_bytes(path: Path, data: bytes, *, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        if path.read_bytes() == data:
            return
        raise FormalDataError(f"output exists with different content (use --force): {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def _copy_clean_features(
    archive_path: Path,
    stage: str,
    output_root: Path,
    *,
    force: bool,
    selected_conditions: set[tuple[str, str, str]] | None,
) -> list[MaterializedFile]:
    records: list[MaterializedFile] = []
    with ZipFile(archive_path) as outer:
        member = _find_member(outer, suffix="myfeature.zip")
        with ZipFile(outer.open(member)) as features:
            for info in features.infolist():
                if info.is_dir() or not info.filename.endswith("_Group_feature_data_clean.csv"):
                    continue
                relative = _safe_relative_member(info.filename, "myfeature")
                parts = relative.parts
                if len(parts) != 4:
                    raise FormalDataError(f"unexpected feature path: {info.filename}")
                motor, rpm, config, _ = parts
                condition = (motor, rpm, config)
                if selected_conditions is not None and condition not in selected_conditions:
                    continue
                payload = features.read(info.filename)
                output = output_root / f"Step-{stage}" / "myfeature" / relative
                _write_bytes(output, payload, force=force)
                frame = pd.read_csv(io.BytesIO(payload))
                numeric = frame.select_dtypes(include="number")
                if numeric.shape[1] != FEATURE_DIM:
                    raise FormalDataError(f"{info.filename}: expected {FEATURE_DIM} numeric columns")
                records.append(
                    MaterializedFile(
                        stage=stage,
                        motor=motor,
                        rpm=rpm,
                        config=config,
                        output=str(output),
                        source_member=f"{archive_path.name}:{member}:{info.filename}",
                        source_sha256=_sha256_bytes(payload),
                        rows_before_clean=len(frame),
                        rows_after_clean=len(frame),
                        columns=numeric.shape[1],
                        mode="copied_clean_feature",
                    )
                )
    return records


def _statistical_features(frame: pd.DataFrame) -> np.ndarray:
    data = frame.to_numpy(dtype=float)
    features = np.zeros((data.shape[1], 15), dtype=float)
    for index in range(data.shape[1]):
        column = data[:, index]
        rms = np.sqrt(np.mean(column**2))
        mean_abs = np.mean(np.abs(column))
        features[index] = (
            rms,
            np.mean(column),
            kurtosis(column, fisher=False),
            np.std(column),
            skew(column),
            np.ptp(column),
            np.abs(np.max(column) / rms),
            np.abs(np.max(column) / np.mean(np.sqrt(np.abs(column) ** 2))),
            rms / mean_abs,
            np.abs(np.max(column) / mean_abs),
            np.max(column),
            np.min(column),
            np.mean(column**2),
            np.var(column),
            mean_abs,
        )
    return features


def _fft_features(frame: pd.DataFrame, rpm: str) -> np.ndarray:
    data = frame.to_numpy(dtype=float)
    raw_length = data.shape[0]
    half = raw_length // 2
    amplitudes = np.abs(fft(data, axis=0)) * 2 / raw_length
    amplitudes = amplitudes[:half, :]
    frequency = np.arange(half, dtype=float) * (SAMPLE_RATE / raw_length)
    result: list[np.ndarray] = []
    base = BASE_FREQUENCY[rpm]
    for harmonic, bandwidth in enumerate(HARMONIC_BANDWIDTHS, start=1):
        indices = np.where(
            (frequency >= base * harmonic - bandwidth)
            & (frequency <= base * harmonic + bandwidth)
        )[0]
        result.append(amplitudes[indices, :].max(axis=0) if len(indices) else np.zeros(data.shape[1]))
    return np.asarray(result).T


def _clean_feature_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Apply the historical feature-level 1.5-IQR row filter."""
    cleaned = frame.copy()
    for column in frame.columns:
        q1 = frame[column].quantile(0.25)
        q3 = frame[column].quantile(0.75)
        iqr = q3 - q1
        cleaned[column] = frame[column].where(
            frame[column].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        )
    before = len(cleaned)
    cleaned = cleaned.dropna()
    return cleaned, before


def _channel_key(filename: str) -> str | None:
    stem = Path(filename).stem
    for suffix, key in (
        ("_Acceleration_X_data", "x"),
        ("_Acceleration_Y_data", "y"),
        ("_Acceleration_Z_data", "z"),
        ("_X_data", "x"),
        ("_Y_data", "y"),
        ("_Z_data", "z"),
        ("_Current_data", "current"),
        ("_Delta_T_data", "delta_t"),
    ):
        if stem.endswith(suffix):
            return key
    return None


def _condition_from_member(name: str) -> tuple[str, str, str] | None:
    match = re.search(r"(?:^|/)\s*(T[123])/(\d+rpm)\.zip$", name)
    if not match:
        return None
    # The class is supplied by the files inside the condition archive.
    return match.group(1), match.group(2), ""


def _convert_condition(
    condition_archive: ZipFile,
    source_label: str,
    output_root: Path,
    motor: str,
    rpm: str,
    *,
    force: bool,
    selected_conditions: set[tuple[str, str, str]] | None,
) -> list[MaterializedFile]:
    records: list[MaterializedFile] = []
    by_config: dict[str, dict[str, ZipInfo]] = {}
    for info in condition_archive.infolist():
        if info.is_dir() or not info.filename.lower().endswith(".csv"):
            continue
        parts = Path(info.filename).parts
        if len(parts) < 2:
            continue
        config = parts[-2]
        channel = _channel_key(parts[-1])
        if channel:
            by_config.setdefault(config, {})[channel] = info

    for config in sorted(by_config):
        condition = (motor, rpm, config)
        if selected_conditions is not None and condition not in selected_conditions:
            continue
        channels = by_config[config]
        missing = {"current", "x", "y", "z", "delta_t"} - channels.keys()
        if missing:
            raise FormalDataError(f"{source_label}: {config} missing channels {sorted(missing)}")
        frames = {
            key: pd.read_csv(condition_archive.open(info), low_memory=False)
            for key, info in channels.items()
        }
        widths = {key: value.shape[1] for key, value in frames.items()}
        n_windows = min(widths.values())
        if n_windows < 1:
            raise FormalDataError(f"{source_label}: {config} has no windows: {widths}")
        arrays = {key: value.iloc[:, :n_windows] for key, value in frames.items()}
        stats = [
            _statistical_features(arrays["current"]),
            _statistical_features(arrays["x"]),
            _statistical_features(arrays["y"]),
            _statistical_features(arrays["z"]),
            _statistical_features(arrays["delta_t"]),
        ]
        feature_x = np.hstack((stats[1], _fft_features(arrays["x"], rpm)))
        feature_y = np.hstack((stats[2], _fft_features(arrays["y"], rpm)))
        feature_z = np.hstack((stats[3], _fft_features(arrays["z"], rpm)))
        raw_frame = pd.DataFrame(
            np.hstack((stats[0], feature_x, feature_y, feature_z, stats[4])),
            columns=FEATURE_NAMES,
        )
        raw_frame = raw_frame.replace([np.inf, -np.inf], np.nan).dropna()
        clean_frame, rows_before_clean = _clean_feature_frame(raw_frame)
        if clean_frame.empty:
            raise FormalDataError(f"{source_label}: {config} produced no clean rows")
        payload = clean_frame.to_csv(index=False).encode("utf-8")
        output = (
            output_root / "Step-2" / "myfeature" / motor / rpm / config
            / f"{motor}_Group_feature_data_clean.csv"
        )
        _write_bytes(output, payload, force=force)
        records.append(
            MaterializedFile(
                stage="2",
                motor=motor,
                rpm=rpm,
                config=config,
                output=str(output),
                source_member=f"{source_label}|{','.join(info.filename for info in channels.values())}",
                source_sha256=_sha256_bytes(payload),
                rows_before_clean=rows_before_clean,
                rows_after_clean=len(clean_frame),
                columns=clean_frame.shape[1],
                mode="converted_step2_channels",
            )
        )
    return records


def _convert_stage2(
    archive_path: Path,
    output_root: Path,
    *,
    force: bool,
    selected_conditions: set[tuple[str, str, str]] | None,
) -> list[MaterializedFile]:
    records: list[MaterializedFile] = []
    with ZipFile(archive_path) as outer:
        csv_member = _find_member(outer, suffix="csv.zip")
        with ZipFile(outer.open(csv_member)) as csv_archive:
            for condition_info in csv_archive.infolist():
                if condition_info.is_dir() or not condition_info.filename.lower().endswith("rpm.zip"):
                    continue
                condition = _condition_from_member(condition_info.filename)
                if condition is None:
                    continue
                motor, rpm, _ = condition
                if selected_conditions is not None and not any(
                    item[:2] == (motor, rpm) for item in selected_conditions
                ):
                    continue
                with ZipFile(csv_archive.open(condition_info)) as condition_archive:
                    records.extend(
                        _convert_condition(
                            condition_archive,
                            f"{archive_path.name}:{csv_member}:{condition_info.filename}",
                            output_root,
                            motor,
                            rpm,
                            force=force,
                            selected_conditions=selected_conditions,
                        )
                    )
    return records


def materialize(
    source_root: Path | str,
    output_root: Path | str,
    *,
    stages: Sequence[str] = STAGES,
    conditions: Sequence[tuple[str, str, str]] | None = None,
    force: bool = False,
) -> dict:
    """Materialise selected formal conditions and return a JSON-safe manifest."""
    stages = tuple(str(stage) for stage in stages)
    invalid = set(stages) - set(STAGES)
    if invalid:
        raise FormalDataError(f"unsupported stages: {sorted(invalid)}")
    source = Path(source_root).expanduser().resolve()
    output = Path(output_root).expanduser().resolve()
    _ensure_output_not_source(source, output)
    archives = discover_stage_archives(source, stages)
    selected = set(conditions) if conditions else None
    records: list[MaterializedFile] = []
    for stage in stages:
        if stage == "2":
            records.extend(
                _convert_stage2(archives[stage], output, force=force, selected_conditions=selected)
            )
        else:
            records.extend(
                _copy_clean_features(
                    archives[stage], stage, output, force=force, selected_conditions=selected
                )
            )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source),
        "output_root": str(output),
        "stages": list(stages),
        "archive_sha256": {stage: _sha256_file(path) for stage, path in archives.items()},
        "formal_contract": {
            "feature_dim": FEATURE_DIM,
            "clean_rule": "feature-level IQR scale=1.5, drop rows outside any feature bound",
            "raw_length": RAW_LENGTH,
            "sample_rate_hz": SAMPLE_RATE,
        },
        "files": [asdict(record) for record in records],
    }
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "formal_materialization_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _parse_condition(value: str) -> tuple[str, str, str]:
    parts = value.split("/")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("condition must be MOTOR/RPM/CONFIG, e.g. T2/8000rpm/8screws")
    if parts[0] not in MOTORS or parts[1] not in RPMS or parts[2] not in CONFIGS:
        raise argparse.ArgumentTypeError(f"unknown formal condition: {value}")
    return parts[0], parts[1], parts[2]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--stage", action="append", dest="stages", choices=STAGES)
    parser.add_argument("--condition", action="append", type=_parse_condition)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    manifest = materialize(
        args.source_root,
        args.output_root,
        stages=tuple(args.stages or STAGES),
        conditions=args.condition,
        force=args.force,
    )
    print(json.dumps({"output_root": manifest["output_root"], "files": len(manifest["files"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
