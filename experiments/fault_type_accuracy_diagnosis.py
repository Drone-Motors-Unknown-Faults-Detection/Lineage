"""Post-evaluation T1 distributions. No refit, tuning, adaptation or selection."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from core.fault_type_features import FeatureStore
from core.fault_type_accuracy_pipeline import records_for
from core.fault_type_final_guard import seal, verify_seal, digest
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_accuracy_baseline import context
from experiments.fault_type_accuracy_registry import check_registry
from experiments.fault_type_accuracy_study import validate_lock, resolved_model
from experiments.fault_type_fixed_calibration import raw_class_scores, verify_sources
from experiments.fault_type_fixed_diagnosis import healthy_shift
from experiments.fault_type_fixed_report import load_predictions
from experiments.fault_type_metrics import _score_distribution


def run(pools, *, registry, locked, verified, trusted_root):
    baseline=check_registry(registry);_,_,manifests,_=context(baseline['baseline_index'])
    verify_seal(verified,'report_checksum')
    if verified['registry_checksum']!=registry['registry_checksum'] or verified['new_completed_evaluations']!=198:
        raise ValueError('diagnosis requires verified full comparison')
    audits=validate_lock(locked,registry,manifests)
    m=next(m for m in manifests if m['motor_roles']['test']=='T1');known=registry['known_labels']
    before=verify_sources(pools.root,m);results=[]
    with threadpool_limits(limits=1):
        for artifact in locked['artifacts']:
            if artifact['fold_id']!=m['fold_id'] or artifact['seed']!=0 or artifact['arm_id'] not in ['A1','A2','A3','A4','B']:continue
            model=resolved_model(artifact,locked,registry,manifests,audits,trusted_root)
            for key,node in model['nodes'].items():
                rpm=None if key=='mixed' else key
                base=model['resolved_reference_model']['nodes'][key] if model['arm_id']=='B' else node
                parts={p:records_for(m,p,rpm) for p in ['train','calibration','test']}
                transformed={p:base['transformer'].transform(pools.load(rr)) for p,rr in parts.items()}
                shifts=healthy_shift(parts,transformed,known[0])
                for score in ([s['id'] for s in registry['score_arms']] if model['arm_id']=='B' else ['mahalanobis','knn']):
                    arm=score if model['arm_id']=='B' else model['arm_id'];groups=[]
                    saved_run=next(r for r in verified['runs'] if (r['arm_id'],r['score_id'],r['fold_id'],r['seed'])==(arm,score,m['fold_id'],0))
                    saved={r['sample_id']:r for r in load_predictions(saved_run['prediction_artifact'])}
                    for part,records in parts.items():
                        X=transformed[part]
                        if model['arm_id']=='B':
                            scorer=node['scores'][score];ref=scorer.definition['reference']
                            raw=node['pooled'].raw_scores(X) if ref=='pooled_within_lw' else raw_class_scores(base['detectors']['knn' if ref=='class_knn' else 'mahalanobis'],X)[0]
                            d=scorer.details(raw)
                        else:
                            raw,threshold,ratios,_=raw_class_scores(base['detectors'][score],X)
                            d={'score':ratios.min(1),'reject':ratios.min(1)>1,'nearest':ratios.argmin(1),'p_values':None,'candidate_size':None}
                        if part=='test' and not np.allclose(d['score'],[saved[r['sample_id']]['openset_score'] for r in records],rtol=1e-12,atol=1e-12):
                            raise ValueError('diagnostic inference differs from sealed prediction')
                        for condition in sorted({r['rpm'] for r in records}):
                            for label in sorted({r['label'] for r in records}):
                                mask=np.array([r['rpm']==condition and r['label']==label for r in records])
                                if not mask.any():continue
                                groups.append({'partition':part,'rpm':condition,'configuration':label,'samples':int(mask.sum()),
                                    'ids_checksum':digest([r['sample_id'] for r,yes in zip(records,mask) if yes]),
                                    'score':_score_distribution(d['score'][mask]),'rejection_rate':float(d['reject'][mask].mean()),
                                    'nearest_counts':dict(Counter(known[int(i)] for i in d['nearest'][mask])),
                                    'raw_class_scores':{c:_score_distribution(raw[mask,j]) for j,c in enumerate(known)},
                                    'class_p_values':None if d['p_values'] is None else {c:_score_distribution(d['p_values'][mask,j]) for j,c in enumerate(known)}})
                    results.append({'arm_id':arm,'score_id':score,'node':key,'motor_roles':m['motor_roles'],'seed':0,
                        'groups':groups,'healthy_same_rpm_shift':shifts,'model_artifact':artifact})
    after=verify_sources(pools.root,m)
    if before!=after:raise ValueError('diagnosis changed sources')
    return seal({'scope':'POSTHOC_READONLY_NOT_SELECTION','test_motor':'T1','registry_checksum':registry['registry_checksum'],
        'report_checksum':verified['report_checksum'],'diagnostics':results,'source_before':before,'source_after':after,
        'threshold_search':False,'model_modified':False,'train_scores_warning':'in-sample optimistic; descriptive only',
        'physical_cause':'UNKNOWN raw timing/session/units/mount/load/cleaning; shift not causal proof'},'diagnosis_checksum')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['registry','locked','verified','data-root']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();log,paths=setup_run('fault_type_accuracy_diagnosis')
    read=lambda q:json.loads(q.read_text(encoding='utf-8'))
    result=run(FeatureStore(a.data_root),registry=read(a.registry),locked=read(a.locked),verified=read(a.verified),trusted_root=Path.cwd()/'output')
    save_json(paths.output_dir/'diagnosis.json',result);log.info('{} read-only T1 score/node diagnostics',len(result['diagnostics']))


if __name__=='__main__':main()
