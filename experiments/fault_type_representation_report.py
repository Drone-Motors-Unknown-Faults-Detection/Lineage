"""Verify ALL saved representation predictions; describe dependent motor folds."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from core.fault_type_final_guard import verify_seal
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_metrics import evaluate_fault_type_predictions
from experiments.fault_type_followup_report import paired_differences


def run(pools, *, locked):
    report=pools; verify_seal(locked,"locked_checksum")
    if report["locked_checksum"]!=locked["locked_checksum"] or len(report["runs"])!=36 or report["failed_runs"]: raise ValueError("fixed36 inventory/lock incomplete")
    seen=set(); rows_total=0
    for item in report["runs"]:
        identity=(item["classifier"],item["seed"],item["method"])
        if identity in seen: raise ValueError("duplicate representation/fold/method")
        seen.add(identity); artifact=item["prediction_artifact"]; data=Path(artifact["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest()!=artifact["sha256"]: raise ValueError("prediction SHA mismatch")
        rows=[json.loads(line) for line in gzip.decompress(data).splitlines()]
        if len(rows)!=artifact["rows"] or len({r["sample_id"] for r in rows})!=len(rows): raise ValueError("prediction count/IDs mismatch")
        if any(r["locked_checksum"]!=locked["locked_checksum"] or r["manifest_checksum"]!=item["manifest_checksum"] or r["classifier"]!=item["classifier"] or r["openset_method"]!=item["method"] for r in rows): raise ValueError("prediction bindings mismatch")
        checksum=hashlib.sha256(json.dumps(sorted(r["sample_id"] for r in rows)).encode()).hexdigest()
        if checksum!=item["test_ids_checksum"]: raise ValueError("test IDs checksum mismatch")
        actual=evaluate_fault_type_predictions(rows,healthy_label=locked["known_labels"][0],known_labels=locked["known_labels"],unknown_labels=locked["unknown_labels"],known_fault_count=5)
        if actual!=item["metrics"]: raise ValueError("saved metrics differ from predictions")
        rows_total+=len(rows)
    for seed in [42,123,2026]:
        members=[r for r in report["runs"] if r["seed"]==seed]
        if len(members)!=12 or len({(r["manifest_checksum"],r["test_ids_checksum"]) for r in members})!=1: raise ValueError("representation comparison not paired on same test")
    summaries=[]
    for name in sorted({r["classifier"] for r in report["runs"]}):
        members=[r for r in report["runs"] if r["classifier"]==name]
        known=[r for r in members if r["method"]=="mahalanobis"]
        summary={"representation":name,"known":{},"detectors":[],"motor_folds":[],"motor_rpm_configuration_strata":[]}
        for key in ["accuracy","balanced_accuracy","macro_f1"]:
            values=[r["metrics"]["known_classification"][key] for r in known]
            summary["known"][key]={"equal_fold_mean":float(np.mean(values)),"minimum":min(values),"maximum":max(values)}
        for method in ["mahalanobis","knn"]:
            subset=[r for r in members if r["method"]==method]
            unknown={}
            for key in ["auroc_unknown_positive","aupr_unknown_positive","unknown_recall","unknown_precision","unknown_f1","fpr_at_95_tpr"]:
                values=[r["metrics"]["unknown_rejection"][key] for r in subset]
                unknown[key]={"equal_fold_mean":float(np.mean(values)),"minimum":min(values),"maximum":max(values)}
            healthy=[r["metrics"]["healthy_safety"]["false_positive_rate"] for r in subset]
            summary["detectors"].append({"method":method,"unknown":unknown,"healthy_fpr_equal_fold_mean":float(np.mean(healthy)),"healthy_acceptance_equal_fold_mean":1-float(np.mean(healthy))})
            for r in subset:
                summary["motor_folds"].append({"seed":r["seed"],"fold_id":r["fold_id"],"method":method,
                    "known":r["metrics"]["known_classification"],"unknown":r["metrics"]["unknown_rejection"],"healthy":r["metrics"]["healthy_safety"]})
                summary["motor_rpm_configuration_strata"].extend([{**s,"method":method,"seed":r["seed"]} for s in r["strata"]])
        summaries.append(summary)
    return {"status":"36_RUNS_VERIFIED","predictions_verified":36,"prediction_records":rows_total,
        "selected_before_test":locked["selected_representation"],"representations":summaries,"paired_detector_differences":paired_differences(report["runs"]),
        "scope":report["scope"],"fresh_final_test":False,"production_default_changed":False,
        "uncertainty":"folds/ranges descriptive;3motors, shared samples across representations/detectors; no motor population CI",
        "raw_alignment_comparison":"NOT_EXECUTED_NO_VERIFIED_RAW"}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--evaluation",type=Path,required=True); p.add_argument("--locked",type=Path,required=True)
    args=p.parse_args(); log,paths=setup_run("fault_type_representation_report")
    result=run(json.loads(args.evaluation.read_text(encoding="utf-8")),locked=json.loads(args.locked.read_text(encoding="utf-8")))
    save_json(paths.output_dir/"verified_comparison.json",result); log.info("{} prediction artifacts verified",result["predictions_verified"])


if __name__ == "__main__": main()
