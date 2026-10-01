"""Strict incoming loader and non-predicting compatibility preflight.

Existing guard remains the sole exposure/coverage qualification authority.
Historical artifacts with unknown physical contract cannot pass this bridge.
"""
from __future__ import annotations
import json
import platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from core.fault_type_final_guard import FinalTestBlocked, ingest, verify_seal, numeric_row_digest, digest
from core.formal_data import FEATURE_NAMES, _sha256_file
from core.synchronized_raw import read_recording, audit_timebase, quality_mask, make_windows
from core.synchronized_features import extract_window, version_registry


class IncomingStore:
    def __init__(self,root): self.root=Path(root).resolve()
    def load(self,records):
        cache={}; rows=[]
        for record in records:
            path=(self.root/record["feature_source"]).resolve()
            if self.root not in path.parents: raise FinalTestBlocked("incoming path escape")
            if path not in cache:
                if _sha256_file(path) != record["source_sha256"]: raise FinalTestBlocked("incoming bytes changed")
                frame=pd.read_csv(path)
                if list(frame.columns) != FEATURE_NAMES: raise FinalTestBlocked("incoming feature column order mismatch")
                cache[path]=frame.to_numpy(float)
            row=cache[path][record["row_index"]]
            if not np.isfinite(row).all() or numeric_row_digest(row) != record["numeric_row_digest"]: raise FinalTestBlocked("incoming row digest mismatch")
            rows.append(row)
        return np.vstack(rows)


def model_contract_checksum(model):
    maha,knn=model["detectors"]["mahalanobis"],model["detectors"]["knn"]
    return digest({"scaler":{"type":type(model["scaler"]).__name__,"params":model["scaler"].get_params()},
        "classifiers":{name:{"type":type(c).__name__,"params":c.get_params()} for name,c in model["classifiers"].items()},
        "detectors":{"mahalanobis":{"method":maha.method,"confidence":maha.confidence,"ridge":maha.ridge,"mcd_variance":maha.mcd_variance},
                     "knn":{"confidence":knn.confidence,"k":knn.n_neighbors}}})


def validate_physical_contract(contract, *, synthetic):
    for key in ("sensor_units","orientation","calibration","mounting","load"):
        fact=contract.get(key)
        if synthetic:
            if not isinstance(fact,str) or not fact.startswith("fixture_attested:"): raise FinalTestBlocked("synthetic physical fields must explicitly say fixture_attested")
        elif not isinstance(fact,dict) or fact.get("level") not in {"operator_attested","file_verified"} or not isinstance(fact.get("reference"),str) or not fact["reference"].strip() or not fact.get("value") or str(fact["value"]).lower() in {"unknown","null","n/a","tbd"}:
            raise FinalTestBlocked(f"physical fact {key} missing/unknown/documented only; actual attestation/reference required")


