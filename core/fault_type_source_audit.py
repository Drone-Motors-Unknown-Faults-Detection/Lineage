"""Read-only archive/script inspection and conservative processed-row mapping.

Historical scripts are parsed, NEVER imported/executed. An ordinal in a
processed channel CSV is not promoted to a contiguous original DAQ interval.
"""
from __future__ import annotations
import ast
import hashlib
import io
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd
from core.formal_data import _sha256_file


def script_audit(path: Path) -> dict:
    payload = path.read_bytes()
    source = payload.decode("utf-8-sig")
    tree = ast.parse(source)
    functions = {node.name: {"line": node.lineno, "end_line": node.end_lineno,
        "ast_sha256": hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()}
        for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    hits = {}
    for key, token in {"raw_header": "header=22", "nominal_window": "10000",
            "per_channel_iqr": "raw_data = iqr", "concatenate_sources": "pd.concat([all_data",
            "reset_index": "reset_index(drop=True)", "truncate_alignment": "min_rows",
            "three_iqr_function": "Q1 - 3 * IQR"}.items():
        hits[key] = [i for i, line in enumerate(source.splitlines(), 1) if token in line]
    return {"name": path.name, "path": str(path.resolve()), "sha256": hashlib.sha256(payload).hexdigest(),
        "functions": functions, "code_evidence_lines": hits,
        "execution": "not executed", "actual_generator_version": None}


def archive_inventory(path: Path) -> dict:
    result = {"path": str(path.resolve()), "sha256": _sha256_file(path), "bytes": path.stat().st_size,
        "entries": [], "processed_channel_csvs": [], "feature_csvs": []}
    with ZipFile(path) as outer:
        for info in outer.infolist():
            if info.is_dir():
                continue
            result["entries"].append({"member": info.filename, "bytes": info.file_size, "crc32": info.CRC})
            if info.filename.endswith("myfeature.zip"):
                with ZipFile(outer.open(info)) as features:
                    result["feature_csvs"] = [{"member": item.filename, "bytes": item.file_size, "crc32": item.CRC}
                        for item in features.infolist() if item.filename.endswith(".csv")]
            elif info.filename.endswith("csv.zip"):
                with ZipFile(outer.open(info)) as channels:
                    for condition in channels.infolist():
                        if condition.filename.endswith("rpm.zip"):
                            with ZipFile(channels.open(condition)) as inner:
                                result["processed_channel_csvs"].extend({"member": f"{info.filename}:{condition.filename}:{item.filename}",
                                    "bytes": item.file_size, "crc32": item.CRC}
                                    for item in inner.infolist() if item.filename.endswith(".csv"))
                        elif condition.filename.endswith(".csv"):
                            result["processed_channel_csvs"].append({"member": f"{info.filename}:{condition.filename}",
                                "bytes": condition.file_size, "crc32": condition.CRC})
    result["classification"] = "processed channel windows / features / model archives, not verified original DAQ recordings"
    return result


def recover_row_mapping(clean: np.ndarray, unclean: np.ndarray, *, rtol=1e-9, atol=1e-10) -> dict:
    """Return only unique numeric matches. Repeated/absent rows stay unknown.

    Input clean rows correspond to outputs; indices refer to unclean feature
    rows (processed-window ordinal), NOT original source sample intervals.
    """
    clean, unclean = np.asarray(clean, float), np.asarray(unclean, float)
    if clean.ndim != 2 or unclean.ndim != 2 or clean.shape[1] != unclean.shape[1]:
        raise ValueError("incompatible feature matrices")
    mappings, ambiguous, unmatched = [], [], []
    for index, row in enumerate(clean):
        possible = np.flatnonzero(np.isclose(unclean[:, 0], row[0], rtol=rtol, atol=atol))
        matches = [int(i) for i in possible if np.all(np.isclose(unclean[i], row, rtol=rtol, atol=atol, equal_nan=False))]
        if len(matches) == 1:
            mappings.append({"clean_row_index": index, "processed_window_ordinal": matches[0]})
        elif matches:
            ambiguous.append({"clean_row_index": index, "candidate_ordinals": matches})
        else:
            unmatched.append(index)
    return {"evidence_level": "reconstructed", "method": "unique all-105 numeric equality within stated tolerances",
        "rtol": rtol, "atol": atol, "clean_rows": len(clean), "unclean_rows": len(unclean),
        "unique_matches": len(mappings), "ambiguous_rows": ambiguous, "unmatched_rows": unmatched,
        "mapping": mappings, "raw_source_intervals": None,
        "limitation": "Processed ordinal only; per-channel deletion/concatenation prevents original timing recovery without DAQ files and masks."}


def archived_feature_mappings(source_root: Path, data_root: Path) -> list[dict]:
    results = []
    for stage in ("1", "3"):
        archive_path = source_root / f"階段{stage}.zip"
        with ZipFile(archive_path) as outer:
            feature_member = next(n for n in outer.namelist() if n.endswith("myfeature.zip"))
            with ZipFile(outer.open(feature_member)) as archive:
                names = set(archive.namelist())
                for name in sorted(names):
                    if not name.endswith("_Group_feature_data_clean.csv"):
                        continue
                    clean_bytes = archive.read(name)
                    formal = data_root / f"Step-{stage}" / name
                    if _sha256_file(formal) != hashlib.sha256(clean_bytes).hexdigest():
                        raise ValueError(f"formal/archive clean checksum mismatch: {name}")
                    # Prefer complete unfiltered feature matrix, not a later *_raw variant.
                    unclean_name = name.replace("_clean.csv", ".csv")
                    if unclean_name not in names:
                        results.append({"formal_source": formal.relative_to(data_root).as_posix(), "status": "MISSING_UNCLEAN"})
                        continue
                    unclean_bytes = archive.read(unclean_name)
                    clean = pd.read_csv(io.BytesIO(clean_bytes)).to_numpy(float)
                    unclean = pd.read_csv(io.BytesIO(unclean_bytes)).to_numpy(float)
                    mapping = recover_row_mapping(clean, unclean)
                    results.append({"formal_source": formal.relative_to(data_root).as_posix(), "source_archive": str(archive_path),
                        "unclean_member": f"{feature_member}:{unclean_name}",
                        "clean_sha256": hashlib.sha256(clean_bytes).hexdigest(),
                        "unclean_sha256": hashlib.sha256(unclean_bytes).hexdigest(), **mapping})
    return results


def source_inventory(roots: list[Path], data_root: Path) -> dict:
    inventories = []
    for root in roots:
        files = sorted(p for p in root.rglob("*") if p.is_file())
        originals = []
        for path in files:
            if path.suffix.lower() in {".txt", ".lvm", ".tdms", ".dat"}:
                originals.append(str(path))
            elif path.suffix.lower() == ".csv":
                with path.open("rb") as handle:
                    head = handle.read(8192)
                if b"X_Value" in head or b"Comment" in head:
                    originals.append(str(path))
        inventories.append({"root": str(root.resolve()), "files": len(files),
            "extensions": dict(Counter(p.suffix.lower() for p in files)),
            "original_daq_candidates": originals,
            "scripts": [script_audit(p) for p in sorted(root.glob("Step[12]*.py"))],
            "archives": [archive_inventory(p) for p in sorted(root.glob("階段*.zip"))]})
    mappings = archived_feature_mappings(roots[0], data_root)
    return {"schema_version": 1, "roots": inventories, "mappings": mappings,
        "recovered_processed_rows": sum(item.get("unique_matches", 0) for item in mappings),
        "recovered_original_daq_intervals": 0, "raw_interval_status": "UNKNOWN_NOT_ZERO_OVERLAP",
        "session_id": None, "run_id": None, "serial_number": None,
        "preprocessing_risks": ["Code concatenates recordings before windowing; original boundaries lost.",
            "Code independently deletes per-channel outliers; ordinal columns may not align in time.",
            "FFT assumes uniform 10kHz after deletion; physical sampling consistency unknown.",
            "Archived generator version not proven merely by current script filename."]}
