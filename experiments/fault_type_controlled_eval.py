"""Post-lock paired evaluation. Old test data requires explicit exploratory mode.

Fresh incoming bundles must pass exposure/provenance gates; qualification
does not establish unrecorded physical compatibility of historical training.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import joblib
import numpy as np
from threadpoolctl import threadpool_limits
from core.fault_type_final_guard import FinalTestBlocked, verify_seal, guard_final_test, record_final_exposure
from core.fault_type_features import FeatureStore
from core.fault_type_manifest import read_split_manifest
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_metrics import evaluate_fault_type_predictions
from experiments.fault_type_model_selection import load_prior_manifests


def _check_locked(locked, ledger):
    verify_seal(locked, "locked_checksum"); verify_seal(ledger, "ledger_checksum")
    if locked.get("status") != "locked" or locked.get("exposure_ledger_checksum") != ledger["ledger_checksum"]:
        raise FinalTestBlocked("model not locked against current exposure history")


def run(pools, *, manifests, locked, ledger, fitted, exploratory=False, incoming_bundle=None, claim=None, exposure_sink=None):
    _check_locked(locked, ledger)
    if incoming_bundle is None and not exploratory:
        raise FinalTestBlocked("existing previously exposed test requires explicit exploratory flag")
    qualification = guard_final_test(incoming_bundle, ledger, locked, claim=claim) if incoming_bundle is not None else {
        "status": "EXPLORATORY_HISTORICAL_TEST_EXPOSED", "fresh_final_test": False}
    if len(manifests) != len(fitted) or len(fitted) != 3:
        raise ValueError("all3 predeclared folds must be included; do not select best seed")
    exposure_receipt = None
    if incoming_bundle is not None:
        if exposure_sink is None:
            raise FinalTestBlocked("fresh evaluation requires durable exposure registration before any test prediction")
        updated = record_final_exposure(ledger, incoming_bundle, evaluation_id=locked["locked_checksum"]+":"+incoming_bundle["data_version_checksum"])
        exposure_sink(updated)  # Failure must block prediction, not be ignored.
        exposure_receipt = {"ledger_checksum": updated["ledger_checksum"], "registered_before_prediction": True}
    results, prediction_sets = [], {}
    for manifest, model in zip(manifests, fitted, strict=True):
        artifact = next(a for a in locked["training_artifacts"] if a["fold_id"] == manifest["fold_id"])
        if artifact["manifest_checksum"] != manifest["manifest_checksum"] or model["fold_id"] != manifest["fold_id"]:
            raise ValueError("locked fit/fold mismatch")
        known, unknown = locked["known_labels"], locked["unknown_labels"]
        if incoming_bundle is None:
            by_id = {r["sample_id"]: r for r in manifest["records"]}
            records = [by_id[sid] for sid in manifest["sample_ids"]["test"]]
        else:
            records = incoming_bundle["records"]
        with threadpool_limits(limits=1):
            X = model["scaler"].transform(pools.load(records))
            for name, classifier in model["classifiers"].items():
                prediction = classifier.predict(X)
                probabilities = classifier.predict_proba(X) if hasattr(classifier, "predict_proba") else None
                for method in ("mahalanobis", "knn"):
                    detector = model["detectors"][method]
                    scores = detector.score_samples(X); nearest = detector.nearest_known_class(X)
                    rows = []
                    for i, record in enumerate(records):
                        label = record["label"]
                        role = "unknown_test" if label in unknown else "healthy" if label == known[0] else "known_fault"
                        rows.append({"sample_id": record["sample_id"], "group_id": record.get("group_id", record.get("session_id")),
                            "source_file": record.get("source_file", record.get("feature_source")), "rpm": record.get("rpm"),
                            "motor_id": record.get("t_code", record.get("motor_id")), "true_label": label, "true_role": role,
                            "predicted_known_class": known[int(prediction[i])], "classifier": name,
                            "classifier_probabilities": {known[int(c)]: float(p) for c, p in zip(classifier.classes_, probabilities[i], strict=True)} if probabilities is not None else None,
                            "probability_unavailable_reason": None if probabilities is not None else "SVM probability=False; margin is not a probability",
                            "openset_score": float(scores[i]), "is_unknown": bool(scores[i] > 1.), "threshold": 1.,
                            "nearest_known_class": known[int(nearest[i])], "openset_method": method,
                            "manifest_checksum": manifest["manifest_checksum"], "locked_checksum": locked["locked_checksum"],
                            "feature_version": locked["feature_version"], "seed": manifest["sample_split_seed"],
                            "evaluation_scope": qualification["status"]})
                    metrics = evaluate_fault_type_predictions(rows, healthy_label=known[0], known_labels=known,
                        unknown_labels=unknown, known_fault_count=5)
                    strata = defaultdict(list)
                    for row in rows: strata[(row["motor_id"], row["rpm"], row["true_label"])].append(row)
                    stratified = [{"motor_id": motor, "rpm": rpm, "configuration": label, "samples": len(members),
                        "classification_accuracy": float(np.mean([r["predicted_known_class"] == r["true_label"] for r in members])) if label in known else None,
                        "unknown_rejection_rate": float(np.mean([r["is_unknown"] for r in members]))}
                        for (motor, rpm, label), members in sorted(strata.items())]
                    run_id = f"{manifest['sample_split_seed']}_{name}_{method}"
                    prediction_sets[run_id] = rows
                    results.append({"run_id": run_id, "fold_id": manifest["fold_id"], "seed": manifest["sample_split_seed"],
                        "classifier": name, "method": method, "manifest_checksum": manifest["manifest_checksum"],
                        "test_ids_checksum": hashlib.sha256(json.dumps(sorted(r["sample_id"] for r in rows)).encode()).hexdigest(),
                        "metrics": metrics, "strata": stratified, "status": "completed"})
    return {"qualification": qualification, "exposure_receipt": exposure_receipt, "locked_checksum": locked["locked_checksum"], "runs": results,
        "predictions": prediction_sets, "failed_runs": [], "final_independent_validation_completed": incoming_bundle is not None,
        "limitations": ["Shared known validation/calibration and historically exposed development data.",
            "Only3 motor folds; list folds/ranges, not window bootstrap population CIs.",
            "Same scaler/reference/calibration makes detector scores unchanged between classifiers; classification improvement alone does not improve unknown AUROC.",
            "Fresh data eligibility does not establish unverified physical compatibility of old training." ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--locked", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--exploratory", action="store_true")
    args = parser.parse_args()
    log, paths = setup_run("fault_type_controlled_eval")
    locked = json.loads(args.locked.read_bytes()); ledger = json.loads(gzip.decompress(args.ledger.read_bytes()))
    _check_locked(locked, ledger)
    if not args.exploratory: raise FinalTestBlocked("CLI currently accepts only historical exploratory evaluation; use guarded API for separately preregistered fresh bundle")
    manifests, _ = load_prior_manifests(args.matrix)
    fitted = []
    output_root = (Path.cwd() / "output").resolve()
    for artifact in locked["training_artifacts"]:
        path = Path(artifact["path"]).resolve()
        if output_root not in path.parents or hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
            raise FinalTestBlocked("training artifact outside trusted local output root or checksum mismatch")
        # Only load artifacts generated by this project and bound to its lock.
        fitted.append(joblib.load(path))
    result = run(FeatureStore(args.data_root), manifests=manifests, locked=locked, ledger=ledger, fitted=fitted, exploratory=True)
    for run_id, rows in result.pop("predictions").items():
        packed = gzip.compress("\n".join(json.dumps(r, sort_keys=True, allow_nan=False) for r in rows).encode(), mtime=0)
        path = paths.output_dir / f"{run_id}_predictions.jsonl.gz"; path.write_bytes(packed)
        next(r for r in result["runs"] if r["run_id"] == run_id)["prediction_artifact"] = {"path": str(path.resolve()), "sha256": hashlib.sha256(packed).hexdigest(), "rows": len(rows)}
    save_json(paths.output_dir / "evaluation_report.json", result)
    log.info("{} paired exploratory runs complete; fresh final validation NOT completed", len(result["runs"]))


if __name__ == "__main__": main()
