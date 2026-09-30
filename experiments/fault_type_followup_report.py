"""Verify saved post-lock predictions and describe matched fold differences."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_metrics import evaluate_fault_type_predictions


def paired_differences(runs: list[dict]) -> list[dict]:
    result = []
    for classifier in sorted({r["classifier"] for r in runs}):
        members = [r for r in runs if r["classifier"] == classifier]
        for seed in (42, 123, 2026):
            pair = {r["method"]: r for r in members if r["seed"] == seed}
            if set(pair) != {"mahalanobis", "knn"}:
                raise ValueError("unmatched detector fold")
            a, b = pair["mahalanobis"], pair["knn"]
            if a["manifest_checksum"] != b["manifest_checksum"] or a["test_ids_checksum"] != b["test_ids_checksum"]:
                raise ValueError("detector comparison test identity mismatch")
            unknown_a, unknown_b = a["metrics"]["unknown_rejection"], b["metrics"]["unknown_rejection"]
            result.append({"classifier": classifier, "seed": seed, "direction": "knn minus mahalanobis",
                "unknown_auroc_delta": unknown_b["auroc_unknown_positive"]-unknown_a["auroc_unknown_positive"],
                "unknown_recall_delta": unknown_b["unknown_recall"]-unknown_a["unknown_recall"],
                "healthy_fpr_delta": b["metrics"]["healthy_safety"]["false_positive_rate"]-a["metrics"]["healthy_safety"]["false_positive_rate"]})
    return result


def run(pools, *, locked: dict) -> dict:
    report = pools
    if report["locked_checksum"] != locked["locked_checksum"]:
        raise ValueError("evaluation/lock mismatch")
    for item in report["runs"]:
        artifact = item["prediction_artifact"]
        payload = Path(artifact["path"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != artifact["sha256"]:
            raise ValueError("prediction checksum mismatch")
        rows = [json.loads(line) for line in gzip.decompress(payload).splitlines()]
        if len(rows) != artifact["rows"] or any(r["locked_checksum"] != locked["locked_checksum"] for r in rows):
            raise ValueError("prediction count or lock binding mismatch")
        ids_digest = hashlib.sha256(json.dumps(sorted(r["sample_id"] for r in rows)).encode()).hexdigest()
        if ids_digest != item["test_ids_checksum"] or len({r["sample_id"] for r in rows}) != len(rows):
            raise ValueError("saved test IDs mismatch/duplicate")
        metrics = evaluate_fault_type_predictions(rows, healthy_label=locked["known_labels"][0],
            known_labels=locked["known_labels"], unknown_labels=locked["unknown_labels"], known_fault_count=5)
        if metrics != item["metrics"]:
            raise ValueError("saved metrics do not match actual predictions")
    classifiers = []
    for name in sorted({r["classifier"] for r in report["runs"]}):
        members = [r for r in report["runs"] if r["classifier"] == name and r["method"] == "mahalanobis"]
        if len(members) != 3: raise ValueError("all3 folds required")
        summary = {"classifier": name, "folds": []}
        for key in ("accuracy", "balanced_accuracy", "macro_f1"):
            values = [r["metrics"]["known_classification"][key] for r in members]
            summary[key] = {"equal_fold_mean": float(np.mean(values)), "minimum": min(values), "maximum": max(values)}
        summary["folds"] = [{"seed": r["seed"], "fold_id": r["fold_id"], **{key: r["metrics"]["known_classification"][key]
            for key in ("accuracy", "balanced_accuracy", "macro_f1")}} for r in members]
        classifiers.append(summary)
    detector_summaries = []
    for method in ("mahalanobis", "knn"):
        members = [r for r in report["runs"] if r["classifier"] == "linear_baseline" and r["method"] == method]
        detector_summaries.append({"method": method, "unknown_metrics_equal_fold_mean": {key: float(np.mean([r["metrics"]["unknown_rejection"][key] for r in members]))
            for key in ("auroc_unknown_positive", "aupr_unknown_positive", "unknown_recall", "unknown_precision", "unknown_f1", "fpr_at_95_tpr")},
            "healthy_false_positive_rate": float(np.mean([r["metrics"]["healthy_safety"]["false_positive_rate"] for r in members]))})
    # Classifier replacement must not be mistaken for a detector-score upgrade.
    for seed in (42, 123, 2026):
        for method in ("mahalanobis", "knn"):
            pair = [r for r in report["runs"] if r["seed"] == seed and r["method"] == method]
            if len(pair) != 2 or pair[0]["metrics"]["unknown_rejection"] != pair[1]["metrics"]["unknown_rejection"]:
                raise ValueError("unexpected detector metric change between unchanged feature/reference pipelines")
    return {"artifact_kind": "post_lock_exposed_test_reanalysis", "predictions_verified": len(report["runs"]),
        "classifiers": classifiers, "detectors": detector_summaries, "paired_detector_differences": paired_differences(report["runs"]),
        "fresh_final_test": False, "scope": report["qualification"]["status"],
        "production_default_changed": False, "all_original2490_runs_repeated": False,
        "limitations": report["limitations"], "unknown_scores_improved_by_classifier_change": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--locked", type=Path, required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_followup_report")
    result = run(json.loads(args.evaluation.read_bytes()), locked=json.loads(args.locked.read_bytes()))
    save_json(paths.output_dir / "verified_comparison.json", result)
    log.info("{} saved runs verified; exposed data only; production defaults unchanged", result["predictions_verified"])


if __name__ == "__main__": main()
