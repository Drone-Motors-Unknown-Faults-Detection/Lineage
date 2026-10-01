"""Guarded new-data CLI: N5, all3locked folds, both factory detectors.

validate never predicts. evaluate exposes durably first. resume uses the SAME
evaluation receipt. Synthetic fixtures are engineering only, never real final.
Historical locks with unknown training physical contract are rejected.
"""
from __future__ import annotations
import argparse
import gzip
import json
import platform
from pathlib import Path
import hashlib
import sklearn
from core import durable_exposure
from core.fault_type_final_guard import FinalTestBlocked, guard_final_test, digest
from core.fresh_data import IncomingStore, prepare_bundle, load_models
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_controlled_eval import paired_predictions


def run(pools, *, manifest, registry, locked, artifact_root, ledger_path, claim, evaluation_id,
        action="validate", receipt=None, output=None):
    root=Path(pools).resolve()
    bundle=prepare_bundle(root,manifest,registry)
    fitted,manifests=load_models(locked,artifact_root,bundle)
    ledger=durable_exposure.read(ledger_path)
    if action == "resume":
        qualification=durable_exposure.validate_resume(ledger_path,receipt,bundle,locked,evaluation_id=evaluation_id,claim=claim)
    else: qualification=guard_final_test(bundle,ledger,locked,claim=claim)
    if action == "validate":
        return {"status":"PREPARED_NO_PREDICTIONS", "qualification":qualification,"data_version_checksum":bundle["data_version_checksum"],
            "synthetic_engineering":bundle["synthetic"],"final_independent_validation_completed":False,"model_reliability":"NOT_ESTABLISHED"}
    if action not in {"evaluate","resume"} or output is None: raise FinalTestBlocked("execution requires action and output")
    # One execution per evaluation at a time, including resumes.
    lock_path=ledger_path.with_name(ledger_path.name+".evaluation-"+digest(evaluation_id))
    with durable_exposure.exclusive(lock_path):
        if action == "evaluate":
            receipt,qualification=durable_exposure.register(ledger_path,bundle,locked,claim=claim,evaluation_id=evaluation_id,
                expected_checksum=ledger["ledger_checksum"])
        save_json(output/"exposure_receipt.json",receipt)
        try:
            result=paired_predictions(IncomingStore(root),manifests=manifests,locked=locked,fitted=fitted,
                qualification=qualification,incoming_bundle=bundle,exposure_receipt=receipt)
            for run_id,rows in result.pop("predictions").items():
                packed=gzip.compress("\n".join(json.dumps(r,sort_keys=True,allow_nan=False) for r in rows).encode(),mtime=0)
                path=output/f"{run_id}_predictions.jsonl.gz"; path.write_bytes(packed)
                next(r for r in result["runs"] if r["run_id"]==run_id)["prediction_artifact"]={"path":str(path.resolve()),"sha256":hashlib.sha256(packed).hexdigest(),"rows":len(rows)}
            result.update(status="EXECUTION_COMPLETE",evaluation_id=evaluation_id,synthetic_engineering=bundle["synthetic"],
                final_independent_validation_completed=not bundle["synthetic"] and action=="evaluate",
                model_reliability="NOT_ESTABLISHED",environment={"python":platform.python_version(),"sklearn":sklearn.__version__},
                limitations=["Hardware facts remain externally attested.","Eligibility/execution/performance are separate; synthetic scores are not motor evidence.",
                             "Repeated folds share incoming samples; no independent sample multiplication."])
            save_json(output/"evaluation_report.json",result)
            return result
        except Exception as error:
            save_json(output/"evaluation_report.json",{"status":"FAILED_AFTER_EXPOSURE","evaluation_id":evaluation_id,
                "exposure_receipt":receipt,"reason":f"{type(error).__name__}: {error}","final_independent_validation_completed":False})
            raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["init-ledger","recover-ledger","receipt","validate","evaluate","resume"])
    p.add_argument("--ledger",type=Path,required=True,help="canonical local durable JSON ledger; never reset for retries")
    p.add_argument("--seed-ledger",type=Path,help="sealed initial exposure ledger, JSON or gzip")
    p.add_argument("--incoming-root",type=Path); p.add_argument("--manifest",type=Path); p.add_argument("--registry",type=Path)
    p.add_argument("--locked",type=Path); p.add_argument("--training-artifacts",type=Path,help="explicit trusted locally generated joblib root, not untrusted downloads")
    p.add_argument("--claim",choices=["new_session","new_motor"]); p.add_argument("--evaluation-id")
    p.add_argument("--resume-receipt",type=Path); p.add_argument("--report-output",type=Path)
    args=p.parse_args(); log,paths=setup_run("fault_type_fresh")
    output=paths.output_dir
    try:
        if args.action == "init-ledger":
            if not args.seed_ledger: p.error("init-ledger requires --seed-ledger")
            data=args.seed_ledger.read_bytes()
            if args.seed_ledger.suffix==".gz": data=gzip.decompress(data)
            durable_exposure.initialize(args.ledger,json.loads(data)); result={"status":"LEDGER_INITIALIZED_NO_PREDICTION"}
        elif args.action == "recover-ledger":
            head=durable_exposure.recover(args.ledger); result={"status":"HEAD_RECOVERED_EXPOSURE_RETAINED","ledger_checksum":head["ledger_checksum"]}
        elif args.action == "receipt":
            ledger=durable_exposure.read(args.ledger)
            matches=[e for e in ledger.get("evaluations",[]) if e["evaluation_id"]==args.evaluation_id]
            if len(matches)!=1: raise FinalTestBlocked("evaluation receipt not found")
            save_json(output/"exposure_receipt.json",matches[0]["receipt"]); result={"status":"RECEIPT_RECOVERED_NO_PREDICTION"}
        else:
            if not all([args.incoming_root,args.manifest,args.registry,args.locked,args.training_artifacts,args.claim,args.evaluation_id]):
                p.error("validate/evaluate/resume require incoming-root, manifest, registry, locked, training-artifacts, claim, evaluation-id")
            if args.action=="resume" and not args.resume_receipt: p.error("resume requires --resume-receipt; receipt action can recover one")
            read_json=lambda path: json.loads(path.read_text(encoding="utf-8"))
            result=run(args.incoming_root,manifest=read_json(args.manifest),registry=read_json(args.registry),locked=read_json(args.locked),
                artifact_root=args.training_artifacts.resolve(),ledger_path=args.ledger.resolve(),claim=args.claim,evaluation_id=args.evaluation_id,
                action=args.action,receipt=read_json(args.resume_receipt) if args.resume_receipt else None,output=output)
        save_json(output/"status.json",result)
        if args.report_output: save_json(args.report_output,result)
        log.info("{}; model reliability not inferred from execution",result["status"])
    except Exception as error:
        save_json(output/"failure.json",{"status":"BLOCKED_OR_FAILED","reason":f"{type(error).__name__}: {error}","final_independent_validation_completed":False})
        log.exception("blocked/failed; canonical exposure history retained")
        raise


if __name__ == "__main__": main()
