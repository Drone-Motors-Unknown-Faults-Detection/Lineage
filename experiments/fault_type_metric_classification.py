"""實驗13：封存距離分類與 factory 配對；無選參、無正式預設變更。"""
import argparse
import gzip
import json
import platform
import shutil
import subprocess
import time
from pathlib import Path
import joblib
import numpy as np
import sklearn
from threadpoolctl import threadpool_limits
from loguru import logger
from sklearn.neighbors import KNeighborsClassifier
from core.fault_type_metric_classifiers import PrototypeClassifier, MarginEnergyClassifier, weight_transform
from core.fault_type_continuous import stratified_subset
from core.fault_type_accuracy_pipeline import records_for, check_cell
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal, verify_seal, digest
from core.fault_type_provenance import save_json
from core.fault_type_metrics_v2 import decision, classification
from core.fault_type_reliability import CONTRACT, assess
from core.fault_type_mechanisms import peak_memory_bytes
from core.formal_data import _sha256_file
from core.openset import create_openset_detector
from core.logger import setup_run
from experiments.fault_type_solver_diagnosis import check as solver_check, audit as solver_audit, verify_cell, METHODS
from experiments.fault_type_continuous_registry import read
from experiments.fault_type_fixed_calibration import verify_sources
from experiments.fault_type_literature_study import load_bundle, artifact, write_gzip, read_gzip, make_rows
from experiments.fault_type_mechanism_study import summarized, check_rows, save_immutable
from experiments.fault_type_mechanism_report import predictions, summarize

ARMS = [
    {'id':'E01','classifier':'identity_subset','detector':'C02/M'},
    {'id':'E02','classifier':'metric_subset','detector':'C02/M'},
    {'id':'E03','classifier':'identity_all','detector':'C02/M'},
    {'id':'E04','classifier':'metric_all','detector':'C02/M'},
    {'id':'E05','classifier':'identity_mean','detector':'C02/M'},
    {'id':'E06','classifier':'metric_mean','detector':'C02/M'},
    {'id':'E07','classifier':'metric_multi','detector':'C02/M'},
    {'id':'E08','classifier':'metric_energy','detector':'C02/M'},
    {'id':'E09','classifier':'identity_all','detector':'identity/mahalanobis'},
    {'id':'E10','classifier':'metric_all','detector':'metric/mahalanobis'},
    {'id':'E11','classifier':'identity_all','detector':'identity/knn'},
    {'id':'E12','classifier':'metric_all','detector':'metric/knn'}]
PARAMS = {'neighbors':{'n_neighbors':5,'weights':'distance','algorithm':'brute','p':2,'n_jobs':1},
    'prototypes':{'centers':[1,3],'n_init':10,'max_iter':300,'tol':1e-4,'algorithm':'lloyd'},
    'energy':{'k':3,'mu':.5,'margin':1,'batch_size':128,'targets':'original_harmonic69','aggregation':'original_sums'}}
FILES = ['core/fault_type_metric_classifiers.py','experiments/fault_type_metric_classification.py',
    'docs/experiments/exp13_metric_classification.md']


def build(solver_path, diagnosis_path):
    s = read(solver_path); q, pp, ms, old, audits = solver_check(s)
    d = read(diagnosis_path); verify_seal(d, 'diagnosis_checksum')
    if d['protocol_checksum'] != s['protocol_checksum'] or d['converged_by_method']['hard600'] != 9:
        raise ValueError('nine converged hard600 cells required')
    weights = [a for a in d['artifacts'] if Path(a['path']).name.startswith('hard600_')]
    if len(weights) != 9: raise ValueError('weight inventory')
    p = {k:q[k] for k in ['dataset_fingerprint','known_labels','unknown_labels','rpms','folds','seeds',
        'factory_parameters','exposure_ledger_checksum','manifest_checksums','reliability_contract']}
    p.update(version='exp13_metric_classification_v1', solver_protocol=artifact(solver_path),
        solver_diagnosis=artifact(diagnosis_path), weight_artifacts=weights, arms=ARMS, parameters=PARAMS,
        parent_protocol_checksum=pp['protocol_checksum'], selection_policy='none',selection_sample_ids=[],
        validation_sample_ids=[],shared_validation_calibration=False,fresh_final_test=False,
        scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED',budget={'planned_runs':108,'seconds_per_action':1800,
        'reserve_C_bytes':1000000000,'artifact_estimate_bytes':300000000},
        environment={'python':platform.python_version(),'sklearn':sklearn.__version__},
        implementations=[artifact(Path(f)) for f in FILES],
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    return seal(p,'protocol_checksum')


