"""Stream saved runs, verify score formulas and paired IDs; never select winner."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np
from core.fault_type_accuracy import study_metrics
from core.fault_type_accuracy_pipeline import records_for
from core.fault_type_final_guard import seal, verify_seal, digest
from core.fault_type_provenance import save_json
from core.logger import setup_run
from core.formal_data import _sha256_file
from experiments.fault_type_accuracy_registry import check_registry
from experiments.fault_type_accuracy_baseline import context
from experiments.fault_type_fixed_report import load_predictions, nested
from experiments.fault_type_accuracy_study import validate_lock, resolved_model

METRICS=['known_fault_classification.accuracy','known_fault_classification.balanced_accuracy','known_fault_classification.macro_f1',
    'known_classification.accuracy','known_classification.balanced_accuracy','known_classification.macro_f1',
    'unknown_rejection.auroc_unknown_positive','unknown_rejection.aupr_unknown_positive','unknown_rejection.unknown_recall',
    'unknown_rejection.unknown_precision','unknown_rejection.unknown_f1','unknown_rejection.fpr_at_95_tpr',
    'known_rejection_rate','healthy_safety.false_positive_rate','open_set_classification_rate',
    'final_open_set_classification.accuracy','selective.accuracy_all_accepted','selective.coverage']


def verify_rows(rows,run,m,registry,locked,model):
    expected=m['sample_ids']['test'];known=registry['known_labels'];unknown=registry['unknown_labels']
    if [r['sample_id'] for r in rows]!=expected or digest(expected)!=run['test_ids_checksum']:raise ValueError('paired test IDs/order differ')
    by={r['sample_id']:r for r in m['records']}
    for row in rows:
        source=by[row['sample_id']]
        for a,b in [('true_label','label'),('motor_id','t_code'),('rpm','rpm'),('source_file','source_file'),('source_sha256','source_sha256')]:
            if row[a]!=source[b]:raise ValueError('truth/source/condition differs')
        role='unknown_test' if source['label'] in unknown else 'healthy' if source['label']==known[0] else 'known_fault'
        if row['true_role']!=role or row['predicted_known_class'] not in known:raise ValueError('role/class differs')
        if (row['arm_id']!=run['arm_id'] or row['score_id']!=run['score_id'] or row['seed']!=run['seed'] or row['fold_id']!=m['fold_id'] or
            row['registry_checksum']!=registry['registry_checksum'] or row['locked_checksum']!=locked['locked_checksum'] or
            row['manifest_checksum']!=m['manifest_checksum'] or row['model_sha256']!=run['model_artifact']['sha256'] or row['historical_test_exposed'] is not True):raise ValueError('method/lock/exposure differs')
        expected_class_sha=model['reference_artifact']['sha256'] if model['arm_id']=='B' else run['model_artifact']['sha256']
        expected_ref_sha=model['reference_artifact']['sha256'] if model['reference_artifact'] is not None else run['model_artifact']['sha256']
        if row['classifier_model_sha256']!=expected_class_sha or row['reference_model_sha256']!=expected_ref_sha:raise ValueError('classifier/reference SHA differs')
        if set(row['raw_class_scores'])!=set(known) or not np.isfinite(list(row['raw_class_scores'].values())).all() or min(row['raw_class_scores'].values())<0:raise ValueError('raw class scores invalid')
    for key,node in model['nodes'].items():
        rr=[r for r in rows if key=='mixed' or r['rpm']==key]
        raw=np.array([[r['raw_class_scores'][c] for c in known] for r in rr])
        if model['arm_id']=='B':
            scorer=node['scores'][run['score_id']];d=scorer.details(raw);thresholds=scorer.thresholds
        else:
            thresholds=np.array([x['threshold'] for x in node['detectors'][run['score_id']].class_summaries()])
            ratios=raw/np.maximum(thresholds,np.finfo(float).eps)
            d={'score':ratios.min(1),'reject':ratios.min(1)>1,'nearest':ratios.argmin(1),'ratios':ratios,'p_values':None,'candidate_size':None,'threshold':1.}
        for i,r in enumerate(rr):
            if not np.isfinite(r['openset_score']) or not np.isclose(r['openset_score'],d['score'][i],rtol=1e-12,atol=1e-12):raise ValueError('score formula differs')
            reject=bool(d['reject'][i])
            if r['is_unknown']!=reject or r['accepted']!= (not reject) or r['threshold']!=d['threshold'] or r['final_class']!=('unknown' if reject else r['predicted_known_class']):raise ValueError('reject/final direction differs')
            if r['nearest_known_class']!=known[int(d['nearest'][i])]:raise ValueError('nearest reference differs')
            if thresholds is None:
                if r['class_thresholds'] is not None or r['normalized_class_scores'] is not None:raise ValueError('conformal thresholds not quantiles')
                if set(r['class_p_values'])!=set(known) or not np.allclose([r['class_p_values'][c] for c in known],d['p_values'][i],rtol=0,atol=1e-12):raise ValueError('p-value formula/calibration differs')
                if r['candidate_set_size']!=int(d['candidate_size'][i]):raise ValueError('candidate set differs')
            else:
                tau=np.repeat(thresholds,len(known)) if len(thresholds)==1 else thresholds
                if set(r['class_thresholds'])!=set(known) or not np.array_equal([r['class_thresholds'][c] for c in known],tau):raise ValueError('threshold audit differs')
                if set(r['normalized_class_scores'])!=set(known) or not np.allclose([r['normalized_class_scores'][c] for c in known],d['ratios'][i],rtol=1e-12,atol=1e-12):raise ValueError('ratios differ')
                if r['class_p_values'] is not None or r['candidate_set_size'] is not None:raise ValueError('nonconformal p-values invented')
    metric=study_metrics(rows,known,unknown)
    if metric!=run['metrics']:raise ValueError('saved metrics differ')
    for item in run['rpm_metrics']:
        rr=[r for r in rows if r['rpm']==item['rpm']]
        if len(rr)!=item['samples'] or study_metrics(rr,known,unknown)!=item['metrics']:raise ValueError('RPM metrics differ')
    for item in run['configuration_metrics']:
        rr=[r for r in rows if r['true_label']==item['label']]
        recall=float(np.mean([r['predicted_known_class']==item['label'] for r in rr])) if item['label'] in known else None
        if len(rr)!=item['samples'] or recall!=item['classifier_recall'] or float(np.mean([r['is_unknown'] for r in rr]))!=item['rejection_rate']:raise ValueError('configuration metrics differ')
    return {'prediction_value_checksum':digest([[r['sample_id'],r['predicted_known_class'],r['openset_score'],r['is_unknown']] for r in rows]),
            'score_reject_checksum':digest([[r['sample_id'],r['openset_score'],r['is_unknown']] for r in rows]),
            'unknown_nearest_reference_counts':dict(Counter(r['nearest_known_class'] for r in rows if r['true_label'] in unknown))}


def describe(runs):
    result=[]
    for arm,score in sorted({(r['arm_id'],r['score_id']) for r in runs}):
        members=[r for r in runs if (r['arm_id'],r['score_id'])==(arm,score)]
        motors=[]
        for motor in ['T1','T2','T3']:
            rr=[r for r in members if r['motor_roles']['test']==motor]
            motors.append({'motor':motor,'seed_results':[{'seed':r['seed'],'metrics':r['metrics'],'rpm_metrics':r['rpm_metrics'],'configuration_metrics':r.get('configuration_metrics'),
                'unknown_nearest_reference_counts':r.get('verification',{}).get('unknown_nearest_reference_counts')} for r in rr],
                'values':{k:{'mean':float(np.mean(v)) if v and all(x is not None for x in v) else None,'seed_sd':float(np.std(v,ddof=1)) if len(v)>1 and all(x is not None for x in v) else None,'values':v}
                    for k in METRICS for v in [[nested(r['metrics'],k) for r in rr]]},
                'prediction_values_identical_across_seeds':bool(rr) and len({r.get('verification',{}).get('prediction_value_checksum') for r in rr})==1})
        result.append({'arm_id':arm,'score_id':score,'motor_results':motors,
            'equal_motor_descriptive':{k:{'mean':float(np.mean(v)),'minimum':min(v),'maximum':max(v)} for k in METRICS
                for v in [[m['values'][k]['mean'] for m in motors]] if all(x is not None for x in v)}})
    return result


def paired_differences(runs,registry):
    result=[]
    for left,right in registry['pairs']:
        left_scores=['mahalanobis','knn'] if left.startswith('A') else [left]
        for score in left_scores:
            l=[r for r in runs if r['arm_id']==left and r['score_id']==score]
            if '/' in right:ra,rs=right.split('/')
            elif right.startswith('B'):ra,rs=right,right
            else:ra,rs=right,score
            for r in l:
                mate=next(t for t in runs if (t['arm_id'],t['score_id'],t['fold_id'],t['seed'])==(ra,rs,r['fold_id'],r['seed']))
                if mate['test_ids_checksum']!=r['test_ids_checksum']:raise ValueError('paired source IDs differ')
                result.append({'left':left+'/'+score,'right':ra+'/'+rs,'motor':r['motor_roles']['test'],'seed':r['seed'],
                    'delta':{k:nested(r['metrics'],k)-nested(mate['metrics'],k) for k in METRICS if nested(r['metrics'],k) is not None and nested(mate['metrics'],k) is not None}})
    return result


def run(pools, *, registry,locked,evaluation,trusted_root):
    baseline=check_registry(registry);_,_,manifests,_=context(baseline['baseline_index'])
    verify_seal(evaluation,'evaluation_checksum')
    if evaluation['registry_checksum']!=registry['registry_checksum'] or evaluation['locked_checksum']!=locked['locked_checksum']:raise ValueError('evaluation binding differs')
    audits=validate_lock(locked,registry,manifests)
    expected={(a['id'],method,m['fold_id'],s) for a in registry['arms'][1:] for method in ['mahalanobis','knn'] for m in manifests for s in registry['seeds']}
    expected|={(a['id'],a['id'],m['fold_id'],s) for a in registry['score_arms'] for m in manifests for s in registry['seeds']}
    actual=[(r['arm_id'],r['score_id'],r['fold_id'],r['seed']) for r in evaluation['runs']]
    if len(actual)!=198 or set(actual)!=expected:raise ValueError('198 evaluation inventory differs')
    runs=[];total=0;unique=set();model_cache={}
    for r in evaluation['runs']:
        if r['status']!='completed':continue
        artifact=r['model_artifact']
        if artifact not in locked['artifacts']:raise ValueError('prediction model not locked')
        key=artifact['sha256']
        if key not in model_cache:
            model_cache={key:resolved_model(artifact,locked,registry,manifests,audits,trusted_root)}
        rows=load_predictions(r['prediction_artifact']);m=next(m for m in manifests if m['fold_id']==r['fold_id'])
        verification=verify_rows(rows,r,m,registry,locked,model_cache[key])
        total+=len(rows);unique.update(x['sample_id'] for x in rows)
        runs.append(dict(r,verification=verification))
    for r in baseline['baseline_runs']:
        if r['representation']!='vibration75':continue
        rows=load_predictions(r['prediction_artifact'])
        m=next(m for m in manifests if m['fold_id']==r['fold_id'])
        if [x['sample_id'] for x in rows]!=m['sample_ids']['test'] or study_metrics(rows,registry['known_labels'],registry['unknown_labels'])!=r['metrics']:raise ValueError('A0 baseline changed')
        runs.append(dict(r,arm_id='A0',score_id=r['method'],test_ids_checksum=digest(m['sample_ids']['test']),
            configuration_metrics=None,verification={'prediction_value_checksum':digest([[x['sample_id'],x['predicted_known_class'],x['openset_score'],x['is_unknown']] for x in rows])}))
    dependencies=[]
    for r in runs:
        if r['arm_id'] not in ['A5','A6','A7','A8']:continue
        mate=next(t for t in runs if (t['arm_id'],t['score_id'],t['fold_id'],t['seed'])==('A1',r['score_id'],r['fold_id'],r['seed']))
        if r['verification']['score_reject_checksum']!=mate['verification']['score_reject_checksum']:raise ValueError('shared reference changed detector scores')
        dependencies.append({'arm_id':r['arm_id'],'score_id':r['score_id'],'fold_id':r['fold_id'],'seed':r['seed'],'same_A1_score_and_reject':True})
    pairs=paired_differences(runs,registry) if not evaluation['failed_runs'] else []
    if evaluation['completed_runs']!=len(runs)-18 or len(evaluation['failed_runs'])!=198-evaluation['completed_runs']:raise ValueError('completion counts differ')
    return seal({'status':'VERIFIED_SAVED_PREDICTIONS' if not evaluation['failed_runs'] else 'INCOMPLETE_VERIFIED_AVAILABLE_PREDICTIONS','registry_checksum':registry['registry_checksum'],'evaluation_checksum':evaluation['evaluation_checksum'],
        'new_completed_evaluations':evaluation['completed_runs'],'failed_evaluations':evaluation['failed_runs'],'baseline_reused_evaluations':18,
        'new_prediction_records':total,'unique_test_ids':len(unique),'fit_counts':locked['fit_counts'],
        'methods':describe(runs),'runs':runs,'paired_differences':pairs,'shared_classifier_reference_checks':dependencies,
        'selection_policy':'none','selection_sample_ids':[],'scope':registry['scope'],'fresh_final_test':False,'independent_validation_status':'INCOMPLETE',
        'uncertainty':'motor descriptive means/ranges; seed sensitivity only, no IID window confidence intervals'},'report_checksum')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['registry','locked','evaluation']:p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();log,paths=setup_run('fault_type_accuracy_report')
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    result=run(None,registry=read(args.registry),locked=read(args.locked),evaluation=read(args.evaluation),trusted_root=Path.cwd()/'output')
    save_json(paths.output_dir/'verified_results.json',result)
    log.info('{} new runs / {} prediction records verified output={}',result['new_completed_evaluations'],result['new_prediction_records'],paths.output_dir)


if __name__=='__main__':main()
