"""Registry-driven bounded study. No implicit defaults or global selection."""
from __future__ import annotations
import argparse
import gzip
import json
import platform
import time
import warnings
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from core.fault_type_accuracy_pipeline import StudyRepresentation, records_for, check_cell, validate_node_audit
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal, verify_seal, digest
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run
from core.openset import create_openset_detector
from experiments.fault_type_accuracy_registry import check_registry, classifier
from experiments.fault_type_accuracy_baseline import context
from experiments.fault_type_fixed_calibration import verify_sources, load_bound_model
from experiments.fault_type_fixed_calibration import raw_class_scores
from core.fault_type_accuracy_scores import PooledWithinLW, ResearchScore


def fit_classifier(arm, seed, registry, X, y):
    model=classifier(arm['classifier'],seed,len(registry['known_labels']))
    if model.get_params()!=registry['classifier_resolved'][arm['classifier']][str(seed)]: raise ValueError('classifier resolved parameters changed')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning)
        model.fit(X,y)
    if any(issubclass(w.category,ConvergenceWarning) for w in caught): raise RuntimeError('nonconvergent fixed classifier')
    return model


def fit_a(pools, *, registry, manifests, output, code_head):
    known=registry['known_labels']; artifacts=[]; audits=[]; failures=[]
    counts={'classifier_fits':0,'factory_reference_fits':0,'pooled_reference_fits':0,'representation_fits':0}
    with threadpool_limits(limits=1):
        for m in manifests:
            for seed in registry['seeds']:
                a1=None; a1_artifact=None
                for arm in registry['arms'][1:]:
                    start=time.perf_counter(); nodes={}
                    node_rpms=registry['expected_rpms'] if arm['rpm_strategy']=='separate' else [None]
                    for rpm in node_rpms:
                        key=rpm or 'mixed'
                        train=records_for(m,'train',rpm); cal=records_for(m,'calibration',rpm)
                        try: cell=check_cell(train,cal,known,registry['rules']['minimum_reference_per_class'])
                        except ValueError as e:
                            failures.append({'arm_id':arm['id'],'fold_id':m['fold_id'],'seed':seed,'rpm':key,'status':'INCOMPLETE','reason':str(e)})
                            continue
                        raw=pools.load(train); calibration=pools.load(cal)
                        y=np.array([known.index(r['label']) for r in train]); cy=np.array([known.index(r['label']) for r in cal])
                        reuse=arm.get('reference_arm')=='A1'
                        if reuse:
                            if a1 is None or key not in a1['nodes']: raise ValueError('A1 reference unavailable')
                            ref=a1['nodes'][key]; transformer=ref['transformer']; detectors=ref['detectors']
                        else:
                            try: transformer=StudyRepresentation(arm,registry['scaler_resolved']).fit(raw)
                            except ValueError as e:
                                failures.append({'arm_id':arm['id'],'fold_id':m['fold_id'],'seed':seed,'rpm':key,'status':'CONTRACT_MISMATCH','reason':str(e)});continue
                            X,C=transformer.transform(raw),transformer.transform(calibration)
                            detectors={method:create_openset_detector(method,**registry['detectors']).fit(X,y,C,cy) for method in ['mahalanobis','knn']}
                            counts['factory_reference_fits']+=2;counts['representation_fits']+=1
                        X=transformer.transform(raw)
                        clf=fit_classifier(arm,seed,registry,X,y);counts['classifier_fits']+=1
                        audit={'arm_id':arm['id'],'fold_id':m['fold_id'],'rpm':key,'seed':seed,'registry_checksum':registry['registry_checksum'],
                            'manifest_checksum':m['manifest_checksum'],'motor_roles':m['motor_roles'],'dataset_fingerprint':registry['dataset_fingerprint'],
                            'selection_policy':'none','selection_sample_ids':[],'shared_validation_calibration':False,
                            'calibration_sample_ids':[r['sample_id'] for r in cal],'class_counts':cell,
                            'train_label_counts_for_weight':np.bincount(y,minlength=len(known)).tolist(),
                            'classifier_parameters':clf.get_params(),'transform_checksum':transformer.transform_checksum,
                            'redundancy_check':transformer.redundancy_check,'reference_reused_from':a1_artifact if reuse else None,
                            'detector_calibration':{method:d.class_summaries() for method,d in detectors.items()},
                            'code_head':code_head}
                        for field in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids']:
                            audit[field]=[r['sample_id'] for r in train]
                        validate_node_audit(audit,m,rpm,arm,registry);audits.append(audit)
                        node={'classifier':clf,'audit_checksum':digest(audit),'fit_ids_checksum':digest(audit['classifier_fit_ids'])}
                        if not reuse: node.update(transformer=transformer,detectors=detectors)
                        nodes[key]=node
                    model={'arm_id':arm['id'],'fold_id':m['fold_id'],'seed':seed,'registry_checksum':registry['registry_checksum'],
                        'manifest_checksum':m['manifest_checksum'],'labels':known,'nodes':nodes,'reference_artifact':a1_artifact if arm.get('reference_arm') else None}
                    path=output/f"{arm['id']}_{m['fold_id']}_seed{seed}.joblib";joblib.dump(model,path,compress=3)
                    artifact={k:model[k] for k in ['arm_id','fold_id','seed','manifest_checksum']}
                    artifact.update(path=str(path.resolve()),sha256=_sha256_file(path),node_count=len(nodes),seconds=time.perf_counter()-start)
                    artifacts.append(artifact)
                    if arm['id']=='A1': a1=model;a1_artifact=artifact
    return artifacts,audits,failures,counts


