"""Predeclared representation-only exploratory study; no fresh-data claims.

Fixed original balanced linear classifier, same manifests and factory detectors.
Selection sees known validation only; evaluation requires committed locked fit.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import platform
import time
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,recall_score,confusion_matrix
from threadpoolctl import threadpool_limits
from core.fault_type_features import FeatureStore
from core.fault_type_feature_contract import FEATURE_VERSION
from core.fault_type_final_guard import seal,verify_seal,digest
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run
from core.openset import create_openset_detector
from experiments.fault_type_model_selection import load_prior_manifests
from experiments.fault_type_openset import CLASSIFIER_CONFIG,DETECTOR_CONFIG
from experiments.fault_type_controlled_eval import paired_predictions

CANDIDATES=[
    {"name":"baseline105","indices":list(range(105)),"pca_components":None,"tie_rank":0},
    {"name":"vibration75","indices":list(range(15,90)),"pca_components":None,"tie_rank":3},
    {"name":"current15","indices":list(range(15)),"pca_components":None,"tie_rank":1},
    {"name":"delta_t15","indices":list(range(90,105)),"pca_components":None,"tie_rank":2},
    {"name":"vibration_current90","indices":list(range(90)),"pca_components":None,"tie_rank":4},
    {"name":"train_pca20","indices":list(range(105)),"pca_components":20,"tie_rank":5},
]


class Representation:
    def __init__(self,candidate): self.candidate=candidate; self.n_features_in_=105
    def fit(self,X):
        self.scaler=RobustScaler().fit(X[:,self.candidate["indices"]])
        transformed=self.scaler.transform(X[:,self.candidate["indices"]])
        self.pca=PCA(n_components=self.candidate["pca_components"],svd_solver="full").fit(transformed) if self.candidate["pca_components"] else None
        self.transform_checksum=digest({"candidate":self.candidate,"center":self.scaler.center_.tolist(),"scale":self.scaler.scale_.tolist(),
            "pca_mean":self.pca.mean_.tolist() if self.pca else None,"pca_components":self.pca.components_.tolist() if self.pca else None})
        return self
    def transform(self,X):
        result=self.scaler.transform(X[:,self.candidate["indices"]])
        return self.pca.transform(result) if self.pca else result


def build_registry(manifests):
    if len(manifests)!=3 or {m["sample_split_seed"] for m in manifests}!={42,123,2026}:
        raise ValueError("all3 prior motor folds required")
    if any(len(m["known_fault_labels"])!=5 or len(m["unknown_test_labels"])!=4 for m in manifests): raise ValueError("N5roles required")
    if len({(tuple(m["known_fault_labels"]),tuple(m["unknown_test_labels"])) for m in manifests})!=1: raise ValueError("same class roles required")
    return seal({"schema_version":1,"candidates":CANDIDATES,"feature_version":FEATURE_VERSION,
        "implementation_sha256":hashlib.sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
        "classifier":CLASSIFIER_CONFIG,"detectors":DETECTOR_CONFIG,
        "feature_contract":"Current0:15/X15:40/Y40:65/Z65:90/Delta_T90:105 zero-based",
        "dataset_fingerprint":manifests[0]["dataset_fingerprint"],
        "manifests":[{"manifest_checksum":m["manifest_checksum"],"fold_id":m["fold_id"],"seed":m["sample_split_seed"],
            "partition_id_checksums":{p:digest(ids) for p,ids in m["sample_ids"].items()}} for m in manifests],
        "selection_rule":"equal-fold known-validation macro-F1, then balanced accuracy, then fixed tie_rank; tolerance1e-12",
        "hyperparameter_budget":"one fixed classifier per representation/fold; PCA20 fixed, full deterministic SVD",
        "scope":"EXPLORATORY_ALL_HISTORICAL_SAMPLES_EXPOSED","shared_validation_calibration":True,
        "planned_test":"all6representations x3folds x2detectors after lock, preserve all results; not2490rerun",
        "raw_alignment_ablation":"NOT_AVAILABLE_NO_VERIFIED_RAW; processed channels not relabeled synchronized"},"registry_checksum")


def _check(manifests,registry):
    verify_seal(registry,"registry_checksum")
    if registry["implementation_sha256"]!=hashlib.sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(): raise ValueError("representation implementation changed after preregistration")
    if registry["candidates"]!=CANDIDATES or registry["classifier"]!=CLASSIFIER_CONFIG or registry["detectors"]!=DETECTOR_CONFIG:
        raise ValueError("predeclared representation/model budget changed")
    if [m["manifest_checksum"] for m in manifests]!=[m["manifest_checksum"] for m in registry["manifests"]]: raise ValueError("manifest binding mismatch")


def run(pools, *, manifests,registry,output):
    _check(manifests,registry)
    rows,artifacts,audits=[],[],[]
    known=[manifests[0]["healthy_label"],*sorted(manifests[0]["known_fault_labels"])]
    unknown=manifests[0]["unknown_test_labels"]
    # Validate ALL fold roles before fitting any transform/model.
    for m in manifests:
        by={r["sample_id"]:r for r in m["records"]}
        if any(by[s]["label"] not in known for p in ["train","validation","calibration"] for s in m["sample_ids"][p]): raise ValueError("unknown input in representation selection/calibration")
        if set(m["sample_ids"]["test"]) & set(m["sample_ids"]["train"]+m["sample_ids"]["validation"]+m["sample_ids"]["calibration"]): raise ValueError("within-fold test leakage")
    with threadpool_limits(limits=1):
        for m in manifests:
            by={r["sample_id"]:r for r in m["records"]}
            train=[by[s] for s in m["sample_ids"]["train"]]; validation=[by[s] for s in m["sample_ids"]["validation"]]; cal=[by[s] for s in m["sample_ids"]["calibration"]]
            raw=pools.load(train); val=pools.load(validation); calibration=pools.load(cal)
            y=np.array([known.index(r["label"]) for r in train]); vy=np.array([known.index(r["label"]) for r in validation]); cy=np.array([known.index(r["label"]) for r in cal])
            for candidate in CANDIDATES:
                start=time.perf_counter(); transformer=Representation(candidate).fit(raw)
                X,V,C=transformer.transform(raw),transformer.transform(val),transformer.transform(calibration)
                classifier=LogisticRegression(**CLASSIFIER_CONFIG).fit(X,y)
                predicted=classifier.predict(V)
                rows.append({"representation":candidate["name"],"fold_id":m["fold_id"],"seed":m["sample_split_seed"],
                    "accuracy":float(accuracy_score(vy,predicted)),"balanced_accuracy":float(balanced_accuracy_score(vy,predicted)),
                    "macro_f1":float(f1_score(vy,predicted,labels=range(6),average="macro",zero_division=0)),
                    "per_class_recall":dict(zip(known,recall_score(vy,predicted,labels=range(6),average=None,zero_division=0).tolist())),
                    "confusion_matrix":confusion_matrix(vy,predicted,labels=range(6)).tolist(),"n_features":X.shape[1],"seconds":time.perf_counter()-start})
                detectors={method:create_openset_detector(method,**DETECTOR_CONFIG).fit(X,y,C,cy) for method in ["mahalanobis","knn"]}
                audit={"representation":candidate["name"],"fold_id":m["fold_id"],"selected_indices":candidate["indices"],"transform_checksum":transformer.transform_checksum,
                    "train_only_transform_fit_ids":m["sample_ids"]["train"],"classifier_fit_ids":m["sample_ids"]["train"],"reference_ids":m["sample_ids"]["train"],
                    "selection_ids":m["sample_ids"]["validation"],"calibration_ids":m["sample_ids"]["calibration"],"test_selection_ids":[],"unknown_selection_ids":[],
                    "shared_validation_calibration":True}
                model={"fold_id":m["fold_id"],"labels":known,"scaler":transformer,"classifiers":{candidate["name"]:classifier},"detectors":detectors}
                path=output/f"{candidate['name']}_{m['sample_split_seed']}.joblib"; joblib.dump(model,path,compress=3)
                artifacts.append({"representation":candidate["name"],"fold_id":m["fold_id"],"path":str(path.resolve()),"sha256":_sha256_file(path),"manifest_checksum":m["manifest_checksum"]}); audits.append(audit)
    scores=[]
    for candidate in CANDIDATES:
        members=[r for r in rows if r["representation"]==candidate["name"]]
        scores.append({"representation":candidate["name"],"macro_f1":float(np.mean([r["macro_f1"] for r in members])),"balanced_accuracy":float(np.mean([r["balanced_accuracy"] for r in members])),"tie_rank":candidate["tie_rank"]})
    eligible=[r for r in scores if r["macro_f1"]>=max(r["macro_f1"] for r in scores)-1e-12]
    eligible=[r for r in eligible if r["balanced_accuracy"]>=max(r["balanced_accuracy"] for r in eligible)-1e-12]
    selected=min(eligible,key=lambda r:r["tie_rank"])["representation"]
    locked=seal({"status":"locked","selected_representation":selected,"registry_checksum":registry["registry_checksum"],
        "feature_version":FEATURE_VERSION,"known_labels":known,"unknown_labels":unknown,"training_artifacts":artifacts,
        "environment":{"python":platform.python_version(),"sklearn":sklearn.__version__},"scope":registry["scope"]},"locked_checksum")
    save_json(output/"locked_config.json",locked); save_json(output/"selection_report.json",{"scores":scores,"fold_results":rows,"selected_representation":selected,"test_loaded":False})
    (output/"fit_audits.json.gz").write_bytes(gzip.compress(json.dumps(audits,sort_keys=True).encode(),mtime=0))
    return locked


def evaluate(pools, *, manifests,registry,locked,output):
    _check(manifests,registry); verify_seal(locked,"locked_checksum")
    if locked.get("status")!="locked" or locked["registry_checksum"]!=registry["registry_checksum"]: raise ValueError("unlocked/mismatched representation selection")
    if locked["environment"]!={"python":platform.python_version(),"sklearn":sklearn.__version__}: raise ValueError("representation joblibs require same environment")
    results=[]
    for candidate in CANDIDATES:
        models=[]
        for m in manifests:
            item=next(a for a in locked["training_artifacts"] if a["representation"]==candidate["name"] and a["fold_id"]==m["fold_id"])
            path=Path(item["path"]).resolve()
            if (Path.cwd()/"output").resolve() not in path.parents or _sha256_file(path)!=item["sha256"]: raise ValueError("untrusted representation artifact/hash")
            models.append(joblib.load(path))
        result=paired_predictions(pools,manifests=manifests,locked=locked,fitted=models,qualification={"status":registry["scope"],"fresh_final_test":False})
        for run_id,predictions in result.pop("predictions").items():
            data=gzip.compress("\n".join(json.dumps(r,sort_keys=True,allow_nan=False) for r in predictions).encode(),mtime=0)
            path=output/f"{run_id}.jsonl.gz"; path.write_bytes(data)
            next(r for r in result["runs"] if r["run_id"]==run_id)["prediction_artifact"]={"path":str(path.resolve()),"sha256":hashlib.sha256(data).hexdigest(),"rows":len(predictions)}
        results.extend(result["runs"])
    report={"runs":results,"planned_runs":36,"completed_runs":len(results),"failed_runs":[],"selected_before_test":locked["selected_representation"],
        "locked_checksum":locked["locked_checksum"],"scope":registry["scope"],"fresh_final_test":False,
        "limitations":["All historical rows exposed; shared validation/calibration.","Three motor folds, not independent windows or seed replications.","Subset/PCA is not restored synchronized raw."]}
    save_json(output/"evaluation_report.json",report); return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["prepare","fit","evaluate"]); p.add_argument("--matrix",type=Path,required=True)
    p.add_argument("--data-root",type=Path,required=True); p.add_argument("--registry",type=Path); p.add_argument("--locked",type=Path)
    args=p.parse_args(); log,paths=setup_run("fault_type_representations"); manifests,_=load_prior_manifests(args.matrix)
    if args.action=="prepare":
        save_json(paths.output_dir/"candidate_registry.json",build_registry(manifests)); log.info("preregistered6 representations; fit nothing; commit first"); return
    if not args.registry: p.error("fit/evaluate requires previously saved and committed registry")
    registry=json.loads(args.registry.read_text(encoding="utf-8")); pools=FeatureStore(args.data_root)
    if args.action=="fit":
        locked=run(pools,manifests=manifests,registry=registry,output=paths.output_dir); log.info("selected={} by known validation; commit lock before test",locked["selected_representation"])
    else:
        if not args.locked: p.error("evaluate requires previously committed locked selection")
        locked=json.loads(args.locked.read_text(encoding="utf-8"))
        result=evaluate(pools,manifests=manifests,registry=registry,locked=locked,output=paths.output_dir); log.info("{} exploratory runs complete",result["completed_runs"])


if __name__ == "__main__": main()
