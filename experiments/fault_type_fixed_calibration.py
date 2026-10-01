"""Fixed historical methods, dedicated calibration motor, no selector.

Exploratory only: all historical rows have prior test exposure. No fresh guard
or default detector is relaxed. Preparation never loads test feature values.
"""
from __future__ import annotations

import argparse
import gzip
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import sklearn
from threadpoolctl import threadpool_limits

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler

from core.fault_type_feature_contract import FEATURE_VERSION
from core.fault_type_final_guard import digest, seal, verify_seal
from core.fault_type_fixed_calibration import fixed_manifests, audit_fixed_fit, fixed_dependency
from core.fault_type_features import FeatureStore
from core.fault_type_manifest import write_split_manifest, read_split_manifest
from core.fault_type_validator import assert_valid_for_formal
from core.openset import create_openset_detector
from core.mahalanobis import _distances
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run
from experiments.fault_type_model_selection import load_prior_manifests
from experiments.fault_type_openset import CLASSIFIER_CONFIG, DETECTOR_CONFIG
from experiments.fault_type_representations import CANDIDATES
from experiments.fault_type_representations import Representation
from experiments.fault_type_metrics import evaluate_fault_type_predictions, _score_distribution

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


def check_protocol(protocol, manifests, ledger):
    verify_seal(protocol, "protocol_checksum")
    verify_seal(ledger, "ledger_checksum")
    if (protocol["selection_policy"] != "none" or protocol["selection_sample_ids"] or
        protocol["validation_sample_ids"] or protocol["shared_validation_calibration"] or
        protocol["seeds"] != SEEDS or protocol["methods"] != METHODS or
        protocol["classifier"] != CLASSIFIER_CONFIG or protocol["detectors"] != DETECTOR_CONFIG or
        protocol["representations"] != [c for c in CANDIDATES if c["name"] in ("baseline105", "vibration75")]):
        raise ValueError("predeclared no-selection budget changed")
    if digest(protocol["scaler_resolved"]) != digest(RobustScaler().get_params()) or digest(protocol["classifier_resolved"]) != digest(LogisticRegression(**CLASSIFIER_CONFIG).get_params()):
        raise ValueError("runtime resolved parameters differ from protocol")
    for item in protocol["implementation_sources"]:
        if _sha256_file(Path(item["path"])) != item["sha256"]:
            raise ValueError("shared implementation changed after preregistration")
    if ledger["ledger_checksum"] != protocol["exposure_ledger_checksum"]:
        raise ValueError("historical exposure mismatch")
    for m, binding in zip(manifests, protocol["folds"]):
        assert_valid_for_formal(m, allow_incomplete=True)
        if m["protocol_checksum"] != protocol["protocol_checksum"] or m["motor_roles"] != binding["motors"]:
            raise ValueError("fixed manifest protocol mismatch")
        for p, checksum in binding["partition_id_checksums"].items():
            if digest(m["sample_ids"][p]) != checksum:
                raise ValueError("fixed input IDs changed")
        if not set(m["sample_ids"]["test"]) <= set(ledger["sample_ids"]):
            raise ValueError("historical test exposure not recorded")
    if len(manifests) != 3:
        raise ValueError("three predeclared motor folds required")
    return fixed_dependency(manifests)


def verify_sources(root, manifest):
    """Fresh filesystem SHA scan before/after; FeatureStore cache is not evidence."""
    root = Path(root).resolve()
    sources = []
    for item in manifest["source_files"]:
        path = (root/item["source_file"]).resolve()
        if root not in path.parents or _sha256_file(path) != item["source_sha256"]:
            raise ValueError("source bytes changed or outside data root")
        sources.append(item["source_sha256"])
    import hashlib
    fingerprint = hashlib.sha256(json.dumps(sorted(sources),separators=(",",":")).encode()).hexdigest()
    if fingerprint != manifest["dataset_fingerprint"]:
        raise ValueError("dataset fingerprint changed")
    return {"file_count": len(sources), "dataset_fingerprint": fingerprint, "status": "VERIFIED_BYTES"}


