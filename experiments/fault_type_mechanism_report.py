"""Paired metric-v2 report, without selector or deployment winner."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import numpy as np
from core.fault_type_metrics_v2 import metrics_v2,decision
from core.fault_type_final_guard import seal,verify_seal,digest
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_mechanism_registry import read
from experiments.fault_type_literature_study import artifact,write_gzip

CONTROLS=[('C02','mahalanobis'),('C02','knn'),('C17','mahalanobis'),('C17','knn'),('C24','mahalanobis'),('C18','mahalanobis'),('R18','R18')]


def predictions(r):
    a=r['prediction_artifact'];path=Path(a['path'])
    if _sha256_file(path)!=a['sha256']:raise ValueError('paired prediction SHA')
    return [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]


def summarize(runs,rows,p):
    seed0=[r for r in runs if r['seed']==0]
    def get(m):
        return {'known_accuracy':m['known_classification']['accuracy'],'fault_accuracy':m['known_fault_classification']['accuracy'],
            'fault_macro_f1':m['known_fault_classification']['macro_f1'],'fault_balanced_accuracy':m['known_fault_classification']['balanced_accuracy'],
            'unknown_auroc':m['unknown_rejection']['auroc_unknown_positive'],'unknown_aupr':m['unknown_rejection']['aupr_unknown_positive'],
            'unknown_recall':m['unknown_rejection']['unknown_recall'],'healthy_total_alarm':m['healthy_safety_v2']['healthy_total_alarm_rate'],
            'healthy_unknown_alarm':m['healthy_safety_v2']['healthy_to_unknown_rate'],'healthy_known_fault_alarm':m['healthy_safety_v2']['healthy_to_known_fault_rate'],
            'coverage':m['selective']['coverage'],'accepted_accuracy':m['selective']['accuracy_all_accepted'],
            'final_accuracy':m['final_open_set_classification']['accuracy']}
    sw=get(metrics_v2(rows,p['known_labels'],p['unknown_labels']));motor=[get(r['metrics']) for r in seed0]
    # Different folds fit different score scales: do NOT create cross-fold ROC pairs.
    for key in ['unknown_auroc','unknown_aupr']:
        sw[key]=float(np.average([t[key] for t in motor],weights=[r['samples'] for r in seed0]))
    rpm=[get(g['metrics']) for r in seed0 for g in r['rpm_metrics']]
    mean=lambda rr:{k:float(np.mean([r[k] for r in rr])) if all(r[k] is not None for r in rr) else None for k in rr[0]}
    worst_class=min(c['classifier_recall'] for r in seed0 for c in r['configuration_metrics'] if c['label'] in p['known_labels'][1:])
    worst_rpm_class=min(c['recall'] for r in seed0 for g in r['rpm_metrics'] for c in g['metrics']['known_fault_classification']['per_class'] if c['recall'] is not None)
    seedvals={}
    for seed in p['seeds']:
        group=[get(r['metrics']) for r in runs if r['seed']==seed];seedvals[str(seed)]=mean(group)
    ranges={k:{'min':min(seedvals[s][k] for s in seedvals),'max':max(seedvals[s][k] for s in seedvals)} for k in seedvals['0'] if all(seedvals[s][k] is not None for s in seedvals)}
    return {'sample_weighted_seed0':sw,'motor_macro_seed0':mean(motor),'motor_rpm_macro_seed0':mean(rpm),
        'worst_motor_unknown_recall':min(r['unknown_recall'] for r in motor),'worst_rpm_unknown_recall':min(r['unknown_recall'] for r in rpm),
        'worst_motor_fault_class_recall':worst_class,'worst_rpm_fault_class_recall':worst_rpm_class,
        'worst_rpm_healthy_total_alarm':max(r['healthy_total_alarm'] for r in rpm),
        'all_nine_health_groups_within_research_limit':all(r['healthy_total_alarm']<=.10 for r in rpm),
        'per_seed_motor_macro':seedvals,'seed_descriptive_range':ranges,
        'auc_aggregation':'sample-weighted mean of within-fold AUROC/AP; no cross-model raw-score ranking',
        'runtime':{'shared_bundle_inference_seconds':sum(r.get('shared_bundle_inference_seconds',0.) for r in runs),
            'process_peak_memory_bytes':max(r.get('process_peak_memory_bytes',0) for r in runs),
            'definition':'same nine-arm shared bundle time, not per-arm time; old control timing unavailable here'},
        'per_motor':[{'motor':r['motor_roles']['test'],'metrics':get(r['metrics']),
            '2screws_recall':next(c['classifier_recall'] for c in r['configuration_metrics'] if c['label']=='2screws'),
            'rpms':r['rpm_metrics'],'classes':r['configuration_metrics']} for r in seed0]}


def run(pools,*,protocol,evaluation,verification,baseline_metrics,output):
    p=protocol;e=evaluation;v=verification;b=baseline_metrics
    for obj,key in [(p,'protocol_checksum'),(e,'evaluation_checksum'),(v,'verification_checksum'),(b,'metrics_checksum')]:verify_seal(obj,key)
    if e['protocol_checksum']!=p['protocol_checksum'] or v['protocol_checksum']!=p['protocol_checksum'] or v['locked_checksum']!=e['locked_checksum'] or v['completed_runs']!=e['completed_runs'] or v['prediction_records']!=e['prediction_records']:raise ValueError('verified report binding')
    if b['protocol_checksum']!=p['parent_protocol_checksum']:raise ValueError('baseline version')
    tables={};pairs=[];allruns=e['runs'];definitions=[(d['id'],None) for d in p['arms']]+CONTROLS
    for method,score_id in definitions:
        source=allruns if score_id is None else b['runs']
        rr=[r for r in source if r['arm_id']==method and (score_id is None or r['score_id']==score_id)]
        if len(rr)!=9:raise ValueError('method inventory missing/duplicate')
        # baseline v2 lacks configuration_metrics: recompute from same saved predictions.
        rows=[];derived=[]
        for r in rr:
            if r['seed']==0:
                x=predictions(r);rows+=x
                if score_id is not None:
                    r=dict(r);r['configuration_metrics']=[{'label':l,'samples':len(xx),'classifier_recall':float(np.mean([t['predicted_known_class']==l for t in xx])) if l in p['known_labels'] else None,'rejection_rate':float(np.mean([t['is_unknown'] for t in xx]))} for l in p['known_labels']+p['unknown_labels'] for xx in [[t for t in x if t['true_label']==l]]]
            derived.append(r)
        if len(rows)!=28910 or len({x['sample_id'] for x in rows})!=28910:raise ValueError('unique paired control coverage')
        label=method if score_id is None else method+'/'+score_id;tables[label]=summarize(derived,rows,p)
    for r in allruns:
        rows=predictions(r)
        for ctl,score in [('C02','mahalanobis'),('C17','mahalanobis'),('C24','mahalanobis')]:
            old=next(x for x in b['runs'] if (x['arm_id'],x['score_id'],x['fold_id'],x['seed'])==(ctl,score,r['fold_id'],r['seed']))
            if r['test_ids_checksum']!=old['test_ids_checksum']:raise ValueError('paired IDs manifest mismatch')
            oldrows=predictions(old)
            if [x['sample_id'] for x in rows]!=[x['sample_id'] for x in oldrows]:raise ValueError('paired row IDs mismatch')
            flips={'known_wrong_to_correct':0,'known_correct_to_wrong':0,'unknown_missed_to_rejected':0,'unknown_rejected_to_missed':0,'healthy_alarm_removed':0,'healthy_alarm_added':0}
            for new,prior in zip(rows,oldrows):
                truth=new['true_label']
                if truth!=prior['true_label']:raise ValueError('paired truth mismatch')
                known=truth in p['known_labels'];nc=new['predicted_known_class']==truth;oc=prior['predicted_known_class']==truth
                flips['known_wrong_to_correct']+=int(known and nc and not oc);flips['known_correct_to_wrong']+=int(known and oc and not nc)
                flips['unknown_missed_to_rejected']+=int(not known and new['is_unknown'] and not prior['is_unknown']);flips['unknown_rejected_to_missed']+=int(not known and prior['is_unknown'] and not new['is_unknown'])
                if truth==p['known_labels'][0]:
                    na=decision(new['predicted_known_class'],new['openset_score'],new['threshold'])!=truth;oa=decision(prior['predicted_known_class'],prior['openset_score'],prior['threshold'])!=truth
                    flips['healthy_alarm_removed']+=int(oa and not na);flips['healthy_alarm_added']+=int(na and not oa)
            pairs.append({'run_id':r['run_id'],'control':ctl+'/'+score,'paired_samples':len(rows),'test_ids_checksum':r['test_ids_checksum'],'flips':flips,
                'differences_percentage_points':{k:(r['metrics']['known_classification']['accuracy']-old['metrics']['known_classification']['accuracy'])*100 for k in ['known_accuracy']}})
    # Decoupling must equal the sealed parent control, not just similar aggregate scores.
    for r in allruns:
        if r['arm_id'] not in ['D01','D02','D03']:continue
        clf='C24' if r['arm_id']=='D03' else 'C17';method='knn' if r['arm_id']=='D02' else 'mahalanobis'
        new=predictions(r)
        cr=next(x for x in b['runs'] if (x['arm_id'],x['score_id'],x['fold_id'],x['seed'])==(clf,'mahalanobis',r['fold_id'],r['seed']))
        dr=next(x for x in b['runs'] if (x['arm_id'],x['score_id'],x['fold_id'],x['seed'])==('C02',method,r['fold_id'],r['seed']))
        cx=predictions(cr);dx=predictions(dr)
        if any(n['predicted_known_class']!=c['predicted_known_class'] or n['openset_score']!=d['openset_score'] or n['threshold']!=d['threshold'] for n,c,d in zip(new,cx,dx)):raise ValueError('decoupling parent mismatch')
    result=seal({'protocol_checksum':p['protocol_checksum'],'evaluation_checksum':e['evaluation_checksum'],'verification_checksum':v['verification_checksum'],
        'baseline_metrics_checksum':b['metrics_checksum'],'methods':tables,'paired_differences':pairs,'runs':allruns,'failed_runs':e['failed_runs'],
        'completed_runs':e['completed_runs'],'planned_runs':81,'prediction_records':e['prediction_records'],'unique_samples':28910,
        'scope':p['scope'],'selection_policy':'none','confidence_intervals':'NOT CALCULATED: acquisition groups UNKNOWN, 3 motors descriptive only',
        'production_default_changed':False,'decoupling_parent_exact':True},'report_checksum')
    save_json(output/'summary.json',result);write_gzip(output/'summary.json.gz',result)
    columns=['method','known_accuracy','fault_accuracy','fault_macro_f1','unknown_auroc','unknown_recall','healthy_total_alarm','coverage','worst_rpm_healthy_total_alarm','worst_motor_fault_class_recall','all_nine_health_groups_within_research_limit']
    with (output/'tradeoff.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for method,t in tables.items():writer.writerow(dict(method=method,**{k:t['motor_macro_seed0'][k] for k in columns[1:8]},**{k:t[k] for k in columns[8:]}))
    save_json(output/'result_index.json',{'summary':artifact(output/'summary.json'),'compact_summary':artifact(output/'summary.json.gz'),'tradeoff':artifact(output/'tradeoff.csv'),'report_checksum':result['report_checksum']})
    return result


def main():
    q=argparse.ArgumentParser(description=__doc__)
    for key in ['protocol','evaluation','verification','baseline-metrics']:q.add_argument('--'+key,type=Path,required=True)
    a=q.parse_args();log,paths=setup_run('fault_type_mechanism_report')
    r=run(None,protocol=read(a.protocol),evaluation=read(a.evaluation),verification=read(a.verification),baseline_metrics=read(a.baseline_metrics),output=paths.output_dir)
    log.info('paired report={} methods={} no selected winner',r['report_checksum'],len(r['methods']))


if __name__=='__main__':main()