def run(pools, *, registry, output, code_head):
    baseline=check_registry(registry)
    _,_,manifests,_=context(baseline['baseline_index'])
    before=verify_sources(pools.root,manifests[0])
    output.mkdir(parents=True,exist_ok=True)
    artifacts,audits,failures,counts=fit_a(pools,registry=registry,manifests=manifests,output=output,code_head=code_head)
    b_artifacts,b_audits,b_failures=fit_b(pools,registry=registry,manifests=manifests,a_artifacts=artifacts,output=output,code_head=code_head)
    counts['pooled_reference_fits']=sum(a['node_count'] for a in b_artifacts)
    counts['new_score_calibrations']=sum(a['node_count']*6 for a in b_artifacts)
    artifacts+=b_artifacts;audits+=b_audits;failures+=b_failures
    audit_path=output/'fit_audits.json.gz'
    audit_path.write_bytes(gzip.compress(json.dumps(audits,sort_keys=True,allow_nan=False).encode(),mtime=0))
    after=verify_sources(pools.root,manifests[0])
    if before!=after: raise ValueError('formal source changed')
    result=seal({'schema_version':1,'registry_checksum':registry['registry_checksum'],'selection_policy':'none','selection_sample_ids':[],
        'shared_validation_calibration':False,'artifacts':artifacts,'fit_counts':counts,'failures':failures,
        'audit_artifact':{'path':str(audit_path.resolve()),'sha256':_sha256_file(audit_path)},'source_before':before,'source_after':after,
        'code_head':code_head,'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__},
        'scope':registry['scope'],'fresh_final_test':False,'independent_validation_status':'INCOMPLETE'},'locked_checksum')
    save_json(output/'locked_study.json',result)
    return result


def fit_b(pools, *, registry, manifests, a_artifacts, output, code_head):
    artifacts=[];audits=[];failures=[];known=registry['known_labels']
    with threadpool_limits(limits=1):
        for m in manifests:
            for seed in registry['seeds']:
                base_artifact=next(a for a in a_artifacts if (a['arm_id'],a['fold_id'],a['seed'])==('A1',m['fold_id'],seed))
                base=load_bound_model(base_artifact,output.parent);nodes={};start=time.perf_counter()
                for rpm in registry['expected_rpms']:
                    if rpm not in base['nodes']:
                        failures.append({'arm_id':'B1-B6','fold_id':m['fold_id'],'seed':seed,'rpm':rpm,'status':'INCOMPLETE','reason':'A1 unavailable'});continue
                    train=records_for(m,'train',rpm);cal=records_for(m,'calibration',rpm)
                    trans=base['nodes'][rpm]['transformer']
                    X,C=trans.transform(pools.load(train)),trans.transform(pools.load(cal))
                    y=np.array([known.index(r['label']) for r in train]);cy=np.array([known.index(r['label']) for r in cal])
                    pooled=PooledWithinLW().fit(X,y,len(known))
                    raw={'pooled_within_lw':pooled.raw_scores(C),
                         'class_mahalanobis':raw_class_scores(base['nodes'][rpm]['detectors']['mahalanobis'],C)[0],
                         'class_knn':raw_class_scores(base['nodes'][rpm]['detectors']['knn'],C)[0]}
                    scores={s['id']:ResearchScore(s,registry['rules']['conformal_alpha']).calibrate(raw[s['reference']],cy) for s in registry['score_arms']}
                    audit={'arm_id':'B','fold_id':m['fold_id'],'seed':seed,'rpm':rpm,'registry_checksum':registry['registry_checksum'],
                        'manifest_checksum':m['manifest_checksum'],'motor_roles':m['motor_roles'],'selection_policy':'none','selection_sample_ids':[],
                        'shared_validation_calibration':False,'reference_fit_ids':[r['sample_id'] for r in train],
                        'pooled_covariance_fit_ids':[r['sample_id'] for r in train],'calibration_sample_ids':[r['sample_id'] for r in cal],
                        'base_A1_artifact':base_artifact,'pooled_formula':'train own-class residuals; LedoitWolf assume_centered=True; sqrt distance',
                        'calibration_summaries':{k:v.summaries() for k,v in scores.items()},'code_head':code_head}
                    audits.append(audit);nodes[rpm]={'pooled':pooled,'scores':scores,'audit_checksum':digest(audit)}
                model={'arm_id':'B','fold_id':m['fold_id'],'seed':seed,'registry_checksum':registry['registry_checksum'],
                    'manifest_checksum':m['manifest_checksum'],'labels':known,'nodes':nodes,'reference_artifact':base_artifact}
                path=output/f"B_{m['fold_id']}_seed{seed}.joblib";joblib.dump(model,path,compress=3)
                artifacts.append({'arm_id':'B','fold_id':m['fold_id'],'seed':seed,'manifest_checksum':m['manifest_checksum'],
                    'path':str(path.resolve()),'sha256':_sha256_file(path),'node_count':len(nodes),'seconds':time.perf_counter()-start})
    return artifacts,audits,failures


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['fit'])
    p.add_argument('--registry',type=Path,required=True)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--code-head',required=True)
    args=p.parse_args();log,paths=setup_run('fault_type_accuracy_study')
    registry=json.loads(args.registry.read_text(encoding='utf-8'))
    result=run(FeatureStore(args.data_root),registry=registry,output=paths.output_dir,code_head=args.code_head)
    log.info('fixed fits sealed {} output={}',result['fit_counts'],paths.output_dir)


if __name__=='__main__': main()
