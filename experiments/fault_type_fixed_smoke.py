"""Synthetic fixed-method CLI smoke fixture. NEVER research performance."""
from __future__ import annotations
import gzip
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from core.fault_type_sample_split import load_formal_catalog, generate_campaign_folds
from core.fault_type_manifest import build_split_manifest, write_split_manifest
from core.fault_type_final_guard import build_exposure_ledger
from core.fault_type_features import FeatureStore
from core.fault_type_provenance import save_json
from core.logger import setup_run


def fixture(root):
    labels = ["8screws","1screws","2screws","3screws","3_14screws","4screws","4_146screws","5screws","6screws","7screws"]
    rng = np.random.default_rng(20261001)
    for stage in ("1","2","3"):
        for rpm in ("6000rpm","8000rpm","11000rpm"):
            for j,label in enumerate(labels):
                path = root/f"Step-{stage}/myfeature/T{stage}/{rpm}/{label}/{label}_Group_feature_data_clean.csv"
                path.parent.mkdir(parents=True,exist_ok=True)
                pd.DataFrame(rng.normal(size=(12,105))+j*.1+int(stage)*.02,
                             columns=[f"x{i}" for i in range(105)]).to_csv(path,index=False)
    records,catalog = load_formal_catalog(root)
    role = {"checksum":"r"*64,"split_id":"synthetic-N5","class_combination_id":"synthetic","class_combination_seed":42,
            "protocol":"A","healthy_label":labels[0],"known_fault_labels":labels[1:6],"unknown_validation_labels":[],"unknown_test_labels":labels[6:]}
    folds = generate_campaign_folds(records,healthy_label=role["healthy_label"],known_fault_labels=role["known_fault_labels"],unknown_test_labels=role["unknown_test_labels"])
    manifests = [build_split_manifest(records,catalog,role,f,sample_split_seed=s,git_commit="synthetic") for f,s in zip(folds,[42,123,2026])]
    ledger = build_exposure_ledger(records,FeatureStore(root),test_ids={r["sample_id"] for r in records},evidence=[{"scope":"SYNTHETIC_ENGINEERING_ONLY"}])
    return manifests,ledger


def run(pools, *, output):
    data = output/"synthetic_features"
    manifests,ledger = fixture(data)
    matrix = output/"matrix"; matrix.mkdir()
    paths = [write_split_manifest(m,matrix/"manifests") for m in manifests]
    save_json(matrix/"run_plan.json",{"roles":[{"split_id":"synthetic-N5"}]})
    save_json(matrix/"run_status.json",{"runs":{str(i):{"method":"mahalanobis","manifest_path":str(p.resolve())} for i,p in enumerate(paths)}})
    ledger_path=output/"ledger.json.gz"
    ledger_path.write_bytes(gzip.compress(json.dumps(ledger).encode(),mtime=0))
    base=[sys.executable,"-m","experiments.fault_type_fixed_calibration"]
    common=["--matrix",str(matrix.resolve()),"--ledger",str(ledger_path.resolve())]
    outputs=[]
    for action in ("prepare","fit","evaluate"):
        args=base+[action]+common
        if action!="prepare": args += ["--protocol",outputs[0]+"/protocol.json","--data-root",str(data.resolve())]
        if action=="evaluate": args += ["--locked",outputs[1]+"/locked_methods.json"]
        existing=set(Path("output/fault_type_fixed_calibration").glob("*"))
        process=subprocess.run(args,capture_output=True,text=True,encoding="utf-8")
        (output/(action+".txt")).write_text(process.stdout+process.stderr,encoding="utf-8")
        if process.returncode: raise RuntimeError(f"synthetic {action} failed")
        created=set(Path("output/fault_type_fixed_calibration").glob("*"))-existing
        if len(created)!=1: raise RuntimeError("CLI output collision")
        outputs.append(str(created.pop().resolve()))
    report=json.loads((Path(outputs[2])/"evaluation_report.json").read_text(encoding="utf-8"))
    result={"scope":"SYNTHETIC_ENGINEERING_ONLY_NOT_RESEARCH","status":"PASS","completed_cli_evaluations":report["completed_runs"],"cli_output_roots":outputs}
    save_json(output/"smoke_index.json",result)
    return result


def main():
    import argparse
    argparse.ArgumentParser(description=__doc__).parse_args()
    log,paths=setup_run("fault_type_fixed_smoke")
    log.info("{}",run(None,output=paths.output_dir))


if __name__=="__main__": main()
