"""Build a checksum-bound history from saved runs, without repeating training."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from core.fault_type_features import FeatureStore
from core.fault_type_sample_split import load_formal_catalog
from core.fault_type_manifest import read_split_manifest
from core.fault_type_provenance import save_json
from core.fault_type_final_guard import build_exposure_ledger
from core.logger import setup_run
from experiments.fault_type_matrix import _digest, verify_saved


def run(pools, *, matrices):
    records, catalog = load_formal_catalog(pools)
    test_ids, evidence, checked = set(), [], []
    for matrix in matrices:
        root = Path(matrix)
        plan_bytes = (root / "run_plan.json").read_bytes()
        plan = json.loads(plan_bytes)
        if plan["plan_checksum"] != _digest({k: v for k, v in plan.items() if k != "plan_checksum"}):
            raise ValueError("baseline plan checksum mismatch")
        if plan["dataset_fingerprint"] != catalog["dataset_fingerprint"]:
            raise ValueError("baseline data fingerprint mismatch")
        state = json.loads((root / "run_status.json").read_bytes())
        if state["plan_checksum"] != plan["plan_checksum"] or any(r["status"] != "completed" for r in state["runs"].values()):
            raise ValueError("baseline matrix unfinished or plan mismatch")
        first = next(iter(state["runs"].values()))
        manifest = read_split_manifest(first["manifest_path"])
        summary = json.loads(Path(first["summary_path"]).read_bytes())
        verify_saved(summary, manifest)
        checked.append({"matrix": str(root.resolve()), "runs": len(state["runs"]),
            "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(), "plan_checksum": plan["plan_checksum"],
            "checked_run": first["run_id"], "saved_predictions_metrics_check": "PASS"})
        # N9 closed-set rotations prove all catalog IDs have been final-test inputs.
        for item in state["runs"].values():
            if item["N"] == 9 and item["method"] == "mahalanobis":
                path = Path(item["manifest_path"])
                manifest = read_split_manifest(path)
                test_ids.update(manifest["sample_ids"]["test"])
                evidence.append({"manifest_path": str(path), "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "manifest_checksum": manifest["manifest_checksum"], "fold_id": manifest["fold_id"],
                    "test_count": len(manifest["sample_ids"]["test"]), "completed_run_id": item["run_id"]})
    ledger = build_exposure_ledger(records, FeatureStore(pools), test_ids=test_ids, evidence=evidence)
    return {"catalog": {k: v for k, v in catalog.items() if k != "files"}, "baseline_checks": checked,
        "ledger": ledger, "fresh_final_test_found": False,
        "reason": "Existing90CSV are all exposed; duplicate source ZIPs and unclean derivatives are not independent acquisitions."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True, action="append")
    args = parser.parse_args()
    log, paths = setup_run("fault_type_exposure")
    result = run(args.data_root, matrices=args.matrix)
    ledger = result.pop("ledger")
    packed = gzip.compress(json.dumps(ledger, sort_keys=True, separators=(",", ":")).encode(), mtime=0)
    path = paths.output_dir / "exposure_ledger.json.gz"
    path.write_bytes(packed)
    result["exposure_ledger"] = {"path": str(path.resolve()), "sha256": hashlib.sha256(packed).hexdigest(),
        "ledger_checksum": ledger["ledger_checksum"], "historical_test_sample_count": ledger["historical_test_sample_count"]}
    save_json(paths.output_dir / "exposure_index.json", result)
    log.info("{} historically tested samples; no fresh final test; {} saved matrices checked", ledger["historical_test_sample_count"], len(result["baseline_checks"]))


if __name__ == "__main__": main()
