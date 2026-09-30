"""105-position computational semantics and read-only reconstruction checks.

Source: the user-provided Step2_Feature_Extraction_<rpm>_<stage>.py scripts.
Historical quirks are deliberately preserved, not silently renamed/repaired.
Physical axes/units/calibration cannot be established by numerical agreement.
"""
from __future__ import annotations
import ast
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew
from core.formal_data import (FEATURE_NAMES, _channel_key, _statistical_features,
    _fft_features, _clean_feature_frame, _sha256_file, HARMONIC_BANDWIDTHS, BASE_FREQUENCY)
from core.fault_type_source_audit import recover_row_mapping

FEATURE_VERSION = "formal105_historical_v1_semantics_audited_20261001"


def reference_statistics(data: np.ndarray) -> np.ndarray:
    """Independent vectorized translation of the historical 15 formulas."""
    x = np.asarray(data, float)
    rms = np.sqrt(np.mean(x*x, axis=0))
    mean_abs = np.mean(np.abs(x), axis=0)
    maximum = np.max(x, axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.column_stack((rms, x.mean(0), kurtosis(x, axis=0, fisher=False),
            x.std(0, ddof=0), skew(x, axis=0), np.ptp(x, axis=0), np.abs(maximum/rms),
            np.abs(maximum/mean_abs), rms/mean_abs, np.abs(maximum/mean_abs),
            maximum, x.min(0), np.mean(x*x, axis=0), x.var(0, ddof=0), mean_abs))


def reference_fft(data: np.ndarray, rpm: str) -> np.ndarray:
    x = np.asarray(data, float)
    half = len(x)//2
    amplitude = np.abs(np.fft.fft(x, axis=0))[:half]*2/len(x)
    frequency = np.arange(half)*10000/len(x)
    return np.column_stack([amplitude[(frequency >= BASE_FREQUENCY[rpm]*i-bandwidth)
        & (frequency <= BASE_FREQUENCY[rpm]*i+bandwidth)].max(0)
        for i, bandwidth in enumerate(HARMONIC_BANDWIDTHS, 1)])


def feature_contract() -> dict:
    return {"version": FEATURE_VERSION, "columns": [{"position": i+1, "canonical_name": name}
        for i, name in enumerate(FEATURE_NAMES)],
        "channel_blocks_1_based": {"current": [1, 15], "x": [16, 40], "y": [41, 65], "z": [66, 90], "delta_t": [91, 105]},
        "statistics": "RMS,mean,Pearson kurtosis,std(ddof=0),skew,ptp,abs(max)/RMS,abs(max)/meanabs,RMS/meanabs,abs(max)/meanabs,max,min,MSA,var(ddof=0),meanabs",
        "historical_quirks": ["clearance_indicator equals impulse_indicator; not conventional squared-mean-sqrt clearance",
            "crest uses abs(max), not max(abs(x)); negative peaks may be understated",
            "MSA = RMS squared; variance = std squared; deterministic redundancy",
            "Y/Z FFT headers may say FFTnX but their input axis is Y/Z",
            "nominal base frequency is integer 133/183 rather than measured RPM or exact RPM/60"],
        "fft": {"sample_rate_code_hz": 10000, "length_code": 10000,
            "amplitude": "2*abs(FFT)/length, bins 0..length//2-1, no detrending/windowing",
            "base_hz": BASE_FREQUENCY, "bandwidth_hz": list(HARMONIC_BANDWIDTHS)},
        "physical_contract": {"sample_rate_actual": None, "sensor_units": None, "orientation": None,
            "calibration": None, "mounting": None, "load": None},
        "historical_feature_cleaning": "Stage2 adapter 1.5-IQR per-file; archived Stage1/3 masks can be recovered but generating rule/version not fully known",
        "scope": "computational contract only; not proof of equal physical measurement semantics"}


def formula_source_check(root: Path) -> dict:
    # Do not execute/import historical source. Hash the AST of relevant functions.
    records = []
    for path in sorted(root.glob("Step2_Feature_Extraction_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        values = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in {"rawdata", "Fs", "baseFreq1", "rpm"}:
                    try:
                        values[node.targets[0].id] = ast.literal_eval(node.value)
                    except ValueError:
                        pass
        records.append({"path": str(path), "sha256": _sha256_file(path), "constants": values,
            "functions": {key: hashlib.sha256(ast.dump(functions[key], include_attributes=False).encode()).hexdigest()
                for key in ("extract_statistical_features", "extract_fft_features") if key in functions}})
    return {"records": records, "statistical_function_ast_variants": len({r["functions"].get("extract_statistical_features") for r in records}),
        "fft_function_ast_variants": len({r["functions"].get("extract_fft_features") for r in records}),
        "generator_identity": "unknown; AST agreement does not prove archive generation version"}


def reconstruct_condition(frames: dict[str, pd.DataFrame], rpm: str) -> tuple[pd.DataFrame, dict]:
    required = {"current", "x", "y", "z", "delta_t"}
    if set(frames) != required or any(frame.shape[0] != 10000 for frame in frames.values()):
        raise ValueError("five 10000-row processed channel matrices required")
    widths = {key: frame.shape[1] for key, frame in frames.items()}
    width = min(widths.values())
    arrays = {key: frame.iloc[:, :width] for key, frame in frames.items()}
    blocks = []
    for key in ("current", "x", "y", "z", "delta_t"):
        block = _statistical_features(arrays[key])
        np.testing.assert_allclose(block, reference_statistics(arrays[key].to_numpy()), rtol=1e-10, atol=1e-10, equal_nan=True)
        if key in {"x", "y", "z"}:
            spectrum = _fft_features(arrays[key], rpm)
            np.testing.assert_allclose(spectrum, reference_fft(arrays[key].to_numpy(), rpm), rtol=1e-9, atol=1e-10, equal_nan=True)
            block = np.hstack((block, spectrum))
        blocks.append(block)
    result = pd.DataFrame(np.hstack(blocks), columns=FEATURE_NAMES)
    return result, {"channel_widths": widths, "aligned_processed_windows": width,
        "truncated_columns_by_channel": {key: value-width for key, value in widths.items()},
        "nan_count_by_channel": {key: int(frame.isna().sum().sum()) for key, frame in frames.items()},
        "physical_time_alignment": "UNKNOWN", "independent_reference_comparison": "PASS"}


def audit_features(source_root: Path, extracted_root: Path, data_root: Path) -> dict:
    checks, stage2_maps = [], []
    # Three predeclared healthy probes per copied stage; every Stage2 condition
    # is reconstructed for complete mapping of its materialized clean rows.
    for formal in sorted(data_root.glob("Step-*/myfeature/*/*/*/*_clean.csv")):
        stage, _, motor, rpm, config, _ = formal.relative_to(data_root).parts
        if stage != "Step-2" and config != "8screws":
            continue
        candidates = [p for p in (extracted_root / f"階段{stage[-1]}").rglob("*_data.csv")
            if p.parent.name == config and rpm in p.parts and _channel_key(p.name)]
        frames, sources = {}, []
        for path in candidates:
            key = _channel_key(path.name)
            if key in frames:
                raise ValueError(f"ambiguous channel source {key}: {path}")
            frames[key] = pd.read_csv(path, low_memory=False)
            sources.append({"path": str(path), "sha256": _sha256_file(path)})
        raw, audit = reconstruct_condition(frames, rpm)
        clean = pd.read_csv(formal).to_numpy(float)
        mapping = recover_row_mapping(clean, raw.to_numpy())
        record = {"formal_source": formal.relative_to(data_root).as_posix(), "formal_sha256": _sha256_file(formal),
            "channel_sources": sources, "numerical_mapping_unique": mapping["unique_matches"],
            "clean_rows": len(clean), **audit}
        if stage == "Step-2":
            finite = raw.replace([np.inf, -np.inf], np.nan).dropna()
            filtered, _ = _clean_feature_frame(finite)
            record["adapter_clean_reproduction"] = bool(filtered.shape == clean.shape and np.allclose(filtered.to_numpy(), clean, rtol=1e-9, atol=1e-10))
            stage2_maps.append({"formal_source": record["formal_source"], "formal_sha256": record["formal_sha256"],
                "channel_sources": sources, **mapping})
        checks.append(record)
    return {"schema_version": 1, "contract": feature_contract(), "source_formula_check": formula_source_check(source_root),
        "predeclared_scope": "all30 Stage2 conditions and six healthy Stage1/3 x RPM probes; no performance-based probe choice",
        "checks": checks, "stage2_mappings": stage2_maps,
        "stage2_unique_processed_mappings": sum(m["unique_matches"] for m in stage2_maps),
        "physical_equivalence": "UNVERIFIED", "original_daq_intervals": None,
        "data_changes": "none; read-only checks; future corrected semantics require a new version and raw metadata"}
