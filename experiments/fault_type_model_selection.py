"""Small predeclared known-only validation search; exposed data is exploratory.

No unknown features/test partitions are loaded by run(). Cold-start healthy-
only research is a different task and is not mixed into this six-class study.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix, recall_score
from sklearn.preprocessing import RobustScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits
from core.fault_type_features import FeatureStore
from core.fault_type_manifest import read_split_manifest
from core.fault_type_final_guard import seal, verify_seal
from core.fault_type_feature_contract import FEATURE_VERSION
from core.fault_type_provenance import save_json
from core.logger import setup_run
from core.openset import create_openset_detector
from experiments.fault_type_openset import CLASSIFIER_CONFIG, DETECTOR_CONFIG


CANDIDATES = [
    {"name": "linear_baseline", "complexity_rank": 0, "parameters": CLASSIFIER_CONFIG,
        "source": "unchanged existing fault_type_openset.CLASSIFIER_CONFIG"},
    {"name": "rbf_svm", "complexity_rank": 1, "parameters": {"C": 1.0, "kernel": "rbf", "gamma": "scale", "class_weight": "balanced", "probability": False},
        "source": "Cortes & Vapnik (1995), Support-vector networks, Machine Learning20:273–297; https://doi.org/10.1007/BF00994018"},
    {"name": "extra_trees", "complexity_rank": 2, "parameters": {"n_estimators": 200, "max_depth": 12, "min_samples_leaf": 5, "max_features": "sqrt", "class_weight": "balanced", "n_jobs": 1},
        "source": "Geurts, Ernst & Wehenkel (2006), Extremely randomized trees, Machine Learning63:3–42; https://doi.org/10.1007/s10994-006-6226-1"},
]


def build_registry(manifests: list[dict], ledger: dict, feature_audit_sha256: str) -> dict:
    verify_seal(ledger, "ledger_checksum")
    roles = {(tuple(m["known_fault_labels"]), tuple(m["unknown_test_labels"])) for m in manifests}
    if len(manifests) != 3 or len(roles) != 1:
        raise ValueError("exactly3 original folds of the same prior N5 class role required")
    if len(manifests[0]["known_fault_labels"]) != 5 or len(manifests[0]["unknown_test_labels"]) != 4:
        raise ValueError("primary task must be healthy+5known/4unknown")
    return seal({"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "candidates": CANDIDATES, "feature_version": FEATURE_VERSION, "feature_audit_sha256": feature_audit_sha256,
        "manifests": [{"split_id": m["split_id"], "manifest_checksum": m["manifest_checksum"],
            "fold_id": m["fold_id"], "seed": m["sample_split_seed"]} for m in manifests],
        "dataset_fingerprint": manifests[0]["dataset_fingerprint"], "exposure_ledger_checksum": ledger["ledger_checksum"],
        "selection_rule": "equal-fold mean known-validation macro-F1, then balanced accuracy, then lower complexity_rank; ties tolerance1e-12",
        "protocol": "first original predeclared126 N5 combination, all3 original motor folds; no new class split/matrix",
        "features": "105 numeric positions only; paths/T-code/label encoding not features",
        "scaler": "train-only RobustScaler; no PCA/feature selector", "detectors": DETECTOR_CONFIG,
        "historical_test_exposure": "all existing samples already exposed; search and future evaluation exploratory only",
        "shared_validation_calibration": True, "fresh_final_test": False,
        "planned_evaluation": "at most original3 folds x baseline/selected x2detectors after config lock; no new2490 matrix",
        "interpretability": "linear coefficients and tree importances are diagnostics; RBF nonlinear similarity is not causal explanation"}, "registry_checksum")


def estimator(candidate: dict, seed: int):
    parameters = dict(candidate["parameters"])
    if candidate["name"] == "linear_baseline": return LogisticRegression(**parameters)
    if candidate["name"] == "rbf_svm": return SVC(**parameters, random_state=seed)
    if candidate["name"] == "extra_trees": return ExtraTreesClassifier(**parameters, random_state=seed)
    raise ValueError("unknown predeclared candidate")


def select_candidate(rows: list[dict], candidates: list[dict]) -> tuple[str, list[dict]]:
    scores = []
    for candidate in candidates:
        members = [r for r in rows if r["candidate"] == candidate["name"]]
        scores.append({"candidate": candidate["name"], "macro_f1": float(np.mean([r["macro_f1"] for r in members])),
            "balanced_accuracy": float(np.mean([r["balanced_accuracy"] for r in members])), "complexity_rank": candidate["complexity_rank"]})
    eligible = [r for r in scores if r["macro_f1"] >= max(r["macro_f1"] for r in scores)-1e-12]
    eligible = [r for r in eligible if r["balanced_accuracy"] >= max(r["balanced_accuracy"] for r in eligible)-1e-12]
    return min(eligible, key=lambda r: r["complexity_rank"])["candidate"], scores


def run(pools, *, manifests: list[dict], registry: dict) -> dict:
    verify_seal(registry, "registry_checksum")
    if [m["manifest_checksum"] for m in manifests] != [m["manifest_checksum"] for m in registry["manifests"]]:
        raise ValueError("selection manifest mismatch")
    if registry["candidates"] != CANDIDATES:
        raise ValueError("candidate set differs from predeclared bounded implementation")
    rows, audits, fitted = [], [], []
    for manifest in manifests:
        by_id = {r["sample_id"]: r for r in manifest["records"]}
        labels = [manifest["healthy_label"], *sorted(manifest["known_fault_labels"])]
        train = [by_id[sid] for sid in manifest["sample_ids"]["train"]]
        validation = [by_id[sid] for sid in manifest["sample_ids"]["validation"]]
        if any(r["label"] not in labels for r in [*train, *validation]):
            raise ValueError("only known train/validation allowed in model selection")
        if set(manifest["sample_ids"]["test"]) & {r["sample_id"] for r in [*train, *validation]}:
            raise ValueError("within-fold test IDs overlap selection inputs")
        start = time.perf_counter()
        with threadpool_limits(limits=1):
            scaler = RobustScaler().fit(pools.load(train))
            X = scaler.transform(pools.load(train)); V = scaler.transform(pools.load(validation))
            y = np.array([labels.index(r["label"]) for r in train])
            target = np.array([labels.index(r["label"]) for r in validation])
            models = {}
            for candidate in registry["candidates"]:
                model_start = time.perf_counter()
                model = estimator(candidate, manifest["sample_split_seed"])
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ConvergenceWarning)
                    model.fit(X, y)
                if any(issubclass(w.category, ConvergenceWarning) for w in caught):
                    raise RuntimeError("non-convergent candidate; entire fixed comparison stops, no silent dropping")
                prediction = model.predict(V)
                indices = np.arange(len(labels))
                rows.append({"fold_id": manifest["fold_id"], "seed": manifest["sample_split_seed"], "candidate": candidate["name"],
                    "accuracy": float(accuracy_score(target, prediction)), "balanced_accuracy": float(balanced_accuracy_score(target, prediction)),
                    "macro_f1": float(f1_score(target, prediction, labels=indices, average="macro", zero_division=0)),
                    "per_class_recall": dict(zip(labels, recall_score(target, prediction, labels=indices, average=None, zero_division=0).tolist())),
                    "confusion_matrix": confusion_matrix(target, prediction, labels=indices).tolist(), "n_validation": len(target),
                    "seconds": time.perf_counter()-model_start})
                models[candidate["name"]] = model
        audits.append({"fold_id": manifest["fold_id"], "manifest_checksum": manifest["manifest_checksum"],
            "scaler_fit_ids": [r["sample_id"] for r in train], "classifier_fit_ids": [r["sample_id"] for r in train],
            "model_selection_input_ids": [r["sample_id"] for r in validation], "test_selection_ids": [],
            "unknown_selection_ids": [], "seconds": time.perf_counter()-start,
            "historical_exposure": "this fold's train/validation were other historical folds' test; exploratory"})
        fitted.append({"scaler": scaler, "classifiers": models, "labels": labels, "fold_id": manifest["fold_id"]})
    selected, scores = select_candidate(rows, registry["candidates"])
    return {"selected_candidate": selected, "scores": scores, "fold_results": rows, "fit_audits": audits,
        "fitted": fitted, "registry_checksum": registry["registry_checksum"], "status": "selected_exploratory_not_final_validated",
        "selection_scope": "known validation only; equal-fold scores; no unknown/test loading or metric access"}


def lock_result(result: dict, registry: dict, manifests: list[dict], pools, output: Path) -> dict:
    artifacts, calibration_audits = [], []
    selected = result["selected_candidate"]
    for fitted, manifest in zip(result["fitted"], manifests, strict=True):
        by_id = {r["sample_id"]: r for r in manifest["records"]}
        train = [by_id[sid] for sid in manifest["sample_ids"]["train"]]
        cal = [by_id[sid] for sid in manifest["sample_ids"]["calibration"]]
        labels = fitted["labels"]
        if any(r["label"] not in labels for r in [*train, *cal]): raise ValueError("unknown in detector calibration")
        scaler = fitted["scaler"]
        with threadpool_limits(limits=1):
            X = scaler.transform(pools.load(train)); C = scaler.transform(pools.load(cal))
            y = np.array([labels.index(r["label"]) for r in train]); cy = np.array([labels.index(r["label"]) for r in cal])
            detectors = {method: create_openset_detector(method, **DETECTOR_CONFIG).fit(X, y, C, cy) for method in ("mahalanobis", "knn")}
        calibration_audits.append({"fold_id": manifest["fold_id"], "reference_ids": manifest["sample_ids"]["train"],
            "threshold_calibration_ids": manifest["sample_ids"]["calibration"], "threshold_inputs_known_only": True,
            "shared_validation_calibration": True, "dependence": "selection/calibration share known rows, no unbiased calibration claim",
            "class_summaries": {method: detector.class_summaries() for method, detector in detectors.items()}})
        fitted["detectors"] = detectors
        fitted["classifiers"] = {name: model for name, model in fitted["classifiers"].items() if name in {selected, "linear_baseline"}}
        path = output / f"training_{manifest['sample_split_seed']}.joblib"
        joblib.dump(fitted, path, compress=3)
        artifacts.append({"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "fold_id": manifest["fold_id"], "manifest_checksum": manifest["manifest_checksum"]})
    locked = seal({"schema_version": 1, "status": "locked", "locked_at": datetime.now(timezone.utc).isoformat(),
        "selected_candidate": selected, "selected_parameters": next(c["parameters"] for c in CANDIDATES if c["name"] == selected),
        "candidate_registry_checksum": registry["registry_checksum"], "feature_version": registry["feature_version"],
        "feature_audit_sha256": registry["feature_audit_sha256"], "exposure_ledger_checksum": registry["exposure_ledger_checksum"],
        "training_artifacts": artifacts, "training_artifact_sha256": hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest(),
        "selection_input_ids": sorted({sid for audit in result["fit_audits"] for sid in audit["model_selection_input_ids"]}),
        "training_records": [], "known_labels": result["fitted"][0]["labels"], "unknown_labels": manifests[0]["unknown_test_labels"],
        "minimum_test_samples_per_class": 30, "minimum_test_groups_per_class": 2,
        "expected_rpms": ["6000rpm", "8000rpm", "11000rpm"], "scope": "exploratory; historical physical contract unverified",
        "shared_validation_calibration": True}, "locked_checksum")
    # Full clean-source provenance is bound by the old manifests and exposure
    # ledger; original raw acquisition intervals cannot be invented in this lock.
    save_json(output / "locked_config.json", locked)
    audit_path = output / "fit_calibration_audits.json.gz"
    audit_path.write_bytes(gzip.compress(json.dumps({"fit": result["fit_audits"], "calibration": calibration_audits}, sort_keys=True).encode(), mtime=0))
    summary = {k: v for k, v in result.items() if k not in {"fitted", "fit_audits"}}
    summary["training_artifacts"] = artifacts
    summary["fit_calibration_audit"] = {"path": str(audit_path.resolve()), "sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest()}
    save_json(output / "selection_report.json", summary)
    return locked


def load_prior_manifests(matrix: Path) -> tuple[list[dict], list[str]]:
    state = json.loads((matrix / "run_status.json").read_bytes())
    plan = json.loads((matrix / "run_plan.json").read_bytes())
    role_id = plan["roles"][0]["split_id"]
    selected, paths = [], []
    for item in state["runs"].values():
        if item["method"] != "mahalanobis": continue
        manifest = read_split_manifest(item["manifest_path"])
        if manifest["class_split_id"] == role_id:
            selected.append(manifest); paths.append(item["manifest_path"])
            if len(selected) == 3:
                break
    ordered = sorted(zip(selected, paths), key=lambda p: [42, 123, 2026].index(p[0]["sample_split_seed"]))
    return [m for m, _ in ordered], [p for _, p in ordered]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--feature-audit", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--registry", type=Path)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_model_selection")
    manifests, manifest_paths = load_prior_manifests(args.matrix)
    feature_audit = json.loads(args.feature_audit.read_bytes())
    if len(feature_audit["checks"]) != 36 or any(c.get("adapter_clean_reproduction") is False for c in feature_audit["checks"]):
        raise ValueError("required computational feature audit incomplete or Stage2 reproduction failed")
    ledger = json.loads(gzip.decompress(args.ledger.read_bytes()))
    if args.prepare_only:
        registry = build_registry(manifests, ledger, hashlib.sha256(args.feature_audit.read_bytes()).hexdigest())
        registry["manifest_paths"] = manifest_paths
        registry = seal(registry, "registry_checksum")
        save_json(paths.output_dir / "candidate_registry.json", registry)
        log.info("Predeclared3 candidates; no models fitted; commit registry before training")
        return
    if not args.registry: parser.error("training requires a previously saved and committed --registry")
    registry = json.loads(args.registry.read_bytes()); verify_seal(registry, "registry_checksum")
    if registry["feature_audit_sha256"] != hashlib.sha256(args.feature_audit.read_bytes()).hexdigest() or registry["exposure_ledger_checksum"] != ledger["ledger_checksum"]:
        raise ValueError("feature audit or exposure version changed after preregistration")
    result = run(FeatureStore(args.data_root), manifests=manifests, registry=registry)
    locked = lock_result(result, registry, manifests, FeatureStore(args.data_root), paths.output_dir)
    save_json(paths.output_dir / "candidate_registry.json", registry)
    log.info("selected={} locked={}; known-validation only; final validation still pending", result["selected_candidate"], locked["locked_checksum"])


if __name__ == "__main__": main()
