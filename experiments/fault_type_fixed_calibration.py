"""Fixed historical methods, dedicated calibration motor, no selector.

Exploratory only: all historical rows have prior test exposure. No fresh guard
or default detector is relaxed. Preparation never loads test feature values.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler

from core.fault_type_feature_contract import FEATURE_VERSION
from core.fault_type_final_guard import digest, seal, verify_seal
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run
from experiments.fault_type_model_selection import load_prior_manifests
from experiments.fault_type_openset import CLASSIFIER_CONFIG, DETECTOR_CONFIG
from experiments.fault_type_representations import CANDIDATES

PROTOCOL = "fixed_methods_motor_calibration_v1"
METHODS = ["mahalanobis", "knn"]
SEEDS = [0, 1, 2]


def build_protocol(manifests, ledger):
    verify_seal(ledger, "ledger_checksum")
    if len(manifests) != 3:
        raise ValueError("all three motor folds required")
    roles = {(tuple(m["known_fault_labels"]), tuple(m["unknown_test_labels"])) for m in manifests}
    if len(roles) != 1 or any(m["unknown_validation_labels"] for m in manifests):
        raise ValueError("one predeclared class manifest without unknown selection required")
    folds = []
    for i, m in enumerate(manifests):
        expected = {"train": str(i+1), "calibration": str((i+1)%3+1), "test": str((i+2)%3+1)}
        if any(m["campaigns"][k] != v for k, v in expected.items()):
            raise ValueError("original motor direction changed")
        folds.append({"fold": i, "motors": {k: "T"+v for k,v in expected.items()},
            "prior_manifest_checksum": m["manifest_checksum"],
            "partition_id_checksums": {k: digest(m["sample_ids"][k]) for k in expected},
            "counts": {k: len(m["sample_ids"][k]) for k in expected}})
    sources = ["experiments/fault_type_representations.py", "experiments/fault_type_openset.py",
               "core/openset.py", "core/mahalanobis.py"]
    return seal({"schema_version": 2, "protocol_version": PROTOCOL,
        "scope": "EXPLORATORY_HISTORICAL_TEST_EXPOSED", "fresh_final_test": False,
        "selection_policy": "none", "selection_sample_ids": [], "validation_sample_ids": [],
        "shared_validation_calibration": False, "seeds": SEEDS, "seed_effect": "algorithm seed only; no motor/window random split; lbfgs/LW/kNN deterministic",
        "representations": [c for c in CANDIDATES if c["name"] in ("baseline105", "vibration75")],
        "classifier": CLASSIFIER_CONFIG, "classifier_resolved": LogisticRegression(**CLASSIFIER_CONFIG).get_params(),
        "scaler_resolved": RobustScaler().get_params(), "detectors": DETECTOR_CONFIG, "methods": METHODS,
        "feature_version": FEATURE_VERSION, "dataset_fingerprint": manifests[0]["dataset_fingerprint"],
        "healthy_label": manifests[0]["healthy_label"], "known_fault_labels": manifests[0]["known_fault_labels"],
        "unknown_test_labels": manifests[0]["unknown_test_labels"], "folds": folds,
        "exposure_ledger_checksum": ledger["ledger_checksum"],
        "historical_exposure": "all28910 rows; prior method shortlist is retrospective, execution lock does not establish blindness",
        "implementation_sources": [{"path": p, "sha256": _sha256_file(Path(p))} for p in sources],
        "expected_rpms": ["6000rpm", "8000rpm", "11000rpm"],
        "conditions": [{"motor": "T"+str(i), "rpm": r} for i in (1,2,3) for r in ("6000rpm","8000rpm","11000rpm")],
        "condition_semantics": "nine observed motor/RPM pairs; each fold tests only three RPMs of one motor; loads UNKNOWN",
        "planned_evaluations": 36, "planned_classifier_fits": 18,
        "score_definition": "minimum across classes(raw distance/max(class .95 quantile, float epsilon)); unknown iff score>1",
        "metrics": ["known accuracy/balanced accuracy/macro-F1/per-class/confusion", "unknown AUROC/AP/prevalence/recall/precision/F1/FPR95",
                    "known rejection/healthy FPR/accepted-correct known rate/final open-set classification", "motor/RPM/configuration strata"],
        "summary": "fixed methods only; equal-motor descriptive mean/range; seed SD algorithm sensitivity, no IID window or motor population CI",
        "unused": "unknown rows on train/cal motors explicitly excluded; no global winner",
        "independence": "one test motor/class; minimum2 retained INCOMPLETE; sessions/raw intervals/physical conditions UNKNOWN"}, "protocol_checksum")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare"])
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_fixed_calibration")
    manifests, _ = load_prior_manifests(args.matrix)
    ledger = json.loads(gzip.decompress(args.ledger.read_bytes()))
    protocol = build_protocol(manifests, ledger)
    save_json(paths.output_dir / "protocol.json", protocol)
    log.info("protocol={} checksum={}; no fit, commit before execution", PROTOCOL, protocol["protocol_checksum"])


if __name__ == "__main__":
    main()