def raw_class_scores(detector, X):
    """Read-only decomposition using the actual factory's distance functions."""
    if hasattr(detector, "distributions_"):
        items = detector.distributions_
        raw = np.column_stack([_distances(detector._transform(X), d.location, d.precision) for d in items])
    else:
        items = detector.models_
        raw = np.column_stack([detector._mean_neighbor_distance(d, X) for d in items])
    thresholds = np.array([d.threshold for d in items])
    ratios = raw / np.maximum(thresholds, np.finfo(float).eps)
    if not np.allclose(np.min(ratios, axis=1), detector.score_samples(X), rtol=1e-12, atol=1e-12):
        raise ValueError("diagnostic scores differ from factory")
    return raw, thresholds, ratios, [d.label for d in items]


def run(pools, *, manifests, protocol, ledger, output, code_head="engineering-test"):
    dependency = check_protocol(protocol, manifests, ledger)
    known = [protocol["healthy_label"], *sorted(protocol["known_fault_labels"])]
    artifacts, audits = [], []
    output.mkdir(parents=True, exist_ok=True)
    manifest_paths = []
    for m in manifests:
        path = write_split_manifest(m, output/"manifests")
        manifest_paths.append({"path": str(path.resolve()), "sha256": _sha256_file(path), "manifest_checksum": m["manifest_checksum"]})
    with threadpool_limits(limits=1):
        for m in manifests:
            by = {r["sample_id"]: r for r in m["records"]}
            train = [by[s] for s in m["sample_ids"]["train"]]
            cal = [by[s] for s in m["sample_ids"]["calibration"]]
            raw, calibration = pools.load(train), pools.load(cal)
            y = np.array([known.index(r["label"]) for r in train])
            cy = np.array([known.index(r["label"]) for r in cal])
            for seed in protocol["seeds"]:
                # Local generator established, but no random sampling is needed.
                np.random.default_rng(seed)
                for candidate in protocol["representations"]:
                    start = time.perf_counter()
                    transformer = Representation(candidate).fit(raw)
                    X, C = transformer.transform(raw), transformer.transform(calibration)
                    classifier = LogisticRegression(**protocol["classifier_resolved"]).fit(X, y)
                    detectors = {method: create_openset_detector(method, **protocol["detectors"]).fit(X, y, C, cy) for method in protocol["methods"]}
                    audit = {"schema_version": 2, "protocol_version": PROTOCOL, "protocol_checksum": protocol["protocol_checksum"],
                        "manifest_checksum": m["manifest_checksum"], "dataset_fingerprint": m["dataset_fingerprint"],
                        "fold_id": m["fold_id"], "motor_roles": m["motor_roles"], "seed": seed,
                        "representation": candidate["name"], "classifier": protocol["classifier_resolved"], "detectors": protocol["detectors"],
                        "selection_sample_ids": [], "selection_policy": "none", "shared_validation_calibration": False,
                        "calibration_sample_ids": [r["sample_id"] for r in cal],
                        "train_feature_digest": digest(raw.tolist()), "cal_feature_digest": digest(calibration.tolist()),
                        "transform_checksum": transformer.transform_checksum, "code_head": code_head,
                        "source_files": m["source_files"], "seconds": time.perf_counter()-start}
                    for key in ("scaler_fit_ids", "representation_fit_ids", "classifier_fit_ids", "reference_fit_ids", "covariance_fit_ids", "neighbor_reference_ids"):
                        audit[key] = [r["sample_id"] for r in train]
                    audit["input_validation"] = audit_fixed_fit(audit, m)
                    audit["detector_calibration"] = {method: d.class_summaries() for method,d in detectors.items()}
                    model = {"fold_id": m["fold_id"], "representation": candidate["name"], "seed": seed,
                             "labels": known, "transformer": transformer, "classifier": classifier, "detectors": detectors}
                    path = output/f"{m['fold_id']}_{candidate['name']}_seed{seed}.joblib"
                    joblib.dump(model, path, compress=3)
                    artifacts.append({"fold_id": m["fold_id"], "representation": candidate["name"], "seed": seed,
                        "path": str(path.resolve()), "sha256": _sha256_file(path), "manifest_checksum": m["manifest_checksum"]})
                    audits.append(audit)
    audit_path = output/"fit_audits.json.gz"
    audit_path.write_bytes(gzip.compress(json.dumps(audits, sort_keys=True, allow_nan=False).encode(), mtime=0))
    locked = seal({"status": "locked", "protocol_checksum": protocol["protocol_checksum"], "selection_policy": "none",
        "selection_sample_ids": [], "shared_validation_calibration": False, "known_labels": known,
        "unknown_labels": protocol["unknown_test_labels"], "training_artifacts": artifacts,
        "manifest_artifacts": manifest_paths, "fit_audit_artifact": {"path": str(audit_path.resolve()), "sha256": _sha256_file(audit_path)},
        "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__},
        "feature_version": protocol["feature_version"], "exposure_ledger_checksum": ledger["ledger_checksum"],
        "dependency": dependency, "fresh_final_test": False, "code_head": code_head}, "locked_checksum")
    save_json(output/"locked_methods.json", locked)
    return locked