def prepare_bundle(root: Path, manifest: dict, registry: dict):
    validate_physical_contract(manifest.get("physical_contract",{}),synthetic=bool(manifest.get("synthetic")))
    if manifest.get("schema_version") != 2 or not manifest.get("raw_recordings"): raise FinalTestBlocked("fresh requires raw parser/count/window verification schema2")
    actual_registry=version_registry(registry["settings"])
    if actual_registry != registry or manifest.get("pipeline_id") != registry["pipeline_id"]: raise FinalTestBlocked("extractor/settings version mismatch")
    if manifest.get("column_order") != FEATURE_NAMES: raise FinalTestBlocked("feature column order mismatch")
    raw_by_sha={}
    for source in manifest["raw_recordings"]:
        path=(root/source["path"]).resolve()
        if root.resolve() not in path.parents: raise FinalTestBlocked("raw path escape")
        recording=read_recording(path,source["config"])
        if bool(recording.config.get("synthetic")) != bool(manifest.get("synthetic")):
            raise FinalTestBlocked("synthetic raw cannot be relabeled as actual acquisition")
        if not manifest.get("synthetic") and any(e.get("level")=="fixture_attested" for e in recording.config.get("evidence",{}).values()):
            raise FinalTestBlocked("fixture evidence cannot qualify actual hardware")
        if recording.config.get("physical_contract") != manifest.get("physical_contract"):
            raise FinalTestBlocked("raw and feature physical contracts differ")
        if recording.sha256 != source["sha256"]: raise FinalTestBlocked("raw checksum changed")
        audit=audit_timebase(recording)
        if not audit.summary["physical_time_alignment_verified"]: raise FinalTestBlocked("raw time/alignment audit incomplete")
        windows,_=make_windows(recording,audit,quality_mask(recording,source["config"]["quality"]),source["config"]["windows"])
        raw_by_sha[recording.sha256]=(recording,{w.source_interval:w for w in windows})
    bundle=ingest(root,manifest)
    if len({r["numeric_row_digest"] for r in bundle["records"]}) != len(bundle["records"]):
        raise FinalTestBlocked("duplicate semantic rows inside incoming final bundle")
    values=IncomingStore(root).load(bundle["records"])
    for row,vector in zip(bundle["records"],values):
        recording,windows=raw_by_sha[row["raw_source_sha256"]]
        interval=tuple(row["source_interval"])
        if interval not in windows or row["raw_sample_count"] != len(recording.values): raise FinalTestBlocked("window metadata/count not in actual raw audit")
        if any(row.get(key)!=value for key,value in windows[interval].metadata.items()): raise FinalTestBlocked("sidecar time/index/quality mapping differs from raw audit")
        for key in ("motor_id","session_id","run_id","label","rpm","acquisition_timestamp","attestation"):
            if row[key] != recording.config.get(key): raise FinalTestBlocked("row acquisition identity differs from raw contract")
        if row["sample_rate_hz"] != recording.config["sample_rate_hz"] or row["synthetic"] != bool(recording.config.get("synthetic")):
            raise FinalTestBlocked("window rate/synthetic scope differs from actual raw parser audit")
        expected=extract_window(windows[interval].values,fs=recording.config["sample_rate_hz"],rpm=row["rpm"],settings=registry["settings"])
        if not np.allclose(expected,vector,rtol=1e-10,atol=1e-10): raise FinalTestBlocked("raw→feature values do not reproduce")
        if row.get("feature_row_id")!=digest([windows[interval].window_id,registry["pipeline_id"],numeric_row_digest(expected)]): raise FinalTestBlocked("feature row ID mapping mismatch")
    # Bind provenance distinctions omitted by historical schema1 ingest.
    from core.fault_type_final_guard import seal
    return seal({**bundle,"synthetic":bool(manifest.get("synthetic")),"pipeline_id":manifest["pipeline_id"],"column_order":FEATURE_NAMES},"data_version_checksum")