def check(p):
    verify_seal(p,'protocol_checksum')
    if p['version']!='exp13_metric_classification_v1' or p['arms']!=ARMS or p['parameters']!=PARAMS or p['reliability_contract']!=CONTRACT:
        raise ValueError('fixed definitions changed')
    if (p['selection_policy']!='none' or p['selection_sample_ids'] or p['validation_sample_ids'] or
        p['shared_validation_calibration'] or p['fresh_final_test']): raise ValueError('selection/exposure policy')
    if p['environment']!={'python':platform.python_version(),'sklearn':sklearn.__version__}: raise ValueError('runtime mismatch')
    if [a['path'] for a in p['implementations']] != [str(Path(f).resolve()) for f in FILES]: raise ValueError('source inventory')
    for a in p['implementations']+[p['solver_protocol'],p['solver_diagnosis']]+p['weight_artifacts']:
        if _sha256_file(Path(a['path'])) != a['sha256']: raise ValueError('source SHA changed')
    q,pp,ms,old,audits = solver_check(read(p['solver_protocol']['path']))
    d=read(p['solver_diagnosis']['path']);verify_seal(d,'diagnosis_checksum')
    if p['weight_artifacts']!=[a for a in d['artifacts'] if Path(a['path']).name.startswith('hard600_')]: raise ValueError('weights replaced')
    for k in ['dataset_fingerprint','known_labels','unknown_labels','rpms','folds','seeds','factory_parameters',
              'exposure_ledger_checksum','manifest_checksums','reliability_contract']:
        if p[k]!=q[k]:raise ValueError('parent binding: '+k)
    if p['parent_protocol_checksum']!=pp['protocol_checksum'] or p['budget']!={'planned_runs':108,'seconds_per_action':1800,
        'reserve_C_bytes':1000000000,'artifact_estimate_bytes':300000000}:raise ValueError('parent/budget')
    return q,pp,ms,old,audits


def weight_cell(p,m,pa):
    train=records_for(m,'train'); y=[p['known_labels'].index(r['label']) for r in train]
    ix=stratified_subset(y,[r['rpm'] for r in train],pa['seed'])
    expected=solver_audit(train,[train[i]['sample_id'] for i in ix],m,p['known_labels'])
    expected.update(seed=pa['seed'],parent_model_sha256=pa['sha256'])
    name='hard600_'+m['fold_id']+'_seed'+str(pa['seed'])+'.json'
    a=next(a for a in p['weight_artifacts'] if Path(a['path']).name==name)
    c=read(a['path']);s=read(p['solver_protocol']['path'])
    verify_cell(c,s,expected,next(d for d in METHODS if d['id']=='hard600'))
    if not c['optimizer']['success'] or c['parent_model']!=pa:raise ValueError('invalid metric fit')
    return c,ix