def load_bound_model(artifact, trusted_root):
    path = Path(artifact["path"]).resolve()
    if Path(trusted_root).resolve() not in path.parents or _sha256_file(path) != artifact["sha256"]:
        raise ValueError("untrusted model path or model checksum mismatch")
    return joblib.load(path)


def evaluate(pools, *, manifests, protocol, ledger, locked, output, trusted_root):
    dependency = check_protocol(protocol, manifests, ledger)
    verify_seal(locked, "locked_checksum")
    if (locked["protocol_checksum"] != protocol["protocol_checksum"] or locked["selection_policy"] != "none" or
        locked["selection_sample_ids"] or locked["shared_validation_calibration"] or
        "selected_representation" in locked or "global_winner" in locked or
        locked["known_labels"] != [protocol["healthy_label"], *sorted(protocol["known_fault_labels"])] or
        locked["unknown_labels"] != protocol["unknown_test_labels"] or
        locked["exposure_ledger_checksum"] != ledger["ledger_checksum"]):
        raise ValueError("locked no-selection binding mismatch")
    if locked["environment"] != {"python": platform.python_version(), "sklearn": sklearn.__version__}:
        raise ValueError("model runtime differs from locked environment")
    if len(locked["training_artifacts"]) != 18:
        raise ValueError("all18 fixed fits required")
    audit_path = Path(locked["fit_audit_artifact"]["path"])
    if _sha256_file(audit_path) != locked["fit_audit_artifact"]["sha256"]:
        raise ValueError("fit audit checksum mismatch")
    audits = json.loads(gzip.decompress(audit_path.read_bytes()))
    by_fold = {m["fold_id"]: m for m in manifests}
    identities = {(m["fold_id"], c["name"], s) for m in manifests for c in protocol["representations"] for s in protocol["seeds"]}
    if {(a["fold_id"],a["representation"],a["seed"]) for a in locked["training_artifacts"]} != identities or len(audits) != 18:
        raise ValueError("incomplete fixed fit inventory")
    if {(a["fold_id"],a["representation"],a["seed"]) for a in audits} != identities:
        raise ValueError("fit audit inventory mismatch")
    for a in audits:
        audit_fixed_fit(a, by_fold[a["fold_id"]])
    output.mkdir(parents=True, exist_ok=True)
    runs = []
    known, unknown = locked["known_labels"], locked["unknown_labels"]
    with threadpool_limits(limits=1):
        for artifact in locked["training_artifacts"]:
            start = time.perf_counter()
            m = by_fold[artifact["fold_id"]]
            if artifact["manifest_checksum"] != m["manifest_checksum"]:
                raise ValueError("model manifest checksum mismatch")
            model = load_bound_model(artifact, trusted_root)
            if any(model[k] != artifact[k] for k in ("fold_id", "representation", "seed")):
                raise ValueError("model identity mismatch")
            audit = next(a for a in audits if (a["fold_id"],a["representation"],a["seed"]) ==
                         (artifact["fold_id"],artifact["representation"],artifact["seed"]))
            if (model["labels"] != known or model["classifier"].get_params() != protocol["classifier_resolved"] or
                model["transformer"].transform_checksum != audit["transform_checksum"] or
                model["transformer"].candidate != next(c for c in protocol["representations"] if c["name"]==artifact["representation"]) or
                {method: d.class_summaries() for method,d in model["detectors"].items()} != audit["detector_calibration"]):
                raise ValueError("model configuration or calibration differs from fixed audit")
            by = {r["sample_id"]: r for r in m["records"]}
            records = [by[s] for s in m["sample_ids"]["test"]]
            X = model["transformer"].transform(pools.load(records))
            prediction = model["classifier"].predict(X)
            for method in protocol["methods"]:
                detector = model["detectors"][method]
                raw, thresholds, ratios, labels = raw_class_scores(detector, X)
                scores, nearest = detector.score_samples(X), detector.nearest_known_class(X)
                if not np.isfinite(scores).all():
                    raise ValueError("nonfinite factory scores")
                name = f"{artifact['fold_id']}_{artifact['representation']}_{method}_seed{artifact['seed']}"
                rows = []
                for i,r in enumerate(records):
                    rows.append({"sample_id": r["sample_id"], "motor_id": r["t_code"], "rpm": r["rpm"],
                        "condition_id": r["t_code"]+"/"+r["rpm"], "group_id": r["group_id"], "source_file": r["source_file"],
                        "source_sha256": r["source_sha256"], "true_label": r["label"],
                        "true_role": "unknown_test" if r["label"] in unknown else "healthy" if r["label"] == known[0] else "known_fault",
                        "predicted_known_class": known[int(prediction[i])], "openset_score": float(scores[i]),
                        "is_unknown": bool(scores[i]>1), "accepted": bool(scores[i]<=1), "threshold": 1.0,
                        "final_class": "unknown" if scores[i]>1 else known[int(prediction[i])],
                        "nearest_known_class": known[int(nearest[i])],
                        "raw_class_scores": {known[int(c)]: float(raw[i,j]) for j,c in enumerate(labels)},
                        "class_thresholds": {known[int(c)]: float(thresholds[j]) for j,c in enumerate(labels)},
                        "normalized_class_scores": {known[int(c)]: float(ratios[i,j]) for j,c in enumerate(labels)},
                        "method_id": artifact["representation"]+"/"+method, "openset_method": method,
                        "representation": artifact["representation"], "seed": artifact["seed"], "fold_id": m["fold_id"],
                        "manifest_checksum": m["manifest_checksum"], "protocol_checksum": protocol["protocol_checksum"],
                        "locked_checksum": locked["locked_checksum"], "historical_test_exposed": True})
                path = output/(name+".jsonl.gz")
                path.write_bytes(gzip.compress("\n".join(json.dumps(r,sort_keys=True,allow_nan=False) for r in rows).encode(), mtime=0))
                metrics = metrics_for(rows, known, unknown)
                runs.append({"run_id": name, "fold_id": m["fold_id"], "motor_roles": m["motor_roles"],
                    "representation": artifact["representation"], "method": method, "seed": artifact["seed"],
                    "status": "completed", "samples": len(rows), "manifest_checksum": m["manifest_checksum"],
                    "test_ids_checksum": digest([r["sample_id"] for r in rows]), "metrics": metrics,
                    "rpm_metrics": [{"rpm": rpm, "metrics": metrics_for([r for r in rows if r["rpm"]==rpm],known,unknown)} for rpm in protocol["expected_rpms"]],
                    "configuration_metrics": [{"label": label, "samples": len(members),
                        "raw_classifier_accuracy": float(np.mean([r["predicted_known_class"]==label for r in members])) if label in known else None,
                        "rejection_rate": float(np.mean([r["is_unknown"] for r in members]))} for label in known+unknown
                        for members in [[r for r in rows if r["true_label"]==label]] if members],
                    "prediction_artifact": {"path": str(path.resolve()), "sha256": _sha256_file(path), "rows": len(rows)},
                    "seconds_including_shared_classifier_load": time.perf_counter()-start})
    result = seal({"schema_version": 2, "protocol_version": PROTOCOL, "protocol_checksum": protocol["protocol_checksum"],
        "locked_checksum": locked["locked_checksum"], "runs": runs, "completed_runs": len(runs), "failed_runs": [],
        "selection_policy": "none", "selection_sample_ids": [], "dependency": dependency,
        "scope": protocol["scope"], "fresh_final_test": False, "independent_validation_status": "INCOMPLETE",
        "known_labels": known, "unknown_labels": unknown}, "evaluation_checksum")
    save_json(output/"evaluation_report.json", result)
    return result


