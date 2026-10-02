"""Partial-aware paired report; v1 preserved in sealed Q protocol.

Reporting-only repair before Q outer evaluation. No numeric model/config change.
"""
import argparse
import csv
from pathlib import Path
import numpy as np
from core.fault_type_final_guard import seal,verify_seal
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.fault_type_reliability import assess
from core.logger import setup_run
from experiments.fault_type_continuous_registry import check,read
from experiments.fault_type_mechanism_report import summarize,predictions
from experiments.fault_type_mechanism_study import summarized
from experiments.fault_type_literature_study import write_gzip,artifact


def paired_delta(new, prior):
    """Per-fold differences never require a complete method aggregate."""
    fields={'known_accuracy':('known_classification','accuracy'),'fault_accuracy':('known_fault_classification','accuracy'),
            'unknown_recall':('unknown_rejection','unknown_recall'),'healthy_total_alarm':('healthy_safety_v2','healthy_total_alarm_rate')}
    return {k:None if new['metrics'][branch][field] is None or prior['metrics'][branch][field] is None else
            (new['metrics'][branch][field]-prior['metrics'][branch][field])*100 for k,(branch,field) in fields.items()}


def run(pools,*,protocol,evaluation,verification,baseline,previous,output):
    p=protocol;e=evaluation;v=verification;b=baseline;old=previous;check(p)
    for x,key in [(e,'evaluation_checksum'),(v,'verification_checksum'),(b,'metrics_checksum'),(old,'evaluation_checksum')]:verify_seal(x,key)
    if e['protocol_checksum']!=p['protocol_checksum'] or v['protocol_checksum']!=p['protocol_checksum'] or v['locked_checksum']!=e['locked_checksum'] or v['completed_runs']!=e['completed_runs'] or v['prediction_records']!=e['prediction_records'] or b['protocol_checksum']!=p['parent_protocol_checksum']:raise ValueError('report evaluation/source binding')
    controls={c:[r for r in b['runs'] if r['arm_id']==c and r['score_id']=='mahalanobis'] for c in ['C02','C17','C24']}
    controls['D01']=[r for r in old['runs'] if r['arm_id']=='D01']
    tables={};gates={};pairs=[];ablations=[]
    for method,runs in {**controls,**{d['id']:[r for r in e['runs'] if r['arm_id']==d['id']] for d in p['arms']}}.items():
        if len(runs)!=9:
            if method in controls:raise ValueError('control missing coverage')
            gates[method]={'main_screen':'INCOMPLETE','evidence_B':False,'evidence_C':False,'reason':'fit/eval missing','runs':len(runs)};continue
        rows=[];derived=[]
        for r in runs:
            x=predictions(r)
            recalc=summarized(x,p)
            if recalc['metrics']!=r['metrics'] or recalc['rpm_metrics']!=r['rpm_metrics']:raise ValueError('saved control/new metrics mismatch')
            derived.append(dict(r,configuration_metrics=recalc['configuration_metrics']))
            if r['seed']==0:rows+=x
        if len(rows)!=28910 or len({x['sample_id'] for x in rows})!=28910:raise ValueError('unique samples')
        tables[method]=summarize(derived,rows,p)
        if method not in controls:gates[method]=assess(derived,controls,p['reliability_contract'])
    paired_controls={**controls,**{d['id']:[r for r in e['runs'] if r['arm_id']==d['id']] for d in p['arms']}}
    comparisons=[(d['id'],c) for d in p['arms'] for c in controls]+[('Q02','Q01'),('Q04','Q03'),('Q03','Q01'),('Q04','Q02'),('Q06','Q05'),('Q07','Q06'),('Q08','Q06')]
    for new_id,old_id in comparisons:
        for r in paired_controls[new_id]:
            matched=[x for x in paired_controls[old_id] if (x['fold_id'],x['seed'])==(r['fold_id'],r['seed'])]
            if not matched:continue
            prior=matched[0];nr=predictions(r);orr=predictions(prior)
            if [x['sample_id'] for x in nr]!=[x['sample_id'] for x in orr] or any(a['true_label']!=b['true_label'] or a['source_sha256']!=b['source_sha256'] for a,b in zip(nr,orr)):raise ValueError('paired source/ID/truth mismatch')
            delta=paired_delta(r,prior)
            item={'method':new_id,'control':old_id,'fold_id':r['fold_id'],'seed':r['seed'],'samples':len(nr),
                'test_ids_checksum':r['test_ids_checksum'],'new_prediction_sha':r['prediction_artifact']['sha256'],
                'control_prediction_sha':prior['prediction_artifact']['sha256'],'per_fold_delta_pp':delta,
                'classifier_predictions_changed':sum(a['predicted_known_class']!=b['predicted_known_class'] for a,b in zip(nr,orr)),
                'scores_exact':all(a['openset_score']==b['openset_score'] for a,b in zip(nr,orr))}
            (pairs if old_id in controls else ablations).append(item)
    result=seal({'protocol_checksum':p['protocol_checksum'],'evaluation_checksum':e['evaluation_checksum'],'verification_checksum':v['verification_checksum'],
        'baseline_metrics_checksum':b['metrics_checksum'],'previous_evaluation_checksum':old['evaluation_checksum'],
        'methods':tables,'reliability':gates,'paired_controls':pairs,'matched_ablations':ablations,'runs':e['runs'],'failed_runs':e['failed_runs'],
        'planned_runs':72,'completed_runs':e['completed_runs'],'prediction_records':e['prediction_records'],'unique_samples':e['unique_samples'],
        'reporter':artifact(Path(__file__)), 'partial_methods_aggregate':'INCOMPLETE, no missing-fold mean',
        'scope':p['scope'],'evidence_C':False,'subsets_tested':1,'production_replacement':False,
        'uncertainty':'descriptive three motors/seeds; no IID window confidence intervals',
        'decision':'no selected method/global winner; fixed gates and all failures retained'},'report_checksum')
    save_json(output/'summary.json',result);write_gzip(output/'summary.json.gz',result)
    cols=['method','known_accuracy','fault_accuracy','fault_macro_f1','unknown_recall','healthy_total_alarm','worst_rpm_healthy_total_alarm','main_screen']
    with (output/'tradeoff.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader()
        for name,t in tables.items():writer.writerow(dict(method=name,**{k:t['motor_macro_seed0'][k] for k in cols[1:6]},worst_rpm_healthy_total_alarm=t['worst_rpm_healthy_total_alarm'],main_screen=gates.get(name,{}).get('main_screen','HISTORICAL_CONTROL')))
    save_json(output/'result_index.json',{'summary':artifact(output/'summary.json'),'compact':artifact(output/'summary.json.gz'),'tradeoff':artifact(output/'tradeoff.csv'),'report_checksum':result['report_checksum']})
    return result
def main():
    q=argparse.ArgumentParser(description=__doc__)
    for key in ['protocol','evaluation','verification','baseline','previous']:q.add_argument('--'+key,type=Path,required=True)
    a=q.parse_args();log,paths=setup_run('fault_type_continuous_report_v2')
    kwargs={k:read(getattr(a,k)) for k in ['protocol','evaluation','verification','baseline','previous']}
    r=run(None,output=paths.output_dir,**kwargs);log.info('report={} complete={} gates={}',r['report_checksum'],r['completed_runs'],{k:x['main_screen'] for k,x in r['reliability'].items()})
if __name__=='__main__':main()

