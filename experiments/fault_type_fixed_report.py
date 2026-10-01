"""Recompute sealed fixed-method predictions; descriptive, no selected winner."""
from __future__ import annotations
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import numpy as np
from core.fault_type_final_guard import digest,verify_seal,seal
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run
from core.fault_type_fixed_calibration import fixed_manifests
from experiments.fault_type_model_selection import load_prior_manifests
from experiments.fault_type_fixed_calibration import metrics_for,check_protocol


METRICS=['known_classification.accuracy','known_classification.balanced_accuracy','known_classification.macro_f1',
         'known_fault_classification.accuracy','known_fault_classification.macro_f1',
         'unknown_rejection.auroc_unknown_positive','unknown_rejection.aupr_unknown_positive',
         'unknown_rejection.unknown_recall','unknown_rejection.unknown_precision','unknown_rejection.unknown_f1',
         'unknown_rejection.fpr_at_95_tpr','known_rejection_rate','healthy_safety.false_positive_rate',
         'open_set_classification_rate','final_open_set_classification.accuracy','final_open_set_classification.macro_f1']


def nested(metrics,path):
    for key in path.split('.'): metrics=metrics[key]
    return metrics


def load_predictions(artifact):
    path=Path(artifact['path'])
    if _sha256_file(path)!=artifact['sha256']: raise ValueError('prediction SHA mismatch')
    rows=[json.loads(line) for line in gzip.decompress(path.read_bytes()).decode().splitlines()]
    if len(rows)!=artifact['rows']: raise ValueError('prediction row count mismatch')
    return rows


def verify_rows(rows, run, manifest, protocol, locked):
    expected=manifest['sample_ids']['test']
    if [r['sample_id'] for r in rows]!=expected or digest(expected)!=run['test_ids_checksum']:
        raise ValueError('prediction IDs/order differ from manifest')
    by={r['sample_id']:r for r in manifest['records']}
    known,unknown=locked['known_labels'],locked['unknown_labels']
    for r in rows:
        source=by[r['sample_id']]
        if any(r[k]!=source[v] for k,v in [('true_label','label'),('motor_id','t_code'),('rpm','rpm'),('source_file','source_file'),('source_sha256','source_sha256')]):
            raise ValueError('prediction source/truth/condition mismatch')
        role='unknown_test' if source['label'] in unknown else 'healthy' if source['label']==known[0] else 'known_fault'
        if r['true_role']!=role or r['condition_id']!=r['motor_id']+'/'+r['rpm']:
            raise ValueError('prediction class role/condition mismatch')
        for k in ['representation','seed','fold_id']:
            if r[k]!=run[k]: raise ValueError('prediction method identity mismatch')
        if (r['openset_method']!=run['method'] or r['protocol_checksum']!=protocol['protocol_checksum'] or
            r['locked_checksum']!=locked['locked_checksum'] or r['manifest_checksum']!=manifest['manifest_checksum'] or
            r['historical_test_exposed'] is not True): raise ValueError('prediction lock/exposure binding mismatch')
        if r['predicted_known_class'] not in known: raise ValueError('unknown classifier prediction')
        raw=r['raw_class_scores']; thresholds=r['class_thresholds']; ratios=r['normalized_class_scores']
        if any(set(x)!=set(known) for x in [raw,thresholds,ratios]): raise ValueError('per-class score coverage mismatch')
        calculated=[raw[k]/max(thresholds[k],np.finfo(float).eps) for k in known]
        if not np.isfinite(calculated).all() or not np.allclose(calculated,[ratios[k] for k in known],rtol=1e-12,atol=1e-12):
            raise ValueError('raw distance normalization mismatch')
        score=min(calculated)
        if not np.isfinite(r['openset_score']) or not np.isclose(r['openset_score'],score,rtol=1e-12,atol=1e-12):
            raise ValueError('saved score differs from normalized minimum')
        if r['threshold']!=1 or r['is_unknown']!=bool(score>1) or r['accepted']!=bool(score<=1):
            raise ValueError('reject comparison/direction mismatch')
        if r['nearest_known_class']!=known[int(np.argmin(calculated))]: raise ValueError('nearest class mismatch')
        if r['final_class']!=('unknown' if score>1 else r['predicted_known_class']): raise ValueError('final class mismatch')
    if metrics_for(rows,known,unknown)!=run['metrics']: raise ValueError('saved metrics differ from prediction recomputation')
    for item in run['rpm_metrics']:
        members=[r for r in rows if r['rpm']==item['rpm']]
        if not members or metrics_for(members,known,unknown)!=item['metrics']: raise ValueError('RPM metrics mismatch')
    return digest([{k:r[k] for k in ['sample_id','predicted_known_class','openset_score','is_unknown']} for r in rows])


