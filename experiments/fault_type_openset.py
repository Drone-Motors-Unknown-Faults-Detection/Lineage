"""Train-only multiclass baseline and paired-factory open-set evaluation.

Protocol A never consumes an unknown except in final-test prediction. Protocol
B optionally describes a distinct unknown-validation label; neither existing
detector requires it and thresholds remain known-calibration-only.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler
from threadpoolctl import threadpool_limits

from core.fault_type_features import FeatureStore
from core.fault_type_manifest import read_split_manifest
from core.fault_type_validator import assert_valid_for_formal
from core.logger import setup_run
from core.openset import create_openset_detector, SUPPORTED_OPENSET_METHODS


CLASSIFIER_CONFIG = {"C": 1.0, "class_weight": "balanced", "solver": "lbfgs", "max_iter": 1000, "tol": 1e-4}
DETECTOR_CONFIG = {"confidence": 0.95, "mahalanobis_method": "ledoit_wolf", "knn_neighbors": 5}


def _load(pools, records: list[dict]) -> np.ndarray:
    values = np.asarray(pools.load(records), dtype=float)
    if values.shape != (len(records), 105) or not np.isfinite(values).all():
        raise ValueError("feature provider must return finite (n,105) matrices")
    return values


def run(pools, *, manifest: dict, openset_method: str = "mahalanobis",
        allow_incomplete: bool = False) -> dict:
    """Fit only train, calibrate only known calibration, then predict frozen test.

    ``pools`` is the read-only FeatureStore (or a fixture with ``load(records)``).
    Invalid manifests are rejected before the provider is called. Classifier
    hyperparameters are fixed before test; no test-based model selection occurs.
    """
    validator = assert_valid_for_formal(manifest, allow_incomplete=allow_incomplete)
    if manifest["protocol"] not in {"A", "B"}:
        raise ValueError("protocol must be A or B")
    if manifest["protocol"] == "A" and manifest["unknown_validation_labels"]:
        raise ValueError("Protocol A forbids unknown-validation roles")
    start = time.perf_counter()
    by_id = {r["sample_id"]: r for r in manifest["records"]}
    partitions = {s: [by_id[sid] for sid in manifest["sample_ids"][s]]
                  for s in ("train", "validation", "calibration", "test")}
    labels = [manifest["healthy_label"], *sorted(manifest["known_fault_labels"])]
    label_ids = {label: i for i, label in enumerate(labels)}
    train, cal = partitions["train"], partitions["calibration"]
    if any(r["label"] not in label_ids for r in [*train, *cal]):
        raise ValueError("unknown samples cannot enter model building or calibration")

    # Limiting numerical worker threads also makes runtime estimates comparable.
    with threadpool_limits(limits=1):
        scaler = RobustScaler().fit(_load(pools, train))
        X_train = scaler.transform(_load(pools, train))
        X_cal = scaler.transform(_load(pools, cal))
        y_train = np.asarray([label_ids[r["label"]] for r in train])
        y_cal = np.asarray([label_ids[r["label"]] for r in cal])
        classifier = LogisticRegression(**CLASSIFIER_CONFIG)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            classifier.fit(X_train, y_train)
        convergence_warnings = [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]
        if convergence_warnings:
            raise RuntimeError("fixed classifier did not converge: " + "; ".join(convergence_warnings))
        detector = create_openset_detector(openset_method, **DETECTOR_CONFIG)
        detector.fit(X_train, y_train, X_cal, y_cal)
        fit_seconds = time.perf_counter() - start

        validation_known = [r for r in partitions["validation"] if r["label"] in label_ids]
        validation_prediction = classifier.predict(scaler.transform(_load(pools, validation_known)))
        validation_accuracy = float(np.mean(validation_prediction == [label_ids[r["label"]] for r in validation_known]))
        unknown_validation = [r for r in partitions["validation"] if r["label"] not in label_ids]
        unknown_validation_diagnostic = None
        if unknown_validation:
            scores = detector.score_samples(scaler.transform(_load(pools, unknown_validation)))
            unknown_validation_diagnostic = {"n": len(scores), "recall_at_fixed_threshold": float(np.mean(scores > 1.0)),
                "used_for_fitting_or_selection": False}

        test = partitions["test"]
        X_test = scaler.transform(_load(pools, test))
        probabilities = classifier.predict_proba(X_test)
        best = np.argmax(probabilities, axis=1)
        classifier_prediction = classifier.classes_[best]
        scores = detector.score_samples(X_test)
        nearest = detector.nearest_known_class(X_test)

    predictions = []
    unknown_labels = set(manifest["unknown_test_labels"])
    for i, r in enumerate(test):
        true_role = "unknown_test" if r["label"] in unknown_labels else "healthy" if r["label"] == labels[0] else "known_fault"
        predictions.append({"sample_id": r["sample_id"], "group_id": r["group_id"],
            "source_file": r["source_file"], "rpm": r.get("rpm"), "stage": r.get("stage"),
            "true_label": r["label"], "true_role": true_role,
            "predicted_known_class": labels[int(classifier_prediction[i])],
            "classifier_confidence": float(probabilities[i, best[i]]),
            "classifier_probabilities": {labels[int(c)]: float(p) for c, p in zip(classifier.classes_, probabilities[i], strict=True)},
            "openset_method": openset_method, "openset_score": float(scores[i]), "threshold": 1.0,
            "is_unknown": bool(scores[i] > 1.0), "nearest_known_class": labels[int(nearest[i])],
            "calibration_version": "known-calibration-quantile-0.95-v1",
            "class_split_id": manifest["class_split_id"], "sample_split_id": manifest["split_id"],
            "seed": manifest["sample_split_seed"], "manifest_checksum": manifest["manifest_checksum"]})
    return {"run_id": manifest["split_id"] + "_" + openset_method, "status": "completed",
        "openset_method": openset_method, "protocol": manifest["protocol"],
        "known_fault_count": len(manifest["known_fault_labels"]), "healthy_label": labels[0],
        "known_labels": labels, "unknown_labels": manifest["unknown_test_labels"],
        "manifest_checksum": manifest["manifest_checksum"], "dataset_fingerprint": manifest["dataset_fingerprint"],
        "class_combination_id": manifest["class_combination_id"], "seed": manifest["sample_split_seed"],
        "git_commit": manifest["git_commit"], "validator": validator,
        "result_scope": "exploratory_incomplete" if validator["status"] == "INCOMPLETE" else "complete_split",
        "config": {"classifier": CLASSIFIER_CONFIG, "detector": DETECTOR_CONFIG, "features": "formal_105d", "preprocessing": "train_only_RobustScaler"},
        "fit_audit": {"scaler_fit_ids": manifest["sample_ids"]["train"],
            "classifier_fit_ids": manifest["sample_ids"]["train"], "detector_reference_ids": manifest["sample_ids"]["train"],
            "threshold_calibration_ids": manifest["sample_ids"]["calibration"],
            "pca_feature_selector_embedding": "not_used", "test_selection_ids": []},
        "classifier_iterations": classifier.n_iter_.tolist(), "validation_accuracy": validation_accuracy,
        "unknown_validation_diagnostic": unknown_validation_diagnostic,
        "class_calibration": detector.class_summaries(), "fit_seconds": fit_seconds,
        "elapsed_seconds": time.perf_counter() - start, "predictions": predictions}


def save_result(result: dict, root: Path | str) -> dict:
    """Persist actual probability fields, never invent unavailable logits."""
    root = Path(root) / result["run_id"]
    root.mkdir(parents=True, exist_ok=True)
    rows = result["predictions"]
    encoded = "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":"), allow_nan=False) for r in rows).encode()
    packed = gzip.compress(encoded, compresslevel=1, mtime=0)
    prediction_path = root / "predictions.jsonl.gz"
    prediction_path.write_bytes(packed)
    summary = {k: v for k, v in result.items() if k not in {"predictions", "fit_audit"}}
    summary["prediction_artifact"] = {"path": str(prediction_path.resolve()), "sha256": hashlib.sha256(packed).hexdigest(), "rows": len(rows)}
    audit = gzip.compress(json.dumps(result["fit_audit"], sort_keys=True).encode(), mtime=0)
    audit_path = root / "fit_audit.json.gz"
    audit_path.write_bytes(audit)
    summary["fit_audit_artifact"] = {"path": str(audit_path.resolve()), "sha256": hashlib.sha256(audit).hexdigest()}
    (root / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--openset-method", choices=SUPPORTED_OPENSET_METHODS, default="mahalanobis")
    parser.add_argument("--allow-incomplete", action="store_true", help="explicit exploratory mode; cannot support main independent-test claims")
    args = parser.parse_args()
    log, paths = setup_run("fault_type_openset")
    result = run(FeatureStore(args.data_root), manifest=read_split_manifest(args.manifest),
                 openset_method=args.openset_method, allow_incomplete=args.allow_incomplete)
    save_result(result, paths.output_dir)
    log.info("completed {} test predictions; scope={}; seconds={:.3f}", len(result["predictions"]), result["result_scope"], result["elapsed_seconds"])


if __name__ == "__main__":
    main()
