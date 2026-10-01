"""Compact delivery views of all fixed methods; descriptive Pareto, not selector."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from core.fault_type_final_guard import verify_seal, seal
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run

AXES={'known_fault_classification.balanced_accuracy':1,'unknown_rejection.unknown_recall':1,'healthy_safety.false_positive_rate':-1}


def pareto(methods):
    """All non-dominated descriptive points, NOT a deployed/selected method."""
    points={m['arm_id']+'/'+m['score_id']:tuple(m['equal_motor_descriptive'].get(k,{}).get('mean') for k in AXES) for m in methods}
    complete={k:v for k,v in points.items() if all(x is not None for x in v)}
    relations=[]
    for target,values in complete.items():
        dominating=[]
        for other,comparison in complete.items():
            delta=[sign*(a-b) for sign,a,b in zip(AXES.values(),comparison,values)]
            if other!=target and all(x>=0 for x in delta) and any(x>0 for x in delta):dominating.append(other)
        relations.append({'method_id':target,'dominated_by':dominating,'non_dominated':not dominating})
    return {'scope':'POSTHOC_DESCRIPTIVE_ONLY_NO_DEPLOYMENT_SELECTION','axes':AXES,'points':points,'relations':relations}


def run(pools, *, verified_path, locked_path, registry_path, diagnosis_path):
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    verified=read(verified_path);locked=read(locked_path);registry=read(registry_path);diagnosis=read(diagnosis_path)
    for data,key in [(verified,'report_checksum'),(locked,'locked_checksum'),(registry,'registry_checksum'),(diagnosis,'diagnosis_checksum')]:verify_seal(data,key)
    if (verified['registry_checksum']!=registry['registry_checksum'] or locked['registry_checksum']!=registry['registry_checksum'] or
        diagnosis['report_checksum']!=verified['report_checksum']):raise ValueError('summary input versions differ')
    sources={name:{'path':str(path.resolve()),'sha256':_sha256_file(path)} for name,path in
        [('verified',verified_path),('locked',locked_path),('registry',registry_path),('diagnosis',diagnosis_path)]}
    return seal({'scope':verified['scope'],'sources':sources,'new_completed_evaluations':verified['new_completed_evaluations'],
        'failed_evaluations':verified['failed_evaluations'],'baseline_reused_evaluations':verified['baseline_reused_evaluations'],
        'new_prediction_records':verified['new_prediction_records'],'unique_test_ids':verified['unique_test_ids'],
        'fit_counts':verified['fit_counts'],'methods':verified['methods'],'paired_differences':verified['paired_differences'],
        'descriptive_pareto':pareto(verified['methods']),
        'run_index':[ {k:r[k] for k in ['arm_id','score_id','fold_id','seed','samples','test_ids_checksum','prediction_artifact']} for r in verified['runs']],
        'physical_model_fit_seconds':sum(a['seconds'] for a in locked['artifacts']),
        'cost_note':'fit seconds sum includes physical bundle work only; eval fields share work and must not be naively summed; not streaming latency',
        'selection_policy':'none','fresh_final_test':False,'independent_validation_status':'INCOMPLETE'},'summary_checksum')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['verified','locked','registry','diagnosis']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();log,paths=setup_run('fault_type_accuracy_summary')
    result=run(None,verified_path=a.verified,locked_path=a.locked,registry_path=a.registry,diagnosis_path=a.diagnosis)
    save_json(paths.output_dir/'summary.json',result)
    log.info('{} fixed method views; descriptive Pareto only',len(result['methods']))


if __name__=='__main__':main()