def verify_report(report, *, manifests, protocol, locked):
    verify_seal(report,'evaluation_checksum'); verify_seal(locked,'locked_checksum')
    if report['protocol_checksum']!=protocol['protocol_checksum'] or report['locked_checksum']!=locked['locked_checksum']:
        raise ValueError('report lock mismatch')
    if any(k in report for k in ['global_winner','selected_representation']) or report['selection_policy']!='none' or report['selection_sample_ids']:
        raise ValueError('aggregator must not select a method')
    expected={(m['fold_id'],c['name'],method,seed) for m in manifests for c in protocol['representations'] for method in protocol['methods'] for seed in protocol['seeds']}
    runs=report['runs']; actual=[(r['fold_id'],r['representation'],r['method'],r['seed']) for r in runs]
    if set(actual)!=expected or len(actual)!=len(expected) or len(runs)!=report['completed_runs'] or report['failed_runs']:
        raise ValueError('fixed evaluation inventory incomplete')
    by={m['fold_id']:m for m in manifests}
    # Store small run metadata plus rows for exact paired and historical checks.
    predictions,signatures={},{}
    for r in runs:
        rows=load_predictions(r['prediction_artifact'])
        signatures[r['run_id']]=verify_rows(rows,r,by[r['fold_id']],protocol,locked)
        predictions[r['run_id']]=rows
    paired=[]
    for r in runs:
        if r['method']!='mahalanobis': continue
        other=next(x for x in runs if (x['fold_id'],x['representation'],x['seed'],x['method'])==(r['fold_id'],r['representation'],r['seed'],'knn'))
        if r['test_ids_checksum']!=other['test_ids_checksum']: raise ValueError('detector pairing IDs mismatch')
        if r['metrics']['known_classification']!=other['metrics']['known_classification']: raise ValueError('shared classifier differs')
        paired.append({'fold_id':r['fold_id'],'representation':r['representation'],'seed':r['seed'],
                       'knn_minus_mahalanobis':{k:nested(other['metrics'],k)-nested(r['metrics'],k) for k in METRICS
                           if nested(other['metrics'],k) is not None and nested(r['metrics'],k) is not None}})
    methods=[]
    for candidate in protocol['representations']:
        for method in protocol['methods']:
            rows=[r for r in runs if r['representation']==candidate['name'] and r['method']==method]
            folds=[]
            for m in manifests:
                members=[r for r in rows if r['fold_id']==m['fold_id']]
                values={k:[nested(r['metrics'],k) for r in members] for k in METRICS}
                folds.append({'fold_id':m['fold_id'],'motor_roles':m['motor_roles'],'samples':members[0]['samples'],
                    'seed_results':[{ 'seed':r['seed'],'metrics':r['metrics']} for r in members],
                    'metrics':{k:{'values':v,'mean':float(np.mean(v)) if all(x is not None for x in v) else None,
                                  'seed_sd':float(np.std(v,ddof=1)) if all(x is not None for x in v) else None} for k,v in values.items()},
                    'prediction_values_identical_across_seeds':len({signatures[r['run_id']] for r in members})==1})
            methods.append({'representation':candidate['name'],'method':method,'folds':folds,
                'equal_motor_descriptive':{k:{'mean':float(np.mean(v)),'minimum':min(v),'maximum':max(v)}
                    for k in METRICS for v in [[f['metrics'][k]['mean'] for f in folds]] if all(x is not None for x in v)}})
    result={'status':'VERIFIED_SAVED_PREDICTIONS','completed_evaluations':len(runs),'prediction_records':sum(len(x) for x in predictions.values()),
            'unique_test_sample_ids':len(set(r['sample_id'] for v in predictions.values() for r in v)),
            'selection_policy':'none','methods':methods,'paired_detectors':paired,
            'fresh_final_test':False,'independent_validation_status':'INCOMPLETE',
            'uncertainty':'motor means/ranges only; three seeds are algorithm repeats, no window IID CI',
            'evaluation_checksum':report['evaluation_checksum'],'protocol_checksum':protocol['protocol_checksum']}
    return result,predictions


