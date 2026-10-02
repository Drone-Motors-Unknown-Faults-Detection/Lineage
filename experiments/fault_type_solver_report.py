"""Recompute train-only objectives and compare sealed original Q weights."""
import argparse
from pathlib import Path
import numpy as np
from core.fault_type_continuous import margin_problem, margin_loss_grad, stratified_subset
from core.fault_type_smooth_margin import smooth_loss_grad, projected_gradient
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import verify_seal, seal, digest
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.fault_type_accuracy_pipeline import records_for
from core.logger import setup_run
from experiments.fault_type_solver_diagnosis import check, audit, verify_cell, METHODS, read
from experiments.fault_type_literature_study import artifact, load_bundle
from experiments.fault_type_continuous_study import load_new
from experiments.fault_type_fixed_calibration import verify_sources
from threadpoolctl import threadpool_limits


def verify_losses(optimizer, problem, smooth):
    w=np.array(optimizer["weights"])
    loss,gradient=(smooth_loss_grad if smooth else margin_loss_grad)(w,problem)
    hard=margin_loss_grad(w,problem)[0]
    pg=float(np.abs(projected_gradient(w,gradient)).max())
    for name,value in [("final_loss",loss),("same_hard_loss",hard),("projected_gradient_inf",pg)]:
        if not np.isclose(optimizer[name],value,rtol=1e-10,atol=1e-10):
            raise ValueError("saved train numeric mismatch: "+name)
    if smooth and not (-1e-12 <= loss-hard <= .5*.1*np.log(2)+1e-12):
        raise ValueError("SGL approximation bound violated")
    return {"final_loss":loss,"same_hard_loss":hard,"projected_gradient_inf":pg}


def run(pools,*,protocol,diagnosis,q_lock,output):
    q,pp,ms,parent_lock,old_audits=check(protocol)
    verify_seal(diagnosis,"diagnosis_checksum");verify_seal(q_lock,"locked_checksum")
    if diagnosis["protocol_checksum"]!=protocol["protocol_checksum"] or q_lock["protocol_checksum"]!=q["protocol_checksum"]:
        raise ValueError("report protocol/model binding")
    if diagnosis["completed_diagnostic_fits"]!=27 or len(diagnosis["artifacts"])!=27 or diagnosis["outer_evaluations"]!=0:
        raise ValueError("missing or wrong diagnostic coverage")
    before=verify_sources(pools.root,ms[0])
    rows=[]; seen=set(); q_matches=[]
    with threadpool_limits(limits=1):
        for pa in parent_lock["artifacts"]:
            m=next(m for m in ms if m["fold_id"]==pa["fold_id"]);seed=pa["seed"]
            train=records_for(m,"train");y=np.array([q["known_labels"].index(r["label"]) for r in train])
            ix=stratified_subset(y,[r["rpm"] for r in train],seed)
            expected=audit(train,[train[i]["sample_id"] for i in ix],m,q["known_labels"])
            expected.update(seed=seed,parent_model_sha256=pa["sha256"])
            parent=load_bundle(pa,parent_lock,pp,ms,old_audits)
            h=parent["references"]["harmonic69/mixed"]["transformer"].transform(pools.load(train))[ix]
            problem=margin_problem(h,y[ix])
            cells={}
            for method in METHODS:
                wanted=method["id"]+"_"+m["fold_id"]+"_seed"+str(seed)+".json"
                aa=[a for a in diagnosis["artifacts"] if Path(a["path"]).name==wanted]
                if len(aa)!=1 or aa[0]["path"] in seen:raise ValueError("duplicate or missing checkpoint")
                a=aa[0];seen.add(a["path"])
                if _sha256_file(Path(a["path"]))!=a["sha256"]:raise ValueError("checkpoint SHA")
                c=read(a["path"]);verify_cell(c,protocol,expected,method)
                if c["parent_model"]!=pa:raise ValueError("parent artifact changed")
                nums=verify_losses(c["optimizer"],problem,method["smooth"])
                row={k:c[k] for k in ["fold_id","seed","method"]}
                row.update(motor=m["motor_roles"]["train"],metric_fit_count=len(ix),
                    metric_fit_ids_checksum=digest(expected["metric_fit_ids"]),
                    optimizer={k:v for k,v in c["optimizer"].items() if k!="weights"},
                    recomputed=nums,artifact=a)
                rows.append(row);cells[method["id"]]=c
            qa=[a for a in q_lock["artifacts"] if a["fold_id"]==m["fold_id"] and a["seed"]==seed]
            if len(qa)!=1:raise ValueError("original Q bundle missing")
            old=load_new(qa[0],q,m,pa)
            metric=old["metric"]
            match={"fold_id":m["fold_id"],"seed":seed,"original_metric_available":metric is not None}
            if metric is not None:
                equal=np.array_equal(metric.weights,np.array(cells["hard150"]["optimizer"]["weights"]))
                if not equal:raise ValueError("hard150 differs from original successful Q metric")
                match.update(weights_exact_match=equal,original_weights_checksum=digest(metric.weights.tolist()))
            else:match.update(weights_exact_match=None,reason="old failed Q metric weights were not preserved")
            q_matches.append(match)
    after=verify_sources(pools.root,ms[0])
    if before!=after or before!=diagnosis["source_before"] or after!=diagnosis["source_after"]:
        raise ValueError("formal source changed")
    counts={m["id"]:sum(r["optimizer"]["success"] for r in rows if r["method"]==m) for m in METHODS}
    if counts!=diagnosis["converged_by_method"]:raise ValueError("convergence counts changed")
    result=seal({"protocol_checksum":protocol["protocol_checksum"],
        "diagnosis_checksum":diagnosis["diagnosis_checksum"],"original_Q_locked_checksum":q_lock["locked_checksum"],
        "reporter":artifact(Path(__file__)),"numeric_recomputation":"PASS","source_before":before,"source_after":after,
        "converged_by_method":counts,"rows":rows,"original_Q_matches":q_matches,
        "selection_policy":"none","selection_sample_ids":[],"calibration_input_ids":[],"test_input_ids":[],
        "outer_evaluations":0,"accuracy_improvement":"NOT_EVALUATED","production_replacement":False,
        "fresh_final_test":False,"physical_reason":"UNKNOWN; numerical solver evidence only"},"report_checksum")
    save_json(output/"summary.json",result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ["protocol","diagnosis","q-lock","data-root"]:p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args();log,paths=setup_run("fault_type_solver_report")
    r=run(FeatureStore(a.data_root),protocol=read(a.protocol),diagnosis=read(a.diagnosis),q_lock=read(a.q_lock),output=paths.output_dir)
    log.info("numeric PASS: {} original matches={} seal={}",r["converged_by_method"],
             sum(v["weights_exact_match"] is True for v in r["original_Q_matches"]),r["report_checksum"])


if __name__=="__main__":main()
