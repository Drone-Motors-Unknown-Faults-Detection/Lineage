"""Versioned 105-D extraction from the SAME shared raw windows.

Historical formula reference: core.fault_type_feature_contract, itself audited
against Ancestor Step2; no legacy import. Corrected formulas and exact nominal
RPM are separate ablations, never mislabeled measured order tracking.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from core.synchronized_raw import CHANNELS, read_recording, audit_timebase, quality_mask, make_windows
from core.fault_type_feature_contract import FEATURE_VERSION, reference_statistics
from core.formal_data import FEATURE_NAMES, BASE_FREQUENCY, HARMONIC_BANDWIDTHS, _sha256_file
from core.fault_type_final_guard import digest, seal
from core.fault_type_provenance import save_json

VARIANTS = ("historical105", "aligned_only", "corrected_formulas", "exact_nominal_rpm")


def version_registry(settings: dict) -> dict:
    variant = settings["variant"]
    if variant not in VARIANTS: raise ValueError("undeclared feature variant")
    source = {name: _sha256_file(Path(__file__).with_name(name)) for name in
              ("synchronized_features.py", "synchronized_raw.py", "fault_type_feature_contract.py", "formal_data.py")}
    code_sha = digest(source)
    pipeline_id = digest({"extractor": code_sha, "settings": settings})
    return {"variant": variant, "feature_version": FEATURE_VERSION if variant == "historical105" else f"aligned105_{variant}_{pipeline_id[:16]}",
        "pipeline_id": pipeline_id, "extractor_sha256": code_sha, "source_checksums": source,
        "settings_checksum": digest(settings), "settings": settings, "columns": FEATURE_NAMES,
        "semantics": {"statistics": "legacy" if variant != "corrected_formulas" else "maxabs crest; squared-mean-sqrt clearance; degenerate moments/ratios zero",
            "frequency": "configured RPM/60 (NOT measured)" if variant == "exact_nominal_rpm" else "historical integer100/133/183 Hz",
            "fft": "2*abs(FFT)/n, no detrending/window function; first n//2 bins; declared harmonic bandwidths",
            "alignment": "shared original row intervals, never reconstructed historical DAQ",
            "column_text": "canonical X/Y/Z suffix; historical CSV text typo not reproduced",
            "redundancy": "MSA=RMS² and variance=std² retained"}}


def extract_window(values: np.ndarray, *, fs: float, rpm: str, settings: dict) -> np.ndarray:
    x = np.asarray(values, float)
    variant = settings["variant"]
    if variant not in VARIANTS or x.ndim != 2 or x.shape[1] != 5 or not np.isfinite(x).all():
        raise ValueError("finite five-channel window and declared variant required")
    if fs != 10000 and variant == "historical105":
        raise ValueError("historical FFT semantics require nominal10kHz; do not relabel another grid")
    if not fs or fs <= 0: raise ValueError("positive configured sampling rate required")
    if rpm not in BASE_FREQUENCY: raise ValueError("undeclared nominal RPM")
    stats = reference_statistics(x)
    if variant == "corrected_formulas":
        maxabs = np.max(np.abs(x), axis=0)
        rms, meanabs = np.sqrt(np.mean(x*x, axis=0)), np.mean(np.abs(x), axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            stats[:,6] = maxabs/rms
            stats[:,7] = maxabs / np.mean(np.sqrt(np.abs(x)), axis=0)**2
        # Explicit degenerate-signal convention; does not delete or change raw.
        for column in (2,4,6,7,8,9): stats[:,column] = np.nan_to_num(stats[:,column], nan=0., posinf=0., neginf=0.)
    freq = np.arange(len(x)//2)*fs/len(x)
    amplitude = np.abs(np.fft.fft(x, axis=0))[:len(x)//2]*2/len(x)
    base = float(rpm.removesuffix("rpm"))/60 if variant == "exact_nominal_rpm" else BASE_FREQUENCY[rpm]
    blocks = []
    for j,name in enumerate(CHANNELS):
        block = stats[j].tolist()
        if name in {"x","y","z"}:
            for harmonic,width in enumerate(HARMONIC_BANDWIDTHS,1):
                band = (freq >= base*harmonic-width) & (freq <= base*harmonic+width)
                if not band.any(): raise ValueError("FFT resolution/Nyquist cannot represent declared harmonic band")
                block.append(float(amplitude[band,j].max()))
        blocks.extend(block)
    return np.asarray(blocks)


def generate(recordings: list[tuple[Path,dict]], *, settings: dict, output: Path, incoming_root: Path) -> dict:
    output, incoming_root = output.resolve(), incoming_root.resolve()
    if incoming_root not in output.parents: raise ValueError("output must be within explicit incoming-root; raw never copied")
    output.mkdir(parents=True, exist_ok=True)
    if (output/"features.csv").exists(): raise ValueError("refuse feature overwrite")
    registry = version_registry(settings)
    rows, vectors, rejected, audits = [], [], [], []
    contracts, raw_configs = [], []
    for path,cfg in recordings:
        raw = read_recording(path,cfg)
        if incoming_root not in raw.path.parents: raise ValueError("raw path outside incoming-root")
        for key in ("quality","windows"):
            if key in settings and settings[key] != cfg[key]: raise ValueError("per-recording settings differ from version registry")
        raw_configs.append({"path":raw.path.relative_to(incoming_root).as_posix(),"sha256":raw.sha256,"config":cfg})
        audit = audit_timebase(raw); quality = quality_mask(raw,cfg["quality"])
        windows,bad = make_windows(raw,audit,quality,cfg["windows"]); rejected.extend(bad); audits.append(audit.summary)
        contracts.append(cfg.get("physical_contract",{}))
        for window in windows:
            vector = extract_window(window.values,fs=cfg.get("sample_rate_hz"),rpm=cfg["rpm"],settings=settings)
            if not np.isfinite(vector).all():
                rejected.append({**window.metadata,"reasons":["nonfinite_historical_features"]}); continue
            row = {**window.metadata, **{k:cfg.get(k) for k in ("recording_id","motor_id","session_id","run_id","label","rpm","acquisition_timestamp","attestation")},
                "row_index":len(vectors), "raw_source_file":raw.path.relative_to(incoming_root).as_posix(),
                "fs_evidence":audit.summary["fs_evidence"], "alignment_evidence":audit.summary["alignment_evidence"],
                "feature_row_id":digest([window.window_id,registry["pipeline_id"],vector.tolist()]),
                "physical_contract":cfg.get("physical_contract",{})}
            vectors.append(vector); rows.append(row)
    if not vectors: raise ValueError("no eligible feature windows; inspect quality/time/degenerate semantics")
    if any(c != contracts[0] for c in contracts): raise ValueError("mixing different physical contracts requires separate bundles")
    feature = output/"features.csv"; pd.DataFrame(vectors,columns=FEATURE_NAMES).to_csv(feature,index=False)
    manifest = seal({"schema_version":2, "feature_version":registry["feature_version"], "extractor_sha256":registry["extractor_sha256"],
        "pipeline_id":registry["pipeline_id"], "column_order":FEATURE_NAMES, "physical_contract":contracts[0],
        "acquisition_evidence":{"source":"raw parse/count/time audit and operator attestations", "synthetic":all(r["synthetic"] for r in rows)},
        "synthetic":any(r["synthetic"] for r in rows), "raw_recordings":raw_configs,
        "feature_files":[{"path":feature.relative_to(incoming_root).as_posix(),"sha256":_sha256_file(feature),"windows":rows}]},"manifest_checksum")
    save_json(output/"manifest.json",manifest); save_json(output/"version_registry.json",registry)
    save_json(output/"raw_window_audit.json",{"audits":audits,"rejected":rejected,"rows":len(rows),
        "scope":"synthetic_engineering" if manifest["synthetic"] else "raw_pipeline_preview",
        "raw_files_modified":False,"formal_data_modified":False})
    return {"manifest":manifest,"registry":registry,"rows":len(rows),"rejected_windows":len(rejected)}
