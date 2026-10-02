"""Fit/seal/evaluate/verify the fixed literature study, without a selector."""
from __future__ import annotations
import argparse
import gzip
import json
import time
import warnings
from pathlib import Path
import joblib
import numpy as np
from loguru import logger
from threadpoolctl import threadpool_limits
from core.fault_type_literature import LiteratureRepresentation,NoveltyReference
from core.fault_type_accuracy_pipeline import records_for,check_cell
from core.fault_type_features import FeatureStore
from core.fault_type_accuracy import study_metrics
from core.fault_type_final_guard import digest,seal,verify_seal
from core.formal_data import _sha256_file
from core.openset import create_openset_detector
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_literature_registry import check,classifier
from experiments.fault_type_fixed_calibration import verify_sources
from experiments.fault_type_accuracy_report import describe,METRICS
from experiments.fault_type_fixed_report import nested


def artifact(path):return {'path':str(path.resolve()),'sha256':_sha256_file(path)}
def write_gzip(path,value):path.write_bytes(gzip.compress(json.dumps(value,sort_keys=True,allow_nan=False).encode(),mtime=0))
def read_gzip(path):return json.loads(gzip.decompress(Path(path).read_bytes()))


def audit_roles(audit,m,rpm):
    by={r['sample_id']:r for r in m['records']}
    expected={part:[s for s in m['sample_ids'][part] if rpm=='mixed' or by[s]['rpm']==rpm] for part in ['train','calibration','test']}
    if set(expected['train'])&set(expected['calibration']) or set(expected['train'])&set(expected['test']) or set(expected['calibration'])&set(expected['test']):raise ValueError('role overlap')
    if len(set(m['motor_roles'][p] for p in ['train','calibration','test']))!=3:raise ValueError('motor overlap')
    known=[m['healthy_label'],*m['known_fault_labels']]
    if any(by[s]['label'] not in known for p in ['train','calibration'] for s in expected[p]):raise ValueError('unknown in development')
    for field in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids']:
        if audit[field]!=expected['train']:raise ValueError(field+' differs from train')
    if not set(audit['metric_fit_ids'])<=set(expected['train']):raise ValueError('metric fit outside train')
    if audit['calibration_sample_ids']!=expected['calibration']:raise ValueError('calibration IDs differ')
    if audit['selection_sample_ids'] or audit['selection_policy']!='none' or audit['shared_validation_calibration'] is not False:raise ValueError('selector/shared calibration forbidden')
    if audit['manifest_checksum']!=m['manifest_checksum']:raise ValueError('manifest binding')
    return expected