def metrics_for(rows, known, unknown):
    result = evaluate_fault_type_predictions(rows, healthy_label=known[0], known_labels=known,
        unknown_labels=unknown, known_fault_count=len(known)-1)
    result["unknown_prevalence"] = sum(r["true_label"] in unknown for r in rows)/len(rows)
    result["known_rejection_rate"] = 1-result["known_acceptance_rate"]
    truth = ["unknown" if r["true_label"] in unknown else r["true_label"] for r in rows]
    final = ["unknown" if r["is_unknown"] else r["predicted_known_class"] for r in rows]
    from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
    labels = known+["unknown"] if unknown else known
    result["final_open_set_classification"] = {"accuracy": float(accuracy_score(truth, final)),
        "macro_f1": float(f1_score(truth,final,labels=labels,average="macro",zero_division=0)),
        "confusion_matrix": confusion_matrix(truth,final,labels=labels).tolist(), "labels": labels}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "fit", "evaluate"])
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--prior-manifests", type=Path, nargs=3,
                        help="explicit predeclared existing N/class manifests in motor-role order")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--locked", type=Path)
    parser.add_argument("--code-head", default="engineering-test")
    args = parser.parse_args()
    log, paths = setup_run("fault_type_fixed_calibration")
    if bool(args.matrix) == bool(args.prior_manifests):
        parser.error("choose exactly one matrix or three explicit prior manifests")
    manifests = [read_split_manifest(p) for p in args.prior_manifests] if args.prior_manifests else load_prior_manifests(args.matrix)[0]
    ledger = json.loads(gzip.decompress(args.ledger.read_bytes()))
    if args.action == "prepare":
        protocol = build_protocol(manifests, ledger)
        save_json(paths.output_dir / "protocol.json", protocol)
        log.info("protocol={} checksum={}; no fit, commit before execution", PROTOCOL, protocol["protocol_checksum"])
        return
    if not args.protocol or not args.data_root:
        parser.error("fit/evaluate requires committed protocol and read-only data root")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    manifests = fixed_manifests(manifests, protocol)
    before = verify_sources(args.data_root, manifests[0])
    pools = FeatureStore(args.data_root)
    if args.action == "fit":
        result = run(pools, manifests=manifests, protocol=protocol, ledger=ledger, output=paths.output_dir, code_head=args.code_head)
        log.info("{} fixed fits sealed; no validation/test loaded; no selection", len(result["training_artifacts"]))
    else:
        if not args.locked:
            parser.error("evaluate requires sealed fixed-method lock")
        locked = json.loads(args.locked.read_text(encoding="utf-8"))
        result = evaluate(pools, manifests=manifests, protocol=protocol, ledger=ledger, locked=locked,
                          output=paths.output_dir, trusted_root=Path.cwd()/"output")
        log.info("{} paired exploratory evaluations complete; no fresh claim", result["completed_runs"])
    after = verify_sources(args.data_root, manifests[0])
    save_json(paths.output_dir/"source_verification.json", {"before": before, "after": after,
        "unchanged": before == after, "protocol_checksum": protocol["protocol_checksum"], "code_head": args.code_head})


if __name__ == "__main__":
    main()
