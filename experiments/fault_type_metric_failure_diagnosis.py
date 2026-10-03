"""實驗13封存後診斷；不擬合、不改門檻、不讀raw。"""
import argparse
from collections import Counter
from pathlib import Path
import numpy as np
from core.fault_type_final_guard import seal,verify_seal
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_metric_classification import check,read
from experiments.fault_type_mechanism_report import predictions
from experiments.fault_type_mechanism_study import check_rows
from experiments.fault_type_literature_study import artifact


def distribution(rows):
    if not rows:return {'status':'N/A','samples':0}
    scores=np.array([r['openset_score'] for r in rows],float)
    thresholds=np.array([r['threshold'] for r in rows],float)
    if not np.isfinite(scores).all() or not np.isfinite(thresholds).all():raise ValueError('finite fixed scores')
    if any(r['is_unknown']!=(r['openset_score']>r['threshold']) for r in rows):raise ValueError('reject direction mismatch')
    return {'status':'DESCRIPTIVE_POSTHOC','samples':len(rows),'quantiles':dict(zip(['min','q25','q50','q75','q95','max'],np.quantile(scores,[0,.25,.5,.75,.95,1]).tolist())),
        'thresholds':sorted(set(thresholds.tolist())),'fixed_rejection_rate':float(np.mean(scores>thresholds)),
        'classifier_output_counts':dict(Counter(r['predicted_known_class'] for r in rows))}


def paired_equal(new,old):
    fields=['sample_id','true_label','source_sha256','predicted_known_class','openset_score','threshold','is_unknown']
    if len(new)!=len(old) or any(any(n[k]!=o[k] for k in fields) for n,o in zip(new,old)):raise ValueError('historical identity control differs')
    return len(new)


def verify_run_binding(evaluation, verification):
    """重推摘要使用精簡 schema；逐 run 核對 ID、筆數及重推結果。"""
    expected={r['run_id']:r['samples'] for r in evaluation['runs']}
    actual={r['run_id']:r['rows'] for r in verification['runs']}
    if (len(expected)!=len(evaluation['runs']) or len(actual)!=len(verification['runs']) or
        expected!=actual or verification['failed_runs'] or evaluation['failed_runs'] or
        any(r['reinference_exact'] is not True or r['truth_mutation_invariant'] is not True for r in verification['runs']) or
        any(evaluation[k]!=verification[k] for k in ['source_before','source_after','unique_samples'])):
        raise ValueError('verified run coverage, sources or reinference differs')


def run(pools,*,protocol,lock,evaluation,verification,prior,output):
    implementation=artifact(Path(__file__))
    p=protocol;q,_,ms,_,_=check(p)
    for x,key in [(lock,'locked_checksum'),(evaluation,'evaluation_checksum'),(verification,'verification_checksum'),(prior,'evaluation_checksum')]:verify_seal(x,key)
    if (evaluation['protocol_checksum']!=p['protocol_checksum'] or evaluation['locked_checksum']!=lock['locked_checksum'] or
        verification['protocol_checksum']!=p['protocol_checksum'] or verification['locked_checksum']!=lock['locked_checksum'] or
        evaluation['completed_runs']!=108 or verification['completed_runs']!=108 or evaluation['prediction_records']!=verification['prediction_records'] or
        prior['protocol_checksum']!=q['protocol_checksum']):raise ValueError('verified binding')
    verify_run_binding(evaluation,verification)
    groups=[];paired=[]
    for r in evaluation['runs']:
        verify_seal(r,'checkpoint_checksum')
        rows=predictions(r);m=next(m for m in ms if m['fold_id']==r['fold_id']);check_rows(rows,r,m,p,lock)
        roles={'healthy':lambda x:x['true_label']==p['known_labels'][0],
            'known_faulty':lambda x:x['true_label'] in p['known_labels'][1:],
            'unknown':lambda x:x['true_label'] in p['unknown_labels']}
        for rpm in [None]+p['rpms']:
            rr=rows if rpm is None else [x for x in rows if x['rpm']==rpm]
            groups.append({'method':r['arm_id'],'motor':r['motor_roles']['test'],'seed':r['seed'],'rpm':rpm or 'ALL_RPM',
                'groups':{name:distribution([x for x in rr if f(x)]) for name,f in roles.items()}})
        if r['arm_id'] in ['E01','E03']:
            old_id={'E01':'Q01','E03':'Q03'}[r['arm_id']]
            old=next(x for x in prior['runs'] if (x['arm_id'],x['fold_id'],x['seed'])==(old_id,r['fold_id'],r['seed']))
            count=paired_equal(rows,predictions(old));paired.append({'method':r['arm_id'],'control':old_id,'fold_id':r['fold_id'],'seed':r['seed'],'samples':count,'status':'EXACT'})
    if len(groups)!=432 or len(paired)!=18:raise ValueError('diagnosis inventory')
    if artifact(Path(__file__))!=implementation:raise ValueError('diagnostic implementation changed during run')
    result=seal({'protocol_checksum':p['protocol_checksum'],'evaluation_checksum':evaluation['evaluation_checksum'],
        'verification_checksum':verification['verification_checksum'],'historical_Q_checksum':prior['evaluation_checksum'],
        'groups':groups,'historical_identity_pairs':paired,'scope':'POSTHOC_DIAGNOSIS_NO_MODEL_OR_THRESHOLD_CHANGE',
        'fresh_final_test':False,'acquisition_independence':'UNKNOWN','implementation':implementation},'diagnosis_checksum')
    save_json(output/'diagnosis.json',result);return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['protocol','lock','evaluation','verification','prior']:parser.add_argument('--'+key,type=Path,required=True)
    a=parser.parse_args();log,paths=setup_run('fault_type_metric_failure_diagnosis')
    result=run(None,**{k:read(getattr(a,k)) for k in ['protocol','lock','evaluation','verification','prior']},output=paths.output_dir)
    log.info('432組描述分布、18組歷史Q精確配對，{}',result['diagnosis_checksum'])
if __name__=='__main__':main()