def load_models(locked: dict, artifact_root: Path, bundle: dict):
    verify_seal(locked,"locked_checksum")
    if locked.get("fresh_protocol") != "paired_n5_three_folds_v1": raise FinalTestBlocked("fresh CLI explicitly supports locked N5/all3folds only")
    known,unknown=locked["known_labels"],locked["unknown_labels"]
    if len(known) != 6 or len(unknown) != 4 or len(set(known+unknown)) != 10 or known[0] != "8screws": raise FinalTestBlocked("N5 roles/healthy encoding mismatch")
    if locked.get("minimum_test_samples_per_class",0) < 30 or locked.get("minimum_test_groups_per_class",0) < 2: raise FinalTestBlocked("fresh coverage cannot be relaxed below declared30windows/2groups")
    if locked.get("expected_rpms") != ["6000rpm","8000rpm","11000rpm"]: raise FinalTestBlocked("fresh requires predeclared3RPM coverage")
    if not locked.get("training_records") or not locked.get("training_physical_contract") or locked["training_physical_contract"] != bundle["physical_contract"]:
        raise FinalTestBlocked("historical unknown physical training cannot be certified by incoming metadata; new verified training/bridge required")
    if locked.get("synthetic") != bundle.get("synthetic"): raise FinalTestBlocked("synthetic and actual acquisition scopes cannot be mixed")
    expected_status="fixture_attested" if bundle["synthetic"] else "operator_attested_complete"
    if locked.get("training_provenance_status") != expected_status: raise FinalTestBlocked("training provenance/physical bridge must be completed independently of final data")
    training_by_id={r["sample_id"]:r for r in locked["training_records"]}
    if len(training_by_id)!=len(locked["training_records"]) or set(locked["selection_input_ids"])-set(training_by_id):
        raise FinalTestBlocked("selection/training ID provenance incomplete")
    if set(locked.get("bridge_input_ids",[])) & {r["sample_id"] for r in bundle["records"]}: raise FinalTestBlocked("final data cannot be bridge calibration")
    if locked.get("column_order") != FEATURE_NAMES or locked.get("pipeline_id") != bundle.get("pipeline_id"): raise FinalTestBlocked("model extractor/column contract mismatch")
    environment={"python":platform.python_version(),"sklearn":sklearn.__version__}
    if locked.get("serialization_environment") != environment: raise FinalTestBlocked("retrain trusted models in current Python/sklearn; cross-runtime joblib unsupported")
    artifacts=locked["training_artifacts"]
    if len(artifacts) != 3 or len({a["fold_id"] for a in artifacts}) != 3: raise FinalTestBlocked("exactly3distinct folds required")
    if locked["training_artifact_sha256"] != digest(artifacts): raise FinalTestBlocked("training artifact index mismatch")
    fitted,manifests=[],[]
    for item in artifacts:
        path=(artifact_root/item["path"]).resolve()
        if artifact_root.resolve() not in path.parents or _sha256_file(path) != item["sha256"]: raise FinalTestBlocked("trusted artifact root/hash mismatch")
        # The explicitly trusted root must contain locally produced artifacts,
        # never arbitrary downloads. Hash is integrity, not pickle safety.
        model=joblib.load(path)
        if model.get("fold_id") != item["fold_id"] or model.get("labels") != known: raise FinalTestBlocked("fold/label encoding mismatch")
        if model_contract_checksum(model) != item.get("model_contract_checksum"): raise FinalTestBlocked("scaler/classifier/factory parameter contract mismatch")
        if model.get("fit_audit") != item.get("fit_audit") or not model.get("fit_audit"): raise FinalTestBlocked("fit audit mismatch")
        audit=model["fit_audit"]
        if set(audit["train_ids"]) & set(audit["calibration_ids"]) or not audit.get("known_only") or not audit.get("train_only_transforms"):
            raise FinalTestBlocked("fit/calibration split invalid")
        training_ids={r["sample_id"] for r in locked["training_records"]}
        if set(audit["train_ids"]+audit["calibration_ids"])-training_ids: raise FinalTestBlocked("fit IDs lack bound acquisition provenance")
        if any(training_by_id[sid].get("label") not in known for sid in audit["train_ids"]+audit["calibration_ids"]): raise FinalTestBlocked("unknown input in fit/calibration provenance")
        if model["scaler"].n_features_in_ != 105 or set(model["detectors"]) != {"mahalanobis","knn"} or not model["classifiers"]:
            raise FinalTestBlocked("model/scaler/detector schema incompatible")
        for classifier in model["classifiers"].values():
            if classifier.n_features_in_ != 105 or list(classifier.classes_) != list(range(6)): raise FinalTestBlocked("classifier feature/label schema incompatible")
        for detector in model["detectors"].values():
            summaries=detector.class_summaries()
            if [s["label"] for s in summaries] != list(range(6)) or any(not np.isfinite(s["threshold"]) or s["threshold"] <= 0 for s in summaries):
                raise FinalTestBlocked("detector known-class/threshold contract mismatch")
        maha,knn=model["detectors"]["mahalanobis"],model["detectors"]["knn"]
        if maha.method != "ledoit_wolf" or maha.pca_ is not None or any(d.location.shape != (105,) or d.precision.shape != (105,105) for d in maha.distributions_) or knn.n_features_in_ != 105:
            raise FinalTestBlocked("fresh detector feature/covariance contract mismatch")
        if maha.confidence != .95 or knn.confidence != .95 or knn.n_neighbors != 5:
            raise FinalTestBlocked("fresh v1 factory settings require confidence.95, LW, k5")
        fitted.append(model); manifests.append({"fold_id":item["fold_id"],"manifest_checksum":item["manifest_checksum"],"sample_split_seed":item["seed"]})
    return fitted,manifests