def expected_audits(p,m,pa,ix):
    train=records_for(m,'train');cal=records_for(m,'calibration')
    ids=[r['sample_id'] for r in train];ci=[r['sample_id'] for r in cal];sub=[ids[i] for i in ix]
    result=[]
    for d in p['arms']:
        clf=d['classifier']; use_metric=clf.startswith('metric') or d['detector'].startswith('metric/')
        result.append({'definition':d,'protocol_checksum':p['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],
            'dataset_fingerprint':p['dataset_fingerprint'],'seed':pa['seed'],'motor_roles':m['motor_roles'],
            'parent_sha256':pa['sha256'],'representation_fit_ids':ids,'scaler_fit_ids':ids,
            'classifier_fit_ids':sub if clf.endswith('subset') or clf.endswith('energy') else ids,
            'metric_fit_ids':sub if use_metric else [],'reference_fit_ids':ids,'calibration_sample_ids':ci,
            'selection_sample_ids':[],'selection_policy':'none','shared_validation_calibration':False,
            'metric_reused':'hard600 train-only checkpoint' if use_metric else None})
    return result


def check_audits(actual,p,m,pa,ix):
    if actual != expected_audits(p,m,pa,ix): raise ValueError('fit/calibration/selection source violation')


def budget(p,start):
    if time.perf_counter()-start>p['budget']['seconds_per_action'] or shutil.disk_usage('C:/').free<p['budget']['reserve_C_bytes']:
        raise RuntimeError('resource budget reached; preserve checkpoint')


def load_model(a,p,m,pa):
    path=Path(a['path']);expected_parent=m['fold_id']+'_seed'+str(pa['seed'])
    if path.name!='model.joblib' or path.parent.name!=expected_parent or _sha256_file(path)!=a['sha256']:raise ValueError('model root/SHA')
    b=joblib.load(path);c,ix=weight_cell(p,m,pa)
    if (b['protocol_checksum']!=p['protocol_checksum'] or b['manifest_checksum']!=m['manifest_checksum'] or
        b['parent_sha256']!=pa['sha256'] or b['seed']!=pa['seed'] or b['metric_checkpoint_checksum']!=c['checkpoint_checksum'] or
        b['weights']!=c['optimizer']['weights']):raise ValueError('model/source/weights binding')
    check_audits(b['audits'],p,m,pa,ix)
    if _sha256_file(Path(a['fit_audits']['path']))!=a['fit_audits']['sha256'] or read_gzip(a['fit_audits']['path'])!=b['audits']:raise ValueError('audit SHA')
    y=np.array([p['known_labels'].index(r['label']) for r in records_for(m,'train')])
    for name in ['identity_subset','metric_subset','identity_all','metric_all']:
        model=b['models'][name];yy=y[ix] if name.endswith('subset') else y
        if not np.array_equal(model._y,yy) or any(model.get_params()[k]!=v for k,v in PARAMS['neighbors'].items()):raise ValueError('actual classifier fit labels/config')
        if digest(model._fit_X.tolist())!=b['fit_array_checksums'][name]:raise ValueError('actual classifier fit features')
    for name in ['identity_mean','metric_mean','metric_multi']:
        model=b['models'][name]
        if model.centers!=(3 if name.endswith('multi') else 1) or model.seed!=pa['seed']:raise ValueError('prototype configuration')
    energy=b['models']['metric_energy']
    if not np.array_equal(energy.y_,y[ix]) or energy.weights_.tolist()!=b['weights'] or energy.k!=3 or energy.mu!=.5:raise ValueError('energy fit source')
    return b


def fit(pools,p,output):
    _,pp,ms,old,audits=check(p);before=verify_sources(pools.root,ms[0]);start=time.perf_counter();arts=[]
    with threadpool_limits(limits=1):
        for pa in old['artifacts']:
            budget(p,start);m=next(x for x in ms if x['fold_id']==pa['fold_id']);cell=output/(m['fold_id']+'_seed'+str(pa['seed']));cell.mkdir(exist_ok=True)
            cp=cell/'checkpoint.json'
            if cp.exists():
                saved=read(cp);verify_seal(saved,'checkpoint_checksum');load_model(saved['artifact'],p,m,pa);arts.append(saved['artifact']);continue
            t=time.perf_counter();parent=load_bundle(pa,old,pp,ms,audits);c,ix=weight_cell(p,m,pa)
            train=records_for(m,'train');cal=records_for(m,'calibration');check_cell(train,cal,p['known_labels'])
            X=pools.load(train);C=pools.load(cal);y=np.array([p['known_labels'].index(r['label']) for r in train]);cy=np.array([p['known_labels'].index(r['label']) for r in cal])
            rep=parent['references']['harmonic69/mixed']['transformer'];H=rep.transform(X);HC=rep.transform(C);w=c['optimizer']['weights']
            spaces={'identity':(H,HC),'metric':(weight_transform(H,w),weight_transform(HC,w))};models={};checksums={};detectors={}
            for geom,(Z,ZC) in spaces.items():
                for subset in [True,False]:
                    name=geom+('_subset' if subset else '_all');jj=ix if subset else np.arange(len(Z))
                    models[name]=KNeighborsClassifier(**PARAMS['neighbors']).fit(Z[jj],y[jj]);checksums[name]=digest(Z[jj].tolist())
                models[geom+'_mean']=PrototypeClassifier(1,pa['seed']).fit(Z,y)
                for detector in ['mahalanobis','knn']:
                    detectors[geom+'/'+detector]=create_openset_detector(detector,**p['factory_parameters']).fit(Z,y,ZC,cy)
            models['metric_multi']=PrototypeClassifier(3,pa['seed']).fit(spaces['metric'][0],y)
            models['metric_energy']=MarginEnergyClassifier().fit(H[ix],y[ix],w)
            b={'protocol_checksum':p['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],'seed':pa['seed'],
                'parent_sha256':pa['sha256'],'metric_checkpoint_checksum':c['checkpoint_checksum'],'weights':w,
                'models':models,'detectors':detectors,'fit_array_checksums':checksums,'audits':expected_audits(p,m,pa,ix)}
            joblib.dump(b,cell/'model.joblib',compress=3);write_gzip(cell/'fit_audits.json.gz',b['audits'])
            a=dict(artifact(cell/'model.joblib'),fold_id=m['fold_id'],seed=pa['seed'],parent_artifact=pa,
                fit_audits=artifact(cell/'fit_audits.json.gz'),seconds=time.perf_counter()-t,process_peak_memory_bytes=peak_memory_bytes())
            load_model(a,p,m,pa);save_json(cp,seal({'artifact':a,'protocol_checksum':p['protocol_checksum']},'checkpoint_checksum'));arts.append(a)
            logger.info('封存 {} {:.1f}s',cell.name,a['seconds'])
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('formal source changed')
    lock=seal({'protocol_checksum':p['protocol_checksum'],'artifacts':arts,'selection_policy':'none','selection_sample_ids':[],
        'environment':p['environment'],'source_before':before,'source_after':after,'code_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()},'locked_checksum')
    return save_immutable(output/'locked_study.json',lock,'locked_checksum')


def infer(parent,b,p,X):
    H=parent['references']['harmonic69/mixed']['transformer'].transform(X);spaces={'identity':H,'metric':weight_transform(H,b['weights'])}
    scores={'C02/M':parent['references']['base75/mixed']['detectors']['mahalanobis'].score_samples(parent['references']['base75/mixed']['transformer'].transform(X))}
    preds={};result={}
    for d in p['arms']:
        name=d['classifier'];det=d['detector']
        if name not in preds:preds[name]=b['models'][name].predict(H if name=='metric_energy' else spaces[name.split('_')[0]])
        if det not in scores:scores[det]=b['detectors'][det].score_samples(spaces[det.split('/')[0]])
        result[d['id']]=(preds[name],scores[det],1.)
    return result


def evaluate(pools,p,lock,output,evaluation=None):
    _,pp,ms,old,audits=check(p);verify_seal(lock,'locked_checksum');verify=evaluation is not None
    if lock['protocol_checksum']!=p['protocol_checksum'] or lock['environment']!=p['environment'] or lock['selection_sample_ids'] or len(lock['artifacts'])!=9:raise ValueError('lock binding')
    if verify:
        verify_seal(evaluation,'evaluation_checksum')
        if evaluation['protocol_checksum']!=p['protocol_checksum'] or evaluation['locked_checksum']!=lock['locked_checksum']:raise ValueError('evaluation binding')
    start=time.perf_counter();before=verify_sources(pools.root,ms[0]);runs=[];unique=set();count=0
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(p,start);m=next(x for x in ms if x['fold_id']==a['fold_id']);pa=next(x for x in old['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']))
            if a['parent_artifact']!=pa:raise ValueError('parent binding')
            parent=load_bundle(pa,old,pp,ms,audits);b=load_model(a,p,m,pa);rr=records_for(m,'test');X=pools.load(rr);t=time.perf_counter();values=infer(parent,b,p,X);secs=time.perf_counter()-t
            altered=pools.load([dict(r,label='MUTATED_TRUTH') for r in rr])
            if not np.array_equal(X,altered):raise ValueError('truth entered features')
            if verify:
                again=infer(parent,b,p,altered)
                if any(not np.array_equal(values[k][j],again[k][j]) for k in values for j in [0,1]):raise ValueError('truth-dependent inference')
            for d in p['arms']:
                rid=d['id']+'_'+a['fold_id']+'_seed'+str(a['seed']);cp=output/(rid+'.checkpoint.json');pred,score,th=values[d['id']]
                if verify or cp.exists():
                    r=next(r for r in evaluation['runs'] if r['run_id']==rid) if verify else read(cp)
                    verify_seal(r,'checkpoint_checksum');rows=predictions(r);check_rows(rows,r,m,p,lock)
                    if r['model_artifact']!=a or not np.array_equal(pred,[p['known_labels'].index(x['predicted_known_class']) for x in rows]) or not np.array_equal(score,[x['openset_score'] for x in rows]) or any(x['threshold']!=th for x in rows):raise ValueError('reinference mismatch')
                else:
                    rows=make_rows(rr,pred,score,th,p['known_labels'],d['id'],a['sha256'],p['protocol_checksum'],lock['locked_checksum'])
                    for row in rows:row.update(seed=a['seed'],split_sha=m['manifest_checksum'],final_decision=decision(row['predicted_known_class'],row['openset_score'],th))
                    path=output/(rid+'.jsonl.gz');path.write_bytes(gzip.compress('\n'.join(json.dumps(x,sort_keys=True,allow_nan=False) for x in rows).encode(),compresslevel=3,mtime=0))
                    r={'run_id':rid,'arm_id':d['id'],'fold_id':m['fold_id'],'seed':a['seed'],'motor_roles':m['motor_roles'],'samples':len(rows),
                        'test_ids_checksum':digest(m['sample_ids']['test']),'prediction_artifact':artifact(path),'model_artifact':a,'threshold':th,
                        'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'status':'completed',
                        'shared_bundle_inference_seconds':secs,'runtime_note':'十二方法共用推論時間；非十二次獨立訓練',
                        'process_peak_memory_bytes':peak_memory_bytes()}
                    r.update(summarized(rows,p));check_rows(rows,r,m,p,lock);r=seal(r,'checkpoint_checksum');save_json(cp,r)
                count+=len(rows);unique.update(x['sample_id'] for x in rows)
                runs.append({'run_id':rid,'reinference_exact':True,'truth_mutation_invariant':True,'rows':len(rows)} if verify else r)
            logger.info('{} {} seed{} 十二方法', '重推核對' if verify else '評估',a['fold_id'],a['seed'])
    after=verify_sources(pools.root,ms[0])
    if before!=after or len(runs)!=108 or len({r['run_id'] for r in runs})!=108:raise ValueError('source/matrix mismatch')
    key='verification_checksum' if verify else 'evaluation_checksum';name='verified' if verify else 'evaluation'
    result=seal({'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'runs':runs,'failed_runs':[],
        'planned_runs':108,'completed_runs':len(runs),'prediction_records':count,'unique_samples':len(unique),
        'source_before':before,'source_after':after,'seconds':time.perf_counter()-start,'scope':p['scope'],'fresh_final_test':False},key)
    result=save_immutable(output/(name+'.json'),result,key);write_gzip(output/(name+'.json.gz'),result);return result


def report(p,e,v,baseline,previous,output):
    check(p)
    for x,k in [(e,'evaluation_checksum'),(v,'verification_checksum'),(baseline,'metrics_checksum'),(previous,'evaluation_checksum')]:verify_seal(x,k)
    if v['protocol_checksum']!=p['protocol_checksum'] or e['protocol_checksum']!=p['protocol_checksum'] or v['locked_checksum']!=e['locked_checksum'] or v['completed_runs']!=108 or v['prediction_records']!=e['prediction_records'] or baseline['protocol_checksum']!=p['parent_protocol_checksum']:raise ValueError('report binding')
    controls={c:[r for r in baseline['runs'] if r['arm_id']==c and r['score_id']=='mahalanobis'] for c in ['C02','C17','C24']}
    controls['D01']=[r for r in previous['runs'] if r['arm_id']=='D01'];groups={**controls,**{d['id']:[r for r in e['runs'] if r['arm_id']==d['id']] for d in p['arms']}}
    tables={};gates={};pairs=[]
    for name,rr in groups.items():
        if len(rr)!=9:raise ValueError('report coverage')
        rows=[];derived=[]
        for r in rr:
            x=predictions(r);re=summarized(x,p)
            if re['metrics']!=r['metrics'] or re['rpm_metrics']!=r['rpm_metrics']:raise ValueError('metrics mismatch')
            derived.append(dict(r,configuration_metrics=re['configuration_metrics']))
            if r['seed']==0:rows+=x
        if len(rows)!=28910 or len({x['sample_id'] for x in rows})!=28910:raise ValueError('sample coverage')
        tables[name]=summarize(derived,rows,p)
        # 舊 CONTRACT 的 conditional fault F1 保留；另列完整分母的 final fault F1。
        def final_fault(x):
            truth=['unknown' if r['true_label'] in p['unknown_labels'] else r['true_label'] for r in x]
            final=[decision(r['predicted_known_class'],r['openset_score'],r['threshold']) for r in x]
            return classification(truth,final,p['known_labels']+['unknown'],p['known_labels'][1:])
        tables[name]['final_fault_all_samples']=final_fault(rows)
        tables[name]['final_fault_all_samples_per_motor_seed']=[{'motor':r['motor_roles']['test'],'seed':r['seed'],
            'classification':final_fault(predictions(r))} for r in rr]
        tables[name]['conditional_fault_f1_scope']='known_fault_classification 僅 true known faulty；不包含 healthy／unknown 假陽性'
        if name not in controls:gates[name]=assess(derived,controls,CONTRACT)
    comparisons=[(d['id'],c) for d in p['arms'] for c in controls]+[('E02','E01'),('E04','E03'),('E06','E05'),('E07','E06'),('E08','E02'),('E10','E09'),('E12','E11')]
    for new,old in comparisons:
        for r in groups[new]:
            prior=next(x for x in groups[old] if (x['fold_id'],x['seed'])==(r['fold_id'],r['seed']));nr=predictions(r);orr=predictions(prior)
            if [(x['sample_id'],x['true_label'],x['source_sha256']) for x in nr]!=[(x['sample_id'],x['true_label'],x['source_sha256']) for x in orr]:raise ValueError('paired source/IDs mismatch')
            pairs.append({'method':new,'control':old,'fold_id':r['fold_id'],'seed':r['seed'],'samples':len(nr),
                'classification_flips':sum(a['predicted_known_class']!=b['predicted_known_class'] for a,b in zip(nr,orr)),
                'scores_exact':all(a['openset_score']==b['openset_score'] for a,b in zip(nr,orr)),
                'fault_accuracy_delta_pp':100*(r['metrics']['known_fault_classification']['accuracy']-prior['metrics']['known_fault_classification']['accuracy'])})
    result=seal({'protocol_checksum':p['protocol_checksum'],'evaluation_checksum':e['evaluation_checksum'],'verification_checksum':v['verification_checksum'],
        'methods':tables,'reliability':gates,'paired_differences':pairs,'completed_runs':108,'prediction_records':e['prediction_records'],
        'unique_samples':e['unique_samples'],'fresh_final_test':False,'production_replacement':False,'subsets_tested':1,
        'conclusion':'未產生 global winner；依固定 CONTRACT 保留全部判定；三馬達描述統計，不提供逐窗 IID 信賴區間'},'report_checksum')
    save_json(output/'summary.json',result);write_gzip(output/'summary.json.gz',result);return result


def run(pools,*,action,p,output,lock=None,evaluation=None,verification=None,baseline=None,previous=None):
    if action=='fit':return fit(pools,p,output)
    if action in ['evaluate','verify']:return evaluate(pools,p,lock,output,evaluation if action=='verify' else None)
    if action=='report':return report(p,evaluation,verification,baseline,previous,output)
    raise ValueError('action')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['lock','fit','evaluate','verify','report','smoke'])
    for name in ['solver-protocol','diagnosis','protocol','lock','evaluation','verification','baseline','previous','data-root','resume']:
        parser.add_argument('--'+name,type=Path)
    a=parser.parse_args();log,paths=setup_run('fault_type_metric_classification_'+a.action);out=paths.output_dir
    if a.resume:
        out=a.resume.resolve()
        if out.parent!=paths.output_dir.parent.resolve() or not out.is_dir():raise ValueError('explicit same-action resume root')
    if a.action=='lock':
        if not a.solver_protocol or not a.diagnosis:parser.error('solver-protocol/diagnosis required')
        result=build(a.solver_protocol,a.diagnosis);check(result);save_json(out/'protocol.json',result)
    elif a.action=='smoke':
        rng=np.random.default_rng(42);y=np.repeat(np.arange(3),5);X=rng.normal(size=(15,69))+y[:,None]
        model=MarginEnergyClassifier().fit(X,y,np.ones(69));result={'scope':'SYNTHETIC_ENGINEERING_ONLY','predictions':model.predict(X).tolist()};save_json(out/'smoke.json',result)
    else:
        if not a.protocol:parser.error('protocol required')
        if a.action in ['fit','evaluate','verify'] and not a.data_root:parser.error('data-root required')
        if a.action in ['evaluate','verify'] and not a.lock:parser.error('lock required')
        if a.action in ['verify','report'] and not a.evaluation:parser.error('evaluation required')
        if a.action=='report' and any(getattr(a,k) is None for k in ['verification','baseline','previous']):parser.error('verification/baseline/previous required')
        kwargs={k:read(getattr(a,k)) if getattr(a,k) else None for k in ['lock','evaluation','verification','baseline','previous']}
        result=run(FeatureStore(a.data_root) if a.data_root else None,action=a.action,p=read(a.protocol),output=out,**kwargs)
    log.info('{} 完成，輸出 {}',a.action,out)
if __name__=='__main__':main()
