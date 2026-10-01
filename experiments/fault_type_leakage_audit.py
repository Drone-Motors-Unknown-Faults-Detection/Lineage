"""Audit all formal features and frozen primary motor folds without refitting.

Reuses catalog, FeatureStore, validator, ledger seal and saved-prediction
verifier. Findings do NOT rewrite old manifests or certify acquisition facts.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import time
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import verify_seal, digest
from core.fault_type_leakage import numeric_duplicates, selection_dependency, audit_fit_ids, paired_saved_metrics
from core.fault_type_provenance import save_json
from core.fault_type_sample_split import load_formal_catalog
from core.fault_type_validator import validate_split_manifest
from core.formal_data import _sha256_file
from core.logger import setup_run
from experiments.fault_type_model_selection import load_prior_manifests
from experiments.fault_type_representation_report import run as verify_predictions


def run(pools, *, records, catalog, manifests, fit_audits, ledger, verified_predictions):
    verify_seal(ledger, "ledger_checksum")
    if {r["sample_id"] for r in records} != set(ledger["sample_ids"]):
        raise ValueError("historical exposure ledger does not exactly cover current catalog")
    if len(manifests) != 3 or {m["sample_split_seed"] for m in manifests} != {42, 123, 2026}:
        raise ValueError("all3 frozen primary motor folds required")
    if any(m["dataset_fingerprint"] != catalog["dataset_fingerprint"] for m in manifests):
        raise ValueError("catalog/frozen manifest fingerprint mismatch")
    values = pools.load(records)  # every row fingerprint/source SHA checked
    duplicates, semantic_groups = numeric_duplicates(records, values)
    source_groups = defaultdict(list)
    for item in catalog["files"]:
        if ledger["files"].get(item["source_file"]) != item["source_sha256"]:
            raise ValueError("exposure/current file binding mismatch")
        source_groups[item["source_sha256"]].append(item["source_file"])
    folds = []
    for m in manifests:
        validation = validate_split_manifest(m)
        ids = {name: set(value) for name, value in m["sample_ids"].items()}
        copy_groups = []
        for key, group in semantic_groups.items():
            members = {r["sample_id"] for r in group}
            splits = {name for name, assigned in ids.items() if assigned & members}
            if len(splits) > 1 and splits != {"validation", "calibration"}:
                copy_groups.append(key)
        folds.append({"fold_id": m["fold_id"], "seed_is_fold_identifier": m["sample_split_seed"],
            "manifest_checksum": m["manifest_checksum"], "validator": validation,
            "test_fit_input_id_overlap": len(ids["test"] & (ids["train"] | ids["validation"] | ids["calibration"])),
            "shared_validation_calibration_rows": len(ids["validation"] & ids["calibration"]),
            "potential_cross_partition_12g_copy_groups": len(copy_groups),
            "copy_groups_checksum": digest(sorted(copy_groups))})
    independence = selection_dependency(manifests)
    fit = audit_fit_ids(fit_audits, manifests)
    unknown_fields = {key: sum(r.get(key) is None or r.get(key) == "" for r in records) for key in
                      ("session_id", "run_id", "acquisition_timestamp", "raw_source_file", "source_interval")}
    failures = []
    if fit["status"] != "PASS": failures.append("fit audit inventory or input binding failed")
    if any(f["validator"]["status"] == "INVALID" for f in folds): failures.append("frozen split has confirmed validator violations")
    return {"status": "AUDIT_COMPLETED_WITH_LIMITATIONS" if not failures else "AUDIT_COMPLETED_WITH_CONFIRMED_VIOLATIONS",
        "file_count": catalog["file_count"], "sample_count": len(records), "dataset_fingerprint": catalog["dataset_fingerprint"],
        "file_byte_alias_groups": [{"sha256": k, "paths": sorted(v)} for k, v in sorted(source_groups.items()) if len(v) > 1],
        "numeric_duplicates": duplicates, "folds": folds, "fit_input_audit": fit,
        "global_selection_dependence": independence, "missing_provenance_counts": unknown_fields,
        "historical_final_exposure_rows": len(set(ledger["sample_ids"])),
        "verified": ["Actual90file/105D/row fingerprint and exposure source binding checked",
            "Saved36predictions SHA/IDs/metrics and paired manifests verified without refitting",
            "Within-fold fit/reference/selection/calibration ID audits inspected"],
        "not_passed": [*failures, "Independent final-test eligibility: all historical samples exposed",
            "Global selected model independent outer-test claim: cross-fold validation reuse",
            "Independent validation/calibration claim: same known rows shared",
            "At least2independent test motor groups/class: only1 documented motor per fold"],
        "cannot_confirm": ["Raw-window overlap and session/run independence: metadata missing",
            "Actual fs/shared clock/units/orientation/calibration/mount/load",
            "No acquisition leakage from absence of identical numeric vectors",
            "Train-only deployable cleaning: historical per-file cleaning used full file distributions; deleted DAQ cannot be recovered here"],
        "comparison": paired_saved_metrics(verified_predictions),
        "fresh_final_test": False, "production_default_changed": False, "formal_sources_modified": False,
        "scope": "Entire formal catalog; first preregistered N5/all3 frozen motor folds/18fit audits/36saved predictions. No2490rerun.",
        "frozen_artifacts_policy": "Overlay findings only; prior manifests, audits, predictions and locks remain unchanged."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("data-root", "matrix", "ledger", "fit-audits", "evaluation", "locked"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_leakage_audit")
    start = time.perf_counter()
    records, catalog = load_formal_catalog(args.data_root)
    manifests, manifest_paths = load_prior_manifests(args.matrix)
    ledger = json.loads(gzip.decompress(args.ledger.read_bytes()))
    audits = json.loads(gzip.decompress(args.fit_audits.read_bytes()))
    locked = json.loads(args.locked.read_text(encoding="utf-8"))
    evaluation = json.loads(args.evaluation.read_text(encoding="utf-8"))
    if {a["manifest_checksum"] for a in locked["training_artifacts"]} != {m["manifest_checksum"] for m in manifests}:
        raise ValueError("saved models and audited manifests differ")
    if any(r["manifest_checksum"] != next(m["manifest_checksum"] for m in manifests
           if m["sample_split_seed"] == r["seed"]) for r in evaluation["runs"]):
        raise ValueError("saved evaluation and audited manifest binding mismatch")
    for artifact in locked["training_artifacts"]:
        if _sha256_file(Path(artifact["path"])) != artifact["sha256"]:
            raise ValueError("saved model artifact SHA changed; no unverified comparison")
    verified = verify_predictions(evaluation, locked=locked)
    result = run(FeatureStore(args.data_root), records=records, catalog=catalog, manifests=manifests,
                 fit_audits=audits, ledger=ledger, verified_predictions=verified)
    result["input_artifacts"] = [{"path": str(path.resolve()), "sha256": _sha256_file(path)} for path in
                                [args.ledger, args.fit_audits, args.evaluation, args.locked, *map(Path, manifest_paths)]]
    result["saved_prediction_verification"] = {"runs": verified["predictions_verified"], "rows": verified["prediction_records"]}
    result["seconds"] = time.perf_counter()-start
    save_json(paths.output_dir/"audit.json", result)
    save_json(paths.output_dir/"source_checksums.json", catalog)
    log.info("status={} files={} rows={} seconds={:.2f}; no refit, no fresh claim", result["status"], result["file_count"], result["sample_count"], result["seconds"])


if __name__ == "__main__":
    main()
