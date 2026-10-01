"""Generate SYNTHETIC engineering bundle/models, not actual acquisition evidence.

Uses independent known-only random training/calibration, no incoming fitting.
No synthetic metric is a research claim. Generated raw/model bytes not in Git.
"""
from __future__ import annotations
import argparse
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler
from threadpoolctl import threadpool_limits
from core.formal_data import FEATURE_NAMES, _sha256_file
from core.fault_type_final_guard import seal,digest
from core.synchronized_features import generate
from core.fault_type_provenance import save_json
from core.openset import create_openset_detector
from core.logger import setup_run
from core.fresh_data import model_contract_checksum

KNOWN=["8screws","1screws","2screws","3screws","3_14screws","4screws"]
UNKNOWN=["4_146screws","5screws","6screws","7screws"]
PHYSICAL={k:"fixture_attested:synthetic only" for k in ["sensor_units","orientation","calibration","mounting","load"]}


def run(pools, *, seed=42):
    root=Path(pools).resolve(); root.mkdir(parents=True,exist_ok=True)
    if (root/"seed_ledger.json").exists(): raise ValueError("fixture exists; refuse overwrite")
    rng=np.random.default_rng(seed); recordings=[]; length=1024
    for i,label in enumerate(KNOWN+UNKNOWN):
        for group in range(2):
            for rpm in ["6000rpm","8000rpm","11000rpm"]:
                rid=f"fixture-{i}-{group}-{rpm}"; time=np.arange(length*5)/10000
                values=np.column_stack([np.sin(2*np.pi*(100+11*j)*time)*(1+i/20)+rng.normal(0,.05,len(time))+j for j in range(5)])
                path=root/f"{rid}.raw.csv"
                pd.DataFrame({"time":time,**{name:values[:,j] for j,name in enumerate(["current","x","y","z","delta_t"])}}).to_csv(path,index=False)
                cfg={"recording_id":rid,"motor_id":f"fixture-M{group}","session_id":f"fixture-S{group}","run_id":rid,"synthetic":True,
                    "raw_sample_count":len(time),"sample_rate_hz":10000,"rpm":rpm,"label":label,"acquisition_timestamp":"2026-10-01T08:00:00+08:00","attestation":"fixture_attested: generated, never real hardware",
                    "physical_contract":PHYSICAL,"parser":{"layout":"single_file_shared_rows","delimiter":",","header_row_0_based":0,
                        "expected_columns":["time","current","x","y","z","delta_t"],"time_column":"time","time_semantics":"relative_seconds",
                        "channels":{k:k for k in ["current","x","y","z","delta_t"]}},
                    "evidence":{k:{"level":"fixture_attested","reference":"synthetic generator"} for k in ["sample_rate","alignment"]},
                    "quality":{},"windows":{"length":length,"stride":length,"gap_rule":"reject","bad_point_rule":"reject"}}
                recordings.append((path,cfg))
    settings={"variant":"aligned_only","quality":{},"windows":recordings[0][1]["windows"]}
    generate(recordings,settings=settings,output=root/"features",incoming_root=root)
    save_json(root/"raw_config_example.json",recordings[0][1])
    registry=json.loads((root/"features/version_registry.json").read_text(encoding="utf-8"))
    ledger=seal({"files":{},"numeric_row_digests":[],"motor_ids":[],"sessions":[],"runs":[],"raw_recording_sha256":[],"sample_ids":[],"evidence":["synthetic empty history"]},"ledger_checksum")
    save_json(root/"seed_ledger.json",ledger)
    artifacts=[]; training_records=[]; selection_ids=[]
    root_models=root/"models"; root_models.mkdir()
    with threadpool_limits(limits=1):
        for fold,foldseed in enumerate([42,123,2026]):
            gen=np.random.default_rng(foldseed); y=np.repeat(np.arange(6),30); cy=np.repeat(np.arange(6),10)
            X=gen.normal(size=(180,105))+y[:,None]/2; C=gen.normal(size=(60,105))+cy[:,None]/2
            scaler=RobustScaler().fit(X); X=scaler.transform(X); C=scaler.transform(C)
            classifier=LogisticRegression(max_iter=1000,class_weight="balanced").fit(X,y)
            detectors={method:create_openset_detector(method).fit(X,y,C,cy) for method in ["mahalanobis","knn"]}
            trainids=[f"fixture-fit-{fold}-{j}" for j in range(180)]; calids=[f"fixture-cal-{fold}-{j}" for j in range(60)]
            for j,sid in enumerate(trainids+calids):
                training_records.append({"sample_id":sid,"motor_id":f"fixture-training-{fold}","session_id":f"fixture-training-session-{fold}","run_id":f"fixture-training-run-{fold}",
                    "raw_source_sha256":digest(["synthetic-fitting",fold]),"source_interval":[j*length,(j+1)*length],
                    "label":KNOWN[j//30] if j<180 else KNOWN[(j-180)//10]})
            audit={"train_ids":trainids,"calibration_ids":calids,"known_only":True,"train_only_transforms":True,"scope":"synthetic_engineering"}
            model={"scaler":scaler,"classifiers":{"linear_baseline":classifier},"detectors":detectors,"labels":KNOWN,"fold_id":f"fixture-fold-{fold}","fit_audit":audit}
            path=root_models/f"training_{foldseed}.joblib"; joblib.dump(model,path,compress=3)
            artifacts.append({"path":path.name,"sha256":_sha256_file(path),"fold_id":model["fold_id"],"seed":foldseed,"manifest_checksum":digest(audit),"fit_audit":audit,"model_contract_checksum":model_contract_checksum(model)})
            selection_ids.extend(calids)
    locked=seal({"status":"locked","fresh_protocol":"paired_n5_three_folds_v1","synthetic":True,
        "feature_version":registry["feature_version"],"pipeline_id":registry["pipeline_id"],"column_order":FEATURE_NAMES,
        "known_labels":KNOWN,"unknown_labels":UNKNOWN,"training_physical_contract":PHYSICAL,"training_records":training_records,
        "training_artifacts":artifacts,"training_artifact_sha256":digest(artifacts),"selection_input_ids":selection_ids,
        "exposure_ledger_checksum":ledger["ledger_checksum"],"minimum_test_samples_per_class":30,"minimum_test_groups_per_class":2,
        "expected_rpms":["6000rpm","8000rpm","11000rpm"],"serialization_environment":{"python":platform.python_version(),"sklearn":sklearn.__version__},
        "scope":"synthetic_engineering_only; no actual final validation"},"locked_checksum")
    locked=seal({**locked,"training_provenance_status":"fixture_attested","bridge_input_ids":[]},"locked_checksum")
    save_json(root/"locked_config.json",locked)
    return {"root":str(root),"scope":"synthetic_engineering","windows":300,"real_final_test":False}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--seed",type=int,default=42)
    args=p.parse_args(); log,paths=setup_run("synchronized_fixture")
    result=run(paths.output_dir,seed=args.seed); save_json(paths.output_dir/"fixture_index.json",result)
    log.info("fixture created at {}; never real motor evidence",paths.output_dir)


if __name__ == "__main__": main()
