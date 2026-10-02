"""Bounded train-only diagnostic: hard150 / smooth150 / hard600,27 cells."""
import argparse
import json
import platform
import shutil
import subprocess
import time
from pathlib import Path
import numpy as np
import sklearn
from threadpoolctl import threadpool_limits
from core.fault_type_smooth_margin import solve
from core.fault_type_continuous import stratified_subset
from core.fault_type_accuracy_pipeline import records_for
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal, verify_seal, digest
from core.fault_type_provenance import save_json
from core.fault_type_mechanisms import peak_memory_bytes
from core.formal_data import _sha256_file
from core.logger import setup_run
from experiments.fault_type_continuous_registry import check as q_check, read
from experiments.fault_type_literature_study import load_bundle, artifact
from experiments.fault_type_fixed_calibration import verify_sources

METHODS = [{"id":"hard150","smooth":False,"maxiter":150,"maxfun":500},
           {"id":"smooth150","smooth":True,"maxiter":150,"maxfun":500},
           {"id":"hard600","smooth":False,"maxiter":600,"maxfun":2000}]
FILES = ["core/fault_type_smooth_margin.py","experiments/fault_type_solver_diagnosis.py",
         "docs/experiments/fault_type_solver_diagnosis.md"]


def build(q_path):
    q = read(q_path)
    _, ms, _, _ = q_check(q)
    return seal({"version":"train_only_solver_diagnosis_v1","q_protocol":artifact(q_path),
        "q_protocol_checksum":q["protocol_checksum"],"dataset_fingerprint":q["dataset_fingerprint"],
        "methods":METHODS,"seeds":[0,1,2],"folds":q["folds"],"manifest_checksums":[m["manifest_checksum"] for m in ms],
        "parameters":{"target_k":3,"per_class_rpm":20,"max_subset":360,"pull":.5,"push":.5,
                      "ridge":.01,"tau":.1,"ftol":1e-9,"gtol":1e-6,"maxls":50,"initial_weight":1.},
        "budget":{"per_fit_seconds":120,"total_seconds":1800,"reserve_C_bytes":1000000000,"planned_fits":27},
        "selection_policy":"none","selection_sample_ids":[],"calibration_fit_ids":[],"test_input_ids":[],
        "scope":"TRAIN_ONLY_DIAGNOSIS; old test exposed; no accuracy or deployment claim",
        "environment":{"python":platform.python_version(),"sklearn":sklearn.__version__},
        "implementations":[artifact(Path(f)) for f in FILES],
        "source_head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()}, "protocol_checksum")


def check(p):
    verify_seal(p,"protocol_checksum")
    if p["version"]!="train_only_solver_diagnosis_v1" or p["methods"]!=METHODS or p["seeds"]!=[0,1,2]:
        raise ValueError("fixed methods/seeds changed")
    if any(p[k] for k in ["selection_sample_ids","calibration_fit_ids","test_input_ids"]) or p["selection_policy"]!="none":
        raise ValueError("forbidden selection/cal/test input")
    if p["parameters"]!={"target_k":3,"per_class_rpm":20,"max_subset":360,"pull":.5,"push":.5,
                       "ridge":.01,"tau":.1,"ftol":1e-9,"gtol":1e-6,"maxls":50,"initial_weight":1.}:
        raise ValueError("fixed solver parameters changed")
    if p["budget"]!={"per_fit_seconds":120,"total_seconds":1800,"reserve_C_bytes":1000000000,"planned_fits":27}:
        raise ValueError("fixed budget changed")
    if p["environment"]!={"python":platform.python_version(),"sklearn":sklearn.__version__}:
        raise ValueError("science runtime changed")
    if [a["path"] for a in p["implementations"]]!=[str(Path(f).resolve()) for f in FILES]:
        raise ValueError("implementation inventory changed")
    for a in p["implementations"]+[p["q_protocol"]]:
        if _sha256_file(Path(a["path"]))!=a["sha256"]:
            raise ValueError("source SHA changed")
    q=read(p["q_protocol"]["path"]);pp,ms,lock,audits=q_check(q)
    if (p["q_protocol_checksum"]!=q["protocol_checksum"] or p["dataset_fingerprint"]!=q["dataset_fingerprint"]
        or p["folds"]!=q["folds"] or p["manifest_checksums"]!=[m["manifest_checksum"] for m in ms]):
        raise ValueError("parent data/split binding")
    return q,pp,ms,lock,audits


def audit(train, subset, manifest, known):
    ids=[r["sample_id"] for r in train]; roles=manifest["motor_roles"]
    if len(set(roles.values()))!=3 or len(set(ids))!=len(ids):
        raise ValueError("motor/ID overlap")
    if any(r["label"] not in known or r["t_code"]!=roles["train"] for r in train):
        raise ValueError("unknown or wrong motor fit")
    forbidden={r["sample_id"] for role in ["calibration","test"] for r in records_for(manifest,role)}
    if forbidden.intersection(ids) or not set(subset).issubset(ids) or len(set(subset))!=len(subset):
        raise ValueError("forbidden or duplicate subset IDs")
    return {"representation_fit_ids":ids,"metric_fit_ids":subset,"calibration_fit_ids":[],
            "selection_sample_ids":[],"test_input_ids":[],"selection_policy":"none",
            "motor_roles":roles,"manifest_checksum":manifest["manifest_checksum"]}


def verify_cell(c,p,expected,definition):
    verify_seal(c,"checkpoint_checksum")
    if c["protocol_checksum"]!=p["protocol_checksum"] or c["audit"]!=expected or c["method"]!=definition:
        raise ValueError("checkpoint config/source/role binding")
    if "seed" in expected and (c["seed"]!=expected["seed"] or c["parent_model"]["sha256"]!=expected["parent_model_sha256"]):
        raise ValueError("checkpoint seed/parent binding")
    r=c["optimizer"]; w=np.asarray(r["weights"])
    if not np.isfinite(w).all() or (w<0).any() or len(w)!=69 or r["weights_checksum"]!=digest(w.tolist()):
        raise ValueError("checkpoint weights invalid")
    if r["maxiter"]!=definition["maxiter"] or r["maxfun"]!=definition["maxfun"] or r["tau"]!=(.1 if definition["smooth"] else None):
        raise ValueError("checkpoint optimizer configuration")
    return True


def run(pools, *, protocol, output):
    q,pp,ms,lock,old_audits=check(protocol)
    before=verify_sources(pools.root,ms[0]); started=time.perf_counter(); cells=[]
    with threadpool_limits(limits=1):
        for pa in lock["artifacts"]:
            if time.perf_counter()-started>protocol["budget"]["total_seconds"] or shutil.disk_usage("C:/").free<protocol["budget"]["reserve_C_bytes"]:
                raise RuntimeError("batch budget: preserve checkpoint and resume")
            m=next(m for m in ms if m["fold_id"]==pa["fold_id"]);seed=pa["seed"]
            train=records_for(m,"train")
            y=np.array([q["known_labels"].index(r["label"]) for r in train])
            ix=stratified_subset(y,[r["rpm"] for r in train],seed)
            expected=audit(train,[train[i]["sample_id"] for i in ix],m,q["known_labels"])
            expected.update(seed=seed,parent_model_sha256=pa["sha256"])
            # Numeric reads are restricted to train. Parent contains previously sealed
            # detectors, but only its train-fit transformer is called here.
            parent=load_bundle(pa,lock,pp,ms,old_audits)
            X=pools.load(train)
            h=parent["references"]["harmonic69/mixed"]["transformer"].transform(X)[ix]
            for method in METHODS:
                if time.perf_counter()-started>protocol["budget"]["total_seconds"]:
                    raise RuntimeError("batch budget: preserve checkpoint and resume")
                target=output/(method["id"]+"_"+m["fold_id"]+"_seed"+str(seed)+".json")
                if target.exists():
                    c=read(target);verify_cell(c,protocol,expected,method)
                else:
                    r=solve(h,y[ix],smooth=method["smooth"],maxiter=method["maxiter"],
                            maxfun=method["maxfun"],seconds=protocol["budget"]["per_fit_seconds"])
                    c=seal({"protocol_checksum":protocol["protocol_checksum"],"fold_id":m["fold_id"],
                            "seed":seed,"method":method,"audit":expected,"parent_model":pa,
                            "optimizer":r,"process_peak_memory_bytes":peak_memory_bytes()},"checkpoint_checksum")
                    verify_cell(c,protocol,expected,method);save_json(target,c)
                cells.append(artifact(target))
                r=c["optimizer"]
                from loguru import logger
                logger.info("{} success={} iter={} hardloss={:.6f} {}",
                            target.name,r["success"],r["iterations"],r["same_hard_loss"],r["message"])
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError("formal source changed")
    all_cells=[read(a["path"]) for a in cells]
    result=seal({"protocol_checksum":protocol["protocol_checksum"],"artifacts":cells,
        "planned_fits":27,"completed_diagnostic_fits":len(cells),
        "converged_by_method":{m["id"]:sum(c["optimizer"]["success"] for c in all_cells if c["method"]==m) for m in METHODS},
        "source_before":before,"source_after":after,"seconds":time.perf_counter()-started,
        "outer_evaluations":0,"accuracy_improvement":"NOT_EVALUATED","production_replacement":False},"diagnosis_checksum")
    target=output/"diagnosis.json"
    if target.exists():
        old=read(target);verify_seal(old,"diagnosis_checksum")
        if any(old[k]!=result[k] for k in result if k not in ["seconds","diagnosis_checksum"]):
            raise ValueError("immutable aggregate exists; don't overwrite")
        return old
    if not target.exists():save_json(target,result)
    return result


def smoke(output):
    rng=np.random.default_rng(42);y=np.repeat(np.arange(3),5);X=rng.normal(size=(15,69))
    r=solve(X,y,smooth=True)
    save_json(output/"smoke.json",dict(scope="SYNTHETIC_ENGINEERING_ONLY",optimizer=r))
    return r


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("action",choices=["lock","fit","smoke"])
    parser.add_argument("--q-protocol",type=Path);parser.add_argument("--protocol",type=Path)
    parser.add_argument("--data-root",type=Path);parser.add_argument("--resume",type=Path)
    a=parser.parse_args();log,paths=setup_run("fault_type_solver_"+a.action)
    if a.action=="lock":
        if a.q_protocol is None:parser.error("--q-protocol required")
        p=build(a.q_protocol);check(p);save_json(paths.output_dir/"protocol.json",p)
        log.info("lock={} commit BEFORE fit",p["protocol_checksum"])
    elif a.action=="smoke":smoke(paths.output_dir);log.info("synthetic smoke complete")
    else:
        if a.protocol is None or a.data_root is None:parser.error("--protocol/--data-root required")
        output=paths.output_dir
        if a.resume:
            output=a.resume.resolve();allowed=(Path.cwd()/"output/fault_type_solver_fit").resolve()
            if not output.is_dir() or output.parent!=allowed:raise ValueError("invalid resume root")
        p=read(a.protocol);r=run(FeatureStore(a.data_root),protocol=p,output=output)
        log.info("27 train-only fits; convergence={} seal={}",r["converged_by_method"],r["diagnosis_checksum"])


if __name__=="__main__":main()