def fit(pools,*,protocol,manifests,output,code_head):
    before=verify_sources(pools.root,manifests[0]);known=protocol['known_labels'];bundles=[];failures=[];audits=[]
    counts={'representation_fits':0,'classifier_fits':0,'factory_reference_fits':0,'novelty_reference_fits':0}
    with threadpool_limits(limits=1):
        for m in manifests:
            parts={p:records_for(m,p) for p in ['train','calibration']}
            for seed in protocol['seeds']:
                start=time.perf_counter();refs={};models={};score_models={};warnings_seen=[]
                for arm in protocol['arms']:
                    rpms=protocol['rpms'] if arm['rpm_strategy']=='separate' else ['mixed']
                    models[arm['id']]={}
                    for rpm in rpms:
                        train=[r for r in parts['train'] if rpm=='mixed' or r['rpm']==rpm];cal=[r for r in parts['calibration'] if rpm=='mixed' or r['rpm']==rpm]
                        key=arm['representation']+'/'+rpm
                        try:
                            check_cell(train,cal,known,max(5,arm['parameter']) if arm['classifier']=='knn' else 5)
                            X=pools.load(train);C=pools.load(cal);y=np.array([known.index(r['label']) for r in train]);cy=np.array([known.index(r['label']) for r in cal])
                            with warnings.catch_warnings(record=True) as caught:
                                warnings.simplefilter('always')
                                if key not in refs:
                                    transformer=LiteratureRepresentation(arm['representation'],seed).fit(X,y)
                                    Z=transformer.transform(X);CZ=transformer.transform(C)
                                    detectors={method:create_openset_detector(method,**protocol['factory_parameters']).fit(Z,y,CZ,cy) for method in ['mahalanobis','knn']}
                                    refs[key]={'transformer':transformer,'detectors':detectors}
                                    counts['representation_fits']+=1;counts['factory_reference_fits']+=2
                                ref=refs[key];Z=ref['transformer'].transform(X);CZ=ref['transformer'].transform(C)
                                clf=classifier(arm,seed,len(known))
                                if clf.get_params()!=protocol['classifier_parameters'][arm['id']][str(seed)]:raise ValueError('classifier parameters changed')
                                clf.fit(Z,y);counts['classifier_fits']+=1
                            warnings_seen.extend({'arm':arm['id'],'rpm':rpm,'category':w.category.__name__,'message':str(w.message)} for w in caught)
                            audit={'arm_id':arm['id'],'fold_id':m['fold_id'],'seed':seed,'rpm':rpm,'reference_key':key,
                                'protocol_checksum':protocol['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],'motor_roles':m['motor_roles'],
                                'dataset_fingerprint':protocol['dataset_fingerprint'],'selection_policy':'none','selection_sample_ids':[],'shared_validation_calibration':False,
                                'calibration_sample_ids':[r['sample_id'] for r in cal],
                                'metric_fit_ids':[train[i]['sample_id'] for i in ref['transformer'].metric_subset_indices],
                                'optimizer':ref['transformer'].optimizer,'transform_checksum':ref['transformer'].transform_checksum,
                                'classifier_parameters':clf.get_params(),'detector_calibration':{method:d.class_summaries() for method,d in ref['detectors'].items()},'code_head':code_head}
                            for field in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids']:audit[field]=[r['sample_id'] for r in train]
                            audit_roles(audit,m,rpm);audits.append(audit)
                            models[arm['id']][rpm]={'classifier':clf,'reference_key':key,'audit_checksum':digest(audit)}
                        except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:
                            failures.append({'arm_id':arm['id'],'fold_id':m['fold_id'],'seed':seed,'rpm':rpm,'status':'INCOMPLETE','reason':str(e)})
                    logger.info('fit fold={} seed={} {} nodes={}',m['fold_id'],seed,arm['id'],len(models[arm['id']]))
                for definition in protocol['scores']:
                    parent=definition['parent_arm'];node=models[parent].get('mixed')
                    try:
                        if node is None:raise ValueError('parent unavailable')
                        ref=refs[node['reference_key']];transformer=ref['transformer']
                        train=parts['train'];cal=parts['calibration'];Z=transformer.transform(pools.load(train));CZ=transformer.transform(pools.load(cal))
                        y=np.array([known.index(r['label']) for r in train]);cy=np.array([known.index(r['label']) for r in cal])
                        if definition['kind']=='knn_factory':
                            params=dict(protocol['factory_parameters'],knn_neighbors=definition['parameter'])
                            scorer=create_openset_detector('knn',**params).fit(Z,y,CZ,cy);counts['factory_reference_fits']+=1
                        else:
                            scorer=NoveltyReference(definition,seed).fit(Z,y,node['classifier'],ref['detectors']['mahalanobis']).calibrate(CZ)
                            counts['novelty_reference_fits']+=1
                        score_models[definition['id']]={'scorer':scorer,'parent_arm':parent,
                            'resolved_reference_parameters':scorer.get_params() if hasattr(scorer,'get_params') else
                                ([m.get_params() for m in scorer.model] if isinstance(getattr(scorer,'model',None),list) else
                                 scorer.model.get_params() if hasattr(getattr(scorer,'model',None),'get_params') else None),
                            'reference_fit_ids':[r['sample_id'] for r in train],'calibration_sample_ids':[r['sample_id'] for r in cal]}
                    except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:
                        failures.append({'arm_id':definition['id'],'fold_id':m['fold_id'],'seed':seed,'rpm':'mixed','status':'INCOMPLETE','reason':str(e)})
                bundle={'fold_id':m['fold_id'],'seed':seed,'protocol_checksum':protocol['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],
                    'labels':known,'references':refs,'models':models,'score_models':score_models,'warnings':warnings_seen}
                path=output/f"{m['fold_id']}_seed{seed}.joblib";joblib.dump(bundle,path,compress=3)
                bundles.append(dict(artifact(path),fold_id=m['fold_id'],seed=seed,seconds=time.perf_counter()-start))
    audit_path=output/'fit_audits.json.gz';write_gzip(audit_path,audits)
    after=verify_sources(pools.root,manifests[0])
    if after!=before:raise ValueError('source changed during fit')
    lock=seal({'version':protocol['version'],'protocol_checksum':protocol['protocol_checksum'],'environment':protocol['environment'],
        'source_before':before,'source_after':after,'artifacts':bundles,'fit_audits':artifact(audit_path),'failures':failures,'fit_counts':counts,
        'selection_policy':'none','selection_sample_ids':[],'code_head':code_head,'fresh_final_test':False,'historical_test_exposed':True},'locked_checksum')
    save_json(output/'locked_study.json',lock);return lock


def validate_lock(lock,protocol,manifests):
    verify_seal(lock,'locked_checksum')
    if lock['protocol_checksum']!=protocol['protocol_checksum'] or lock['environment']!=protocol['environment'] or lock['selection_policy']!='none' or lock['selection_sample_ids']:raise ValueError('locked config differs')
    if len(lock['artifacts'])!=9 or {(a['fold_id'],a['seed']) for a in lock['artifacts']}!={(m['fold_id'],s) for m in manifests for s in protocol['seeds']}:raise ValueError('bundle inventory differs')
    a=lock['fit_audits']
    if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('fit audit SHA')
    audits=read_gzip(a['path']);by={m['fold_id']:m for m in manifests}
    audit_keys=set()
    for audit in audits:
        key=(audit['arm_id'],audit['fold_id'],audit['seed'],audit['rpm'])
        if key in audit_keys:raise ValueError('duplicate audit')
        audit_keys.add(key);audit_roles(audit,by[audit['fold_id']],audit['rpm'])
        if audit['protocol_checksum']!=protocol['protocol_checksum'] or audit['classifier_parameters']!=protocol['classifier_parameters'][audit['arm_id']][str(audit['seed'])]:raise ValueError('audit configuration changed')
    expected={(a['id'],m['fold_id'],s,rpm) for a in protocol['arms'] for m in manifests for s in protocol['seeds']
              for rpm in (protocol['rpms'] if a['rpm_strategy']=='separate' else ['mixed'])}
    failed={(e['arm_id'],e['fold_id'],e['seed'],e['rpm']) for e in lock['failures'] if e['arm_id'].startswith('C')}
    if audit_keys&failed or audit_keys|failed!=expected:raise ValueError('fit/audit inventory incomplete')
    return audits


def load_bundle(a,lock,protocol,manifests,audits):
    path=Path(a['path']).resolve();trusted=Path(lock['fit_audits']['path']).resolve().parent
    if path.parent!=trusted or _sha256_file(path)!=a['sha256']:raise ValueError('untrusted/tampered model')
    b=joblib.load(path);m=next(m for m in manifests if m['fold_id']==a['fold_id'])
    if b['fold_id']!=a['fold_id'] or b['seed']!=a['seed'] or b['protocol_checksum']!=protocol['protocol_checksum'] or b['manifest_checksum']!=m['manifest_checksum'] or b['labels']!=protocol['known_labels']:raise ValueError('model identity')
    for arm in protocol['arms']:
        for rpm,node in b['models'][arm['id']].items():
            audit=next(x for x in audits if (x['arm_id'],x['fold_id'],x['seed'],x['rpm'])==(arm['id'],a['fold_id'],a['seed'],rpm))
            ref=b['references'][node['reference_key']]
            if node['audit_checksum']!=digest(audit) or node['classifier'].get_params()!=protocol['classifier_parameters'][arm['id']][str(a['seed'])] or ref['transformer'].checksum()!=audit['transform_checksum']:raise ValueError('model fit binding')
            if {k:d.class_summaries() for k,d in ref['detectors'].items()}!=audit['detector_calibration']:raise ValueError('factory calibration changed')
    for s,node in b['score_models'].items():
        if node['reference_fit_ids']!=m['sample_ids']['train'] or node['calibration_sample_ids']!=m['sample_ids']['calibration']:raise ValueError('novelty reference/cal IDs')
        definition=next(d for d in protocol['scores'] if d['id']==s)
        if node['parent_arm']!=definition['parent_arm']:raise ValueError('novelty parent changed')
        if hasattr(node['scorer'],'definition') and node['scorer'].definition!=definition:raise ValueError('novelty definition changed')
    return b


def infer(b,protocol,records,pools):
    raw=pools.load(records);K=protocol['known_labels'];results={};parent_predictions={};parent_features={}
    for arm in protocol['arms']:
        pred=np.empty(len(records),int);scores={k:np.empty(len(records),float) for k in ['mahalanobis','knn']}
        expected_nodes=protocol['rpms'] if arm['rpm_strategy']=='separate' else ['mixed']
        if set(b['models'][arm['id']])!=set(expected_nodes):continue
        for rpm,node in b['models'][arm['id']].items():
            indices=np.array([i for i,r in enumerate(records) if rpm=='mixed' or r['rpm']==rpm],int)
            ref=b['references'][node['reference_key']];X=ref['transformer'].transform(raw[indices]);pred[indices]=node['classifier'].predict(X)
            for method,detector in ref['detectors'].items():scores[method][indices]=detector.score_samples(X)
            if rpm=='mixed':parent_features[arm['id']]=X
        parent_predictions[arm['id']]=pred
        for method,score in scores.items():results[(arm['id'],method)]=(pred,score,1.)
    for definition in protocol['scores']:
        if definition['id'] not in b['score_models']:continue
        scorer=b['score_models'][definition['id']]['scorer'];parent=definition['parent_arm'];X=parent_features[parent]
        score=scorer.score_samples(X) if definition['kind']=='knn_factory' else scorer.raw(X)
        results[(definition['id'],definition['id'])]=(parent_predictions[parent],score,1. if definition['kind']=='knn_factory' else scorer.threshold)
    return results


def make_rows(records,pred,score,threshold,known,method_id,model_sha,protocol_sha,lock_sha):
    if len(records)!=len(pred) or len(records)!=len(score) or not np.isfinite(score).all() or not np.isfinite(threshold):raise ValueError('invalid prediction scores')
    return [{'sample_id':r['sample_id'],'motor_id':r['t_code'],'rpm':r['rpm'],'true_label':r['label'],
        'source_file':r['source_file'],'source_sha256':r['source_sha256'],'predicted_known_class':known[int(pred[i])],
        'openset_score':float(score[i]),'threshold':float(threshold),'is_unknown':bool(score[i]>threshold),
        'method_id':method_id,'model_sha256':model_sha,'protocol_checksum':protocol_sha,'locked_checksum':lock_sha,
        'historical_test_exposed':True} for i,r in enumerate(records)]


def metrics(rows,known,unknown,rpms):
    return {'metrics':study_metrics(rows,known,unknown),
        'rpm_metrics':[{'rpm':rpm,'samples':len(rr),'metrics':study_metrics(rr,known,unknown)} for rpm in rpms for rr in [[r for r in rows if r['rpm']==rpm]]],
        'configuration_metrics':[{'label':label,'samples':len(rr),'classifier_recall':float(np.mean([r['predicted_known_class']==label for r in rr])) if label in known else None,
            'rejection_rate':float(np.mean([r['is_unknown'] for r in rr]))} for label in known+unknown for rr in [[r for r in rows if r['true_label']==label]] if rr]}


def evaluate(pools,*,protocol,manifests,lock,output):
    audits=validate_lock(lock,protocol,manifests);before=verify_sources(pools.root,manifests[0]);runs=[];known=protocol['known_labels'];unknown=protocol['unknown_labels']
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            start=time.perf_counter();b=load_bundle(a,lock,protocol,manifests,audits);m=next(m for m in manifests if m['fold_id']==a['fold_id']);records=records_for(m,'test')
            inferred=infer(b,protocol,records,pools)
            for (arm,score_id),(pred,score,threshold) in inferred.items():
                run_id=f"{arm}_{score_id}_{a['fold_id']}_seed{a['seed']}";method_id=arm+'/'+score_id
                rows=make_rows(records,pred,score,threshold,known,method_id,a['sha256'],protocol['protocol_checksum'],lock['locked_checksum'])
                path=output/(run_id+'.jsonl.gz')
                path.write_bytes(gzip.compress('\n'.join(json.dumps(r,sort_keys=True,allow_nan=False) for r in rows).encode(),compresslevel=3,mtime=0))
                r={'run_id':run_id,'arm_id':arm,'score_id':score_id,'fold_id':a['fold_id'],'seed':a['seed'],'motor_roles':m['motor_roles'],
                    'samples':len(rows),'test_ids_checksum':digest(m['sample_ids']['test']),'prediction_artifact':dict(artifact(path),rows=len(rows)),
                    'model_artifact':a,'status':'completed','threshold':threshold}
                r.update(metrics(rows,known,unknown,protocol['rpms']));runs.append(r)
            logger.info('evaluated fold={} seed={} methods={} elapsed={:.1f}s',a['fold_id'],a['seed'],len(inferred),time.perf_counter()-start)
    identities={(r['arm_id'],r['score_id'],r['fold_id'],r['seed']) for r in runs}
    expected={(a['id'],s,m['fold_id'],seed) for a in protocol['arms'] for s in ['mahalanobis','knn'] for m in manifests for seed in protocol['seeds']}
    expected|={(d['id'],d['id'],m['fold_id'],seed) for d in protocol['scores'] for m in manifests for seed in protocol['seeds']}
    if len(expected)!=630 or len(identities)!=len(runs) or not identities<=expected:raise ValueError('evaluation inventory differs')
    failed=[{'arm_id':a,'score_id':s,'fold_id':f,'seed':seed,'status':'INCOMPLETE','fit_reasons':[e for e in lock['failures'] if (e['arm_id'],e['fold_id'],e['seed'])==(a,f,seed)]} for a,s,f,seed in sorted(expected-identities)]
    after=verify_sources(pools.root,manifests[0])
    if after!=before:raise ValueError('source changed during test')
    result=seal({'protocol_checksum':protocol['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'runs':runs,'failed_runs':failed,
        'completed_runs':len(runs),'prediction_records':sum(r['samples'] for r in runs),'source_before':before,'source_after':after,
        'scope':protocol['scope'],'fresh_final_test':False,'selection_policy':'none'},'evaluation_checksum')
    save_json(output/'evaluation.json',result);return result


def verify_rows(rows,r,m,protocol,lock):
    if [x['sample_id'] for x in rows]!=m['sample_ids']['test'] or digest(m['sample_ids']['test'])!=r['test_ids_checksum']:raise ValueError('paired test IDs changed')
    by={x['sample_id']:x for x in m['records']}
    for x in rows:
        record=by[x['sample_id']]
        if any(x[k]!=record[v] for k,v in [('motor_id','t_code'),('rpm','rpm'),('true_label','label'),('source_file','source_file'),('source_sha256','source_sha256')]):raise ValueError('prediction provenance/truth changed')
        if x['method_id']!=r['arm_id']+'/'+r['score_id'] or x['model_sha256']!=r['model_artifact']['sha256'] or x['protocol_checksum']!=protocol['protocol_checksum'] or x['locked_checksum']!=lock['locked_checksum'] or x['historical_test_exposed'] is not True:raise ValueError('prediction lock/exposure binding')
        if x['predicted_known_class'] not in protocol['known_labels'] or not np.isfinite(x['openset_score']) or x['threshold']!=r['threshold'] or x['is_unknown']!=bool(x['openset_score']>x['threshold']):raise ValueError('prediction score/reject direction')
    if metrics(rows,protocol['known_labels'],protocol['unknown_labels'],protocol['rpms'])!={k:r[k] for k in ['metrics','rpm_metrics','configuration_metrics']}:raise ValueError('saved metrics differ')
    return {'prediction_value_checksum':digest([[x['sample_id'],x['predicted_known_class'],x['openset_score'],x['is_unknown']] for x in rows])}


def verify(pools,*,protocol,manifests,lock,evaluation,output):
    audits=validate_lock(lock,protocol,manifests);verify_seal(evaluation,'evaluation_checksum')
    if evaluation['protocol_checksum']!=protocol['protocol_checksum'] or evaluation['locked_checksum']!=lock['locked_checksum']:raise ValueError('evaluation binding')
    before=verify_sources(pools.root,manifests[0]);runs=[];records_count=0;unique=set();pairs=[]
    # Re-infer from sealed model for every saved sample, not only recompute metrics.
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            start=time.perf_counter();b=load_bundle(a,lock,protocol,manifests,audits);m=next(m for m in manifests if m['fold_id']==a['fold_id']);records=records_for(m,'test');inferred=infer(b,protocol,records,pools)
            rr=[r for r in evaluation['runs'] if (r['fold_id'],r['seed'])==(a['fold_id'],a['seed'])]
            if {(r['arm_id'],r['score_id']) for r in rr}!=set(inferred) or len(rr)!=len(inferred):raise ValueError('saved method inventory')
            for r in rr:
                if r['model_artifact']!=a:raise ValueError('model artifact replaced')
                pa=r['prediction_artifact'];path=Path(pa['path'])
                if _sha256_file(path)!=pa['sha256']:raise ValueError('prediction SHA changed')
                rows=[json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
                if len(rows)!=r['samples'] or len(rows)!=pa['rows']:raise ValueError('prediction count')
                verification=verify_rows(rows,r,m,protocol,lock);pred,score,threshold=inferred[(r['arm_id'],r['score_id'])]
                if [x['predicted_known_class'] for x in rows]!=[protocol['known_labels'][int(c)] for c in pred] or not np.array_equal([x['openset_score'] for x in rows],score) or threshold!=r['threshold']:raise ValueError('sealed model inference differs')
                runs.append(dict(r,verification=verification));records_count+=len(rows);unique.update(x['sample_id'] for x in rows)
            baseline=next(r for r in rr if (r['arm_id'],r['score_id'])==('C02','mahalanobis'))
            for r in rr:
                if r['test_ids_checksum']!=baseline['test_ids_checksum']:raise ValueError('unpaired test IDs')
                pairs.append({'method_id':r['arm_id']+'/'+r['score_id'],'against':'C02/mahalanobis','test_motor':m['motor_roles']['test'],'seed':a['seed'],
                    'delta':{k:nested(r['metrics'],k)-nested(baseline['metrics'],k) for k in METRICS if nested(r['metrics'],k) is not None and nested(baseline['metrics'],k) is not None}})
            logger.info('verified fresh sealed inference fold={} seed={} methods={} {:.1f}s',a['fold_id'],a['seed'],len(rr),time.perf_counter()-start)
    if len(runs)!=evaluation['completed_runs'] or records_count!=evaluation['prediction_records'] or len(runs)+len(evaluation['failed_runs'])!=630:raise ValueError('total inventory differs')
    after=verify_sources(pools.root,manifests[0])
    if after!=before:raise ValueError('source changed during verification')
    result=seal({'status':'VERIFIED_AVAILABLE_RESULTS','scope':protocol['scope'],'protocol_checksum':protocol['protocol_checksum'],'locked_checksum':lock['locked_checksum'],
        'evaluation_checksum':evaluation['evaluation_checksum'],'completed_runs':len(runs),'failed_runs':evaluation['failed_runs'],'prediction_records':records_count,'unique_test_rows':len(unique),
        'methods':describe(runs),'paired_differences':pairs,'runs':runs,'fit_counts':lock['fit_counts'],'fit_failures':lock['failures'],
        'source_before':before,'source_after':after,'selection_policy':'none','fresh_final_test':False,'independent_validation':'INCOMPLETE'},'report_checksum')
    save_json(output/'verified.json',result);write_gzip(output/'verified.json.gz',result);return result


def run(pools,*,action,protocol,output,code_head,locked=None,evaluation=None):
    manifests=check(protocol)
    if action=='fit':return fit(pools,protocol=protocol,manifests=manifests,output=output,code_head=code_head)
    if locked is None:raise ValueError('sealed lock required')
    if action=='evaluate':return evaluate(pools,protocol=protocol,manifests=manifests,lock=locked,output=output)
    if action=='verify' and evaluation is not None:return verify(pools,protocol=protocol,manifests=manifests,lock=locked,evaluation=evaluation,output=output)
    raise ValueError('unsupported action/inputs')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['fit','evaluate','verify']);p.add_argument('--protocol',type=Path,required=True)
    p.add_argument('--data-root',type=Path,required=True);p.add_argument('--locked',type=Path);p.add_argument('--evaluation',type=Path);p.add_argument('--code-head',default='engineering-test')
    a=p.parse_args();log,paths=setup_run('fault_type_literature_'+a.action)
    read=lambda path:json.loads(path.read_text(encoding='utf-8')) if path else None
    result=run(FeatureStore(a.data_root),action=a.action,protocol=read(a.protocol),output=paths.output_dir,code_head=a.code_head,locked=read(a.locked),evaluation=read(a.evaluation))
    log.info('{} complete; output={} count={}',a.action,paths.output_dir,result.get('completed_runs',len(result.get('artifacts',[]))))


if __name__=='__main__':main()