def historical_difference(report,predictions,historical):
    differences=[]
    for r in report['runs']:
        if r['seed']!=0: continue
        motor=r['motor_roles']['test']
        old=next(x for x in historical['runs'] if x['classifier']==r['representation'] and x['method']==r['method'] and x['fold_id'].endswith('test'+motor[1:]))
        previous=load_predictions(old['prediction_artifact'])
        lookup={x['sample_id']:x for x in previous}; rows=predictions[r['run_id']]
        if set(lookup)!={x['sample_id'] for x in rows}: raise ValueError('historical paired IDs mismatch')
        differences.append({'motor':motor,'representation':r['representation'],'method':r['method'],
            'changed_classifier_predictions':sum(x['predicted_known_class']!=lookup[x['sample_id']]['predicted_known_class'] for x in rows),
            'changed_reject_predictions':sum(x['is_unknown']!=lookup[x['sample_id']]['is_unknown'] for x in rows),
            'maximum_absolute_score_difference':max(abs(x['openset_score']-lookup[x['sample_id']]['openset_score']) for x in rows),
            'known_accuracy_difference':r['metrics']['known_classification']['accuracy']-old['metrics']['known_classification']['accuracy'],
            'unknown_recall_difference':r['metrics']['unknown_rejection']['unknown_recall']-old['metrics']['unknown_rejection']['unknown_recall']})
    return {'paired_prior_runs':len(differences),'differences':differences,
            'meaning':'fit/cal computation retained; procedure changes interpretation, not necessarily predictions. Old global selection/shared-valcal is NOT independent final validation.'}


def run(pools, *, report,manifests,protocol,locked,historical=None):
    result,predictions=verify_report(report,manifests=manifests,protocol=protocol,locked=locked)
    if historical is not None: result['historical_comparison']=historical_difference(report,predictions,historical)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['matrix','protocol','locked','ledger','evaluation']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--historical',type=Path)
    args=p.parse_args(); log,paths=setup_run('fault_type_fixed_report')
    protocol=json.loads(args.protocol.read_text(encoding='utf-8')); priors,_=load_prior_manifests(args.matrix)
    manifests=fixed_manifests(priors,protocol); ledger=json.loads(gzip.decompress(args.ledger.read_bytes()))
    check_protocol(protocol,manifests,ledger)
    report=json.loads(args.evaluation.read_text(encoding='utf-8')); locked=json.loads(args.locked.read_text(encoding='utf-8'))
    historical=json.loads(args.historical.read_text(encoding='utf-8')) if args.historical else None
    if args.historical:
        sources=json.loads(Path('reports/fixed_motor_calibration/baseline_sources.json').read_text(encoding='utf-8'))['artifacts']
        expected=next(x['sha256'] for x in sources if x['path']==args.historical.as_posix())
        if _sha256_file(args.historical)!=expected: raise ValueError('historical baseline SHA changed')
    result=run(None,report=report,manifests=manifests,protocol=protocol,locked=locked,historical=historical)
    result['input_artifacts']=[{'path':str(q.resolve()),'sha256':_sha256_file(q)} for q in [args.protocol,args.locked,args.evaluation,args.ledger]]
    save_json(paths.output_dir/'verified_results.json',seal(result,'report_checksum'))
    log.info('{} evaluations / {} records recomputed',result['completed_evaluations'],result['prediction_records'])


if __name__=='__main__': main()
