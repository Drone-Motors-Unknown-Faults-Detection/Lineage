"""實驗15：固定GLVQ／anchor與static配對，無選參、無預設更動。"""
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
from loguru import logger
from threadpoolctl import threadpool_limits
from core.fault_type_discriminative_prototypes import DiscriminativePrototypes,calibrate_ambiguity,OPTIONS,BETA,EPSILON
from core.fault_type_metric_classifiers import weight_transform
from core.fault_type_accuracy_pipeline import records_for,check_cell
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal,verify_seal,digest
from core.fault_type_provenance import save_json
from core.fault_type_metrics_v2 import decision,classification
from core.fault_type_reliability import CONTRACT,assess
from core.fault_type_mechanisms import peak_memory_bytes
from core.formal_data import _sha256_file
from core.logger import setup_run
from experiments.fault_type_metric_classification import check as parent_check,weight_cell,read
from experiments.fault_type_fixed_calibration import verify_sources
from experiments.fault_type_literature_study import artifact,write_gzip,read_gzip,load_bundle,make_rows
from experiments.fault_type_mechanism_study import summarized,check_rows,save_immutable
from experiments.fault_type_mechanism_report import predictions,summarize

MODELS=[{'id':geom+'_'+str(centers)+'_'+variant,'geometry':geom,'centers':centers,'variant':variant}
    for geom in ['identity','metric'] for centers in [1,3] for variant in ['static','glvq','anchored']]
ARMS=[dict(id='G'+str(i*2+j+1).zfill(2),model=d['id'],detector=method) for i,d in enumerate(MODELS) for j,method in enumerate(['C02/M','ambiguity'])]
PARAMETERS={'models':MODELS,'optimizer':OPTIONS,'beta':BETA,'epsilon':EPSILON,'anchor':[0.,.01],
    'prototype_seconds':120,'calibration_quantile':.95,'quantile_method':'linear','strict_reject':'score > threshold',
    'initialization':'all known train class mean or KMeans3','loss_subset_per_class_rpm':20}
BUDGET={'planned_runs':216,'seconds_per_action':1800,'reserve_C_bytes':1000000000,'artifact_estimate_bytes':300000000}
FILES=['core/fault_type_discriminative_prototypes.py','experiments/fault_type_discriminative_prototypes.py','docs/experiments/exp15_discriminative_prototypes.md']
ARTIFACT_BASE=Path('D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/discriminative_prototypes_v1/workspace/output')


def build(parent_path):
    ep=read(parent_path);q,pp,ms,old,audits=parent_check(ep)
    p={k:ep[k] for k in ['dataset_fingerprint','known_labels','unknown_labels','rpms','folds','seeds','factory_parameters','exposure_ledger_checksum','manifest_checksums','reliability_contract']}
    p.update(version='exp15_discriminative_prototypes_v1',parent_protocol=artifact(parent_path),parent_protocol_checksum=pp['protocol_checksum'],
        arms=ARMS,parameters=PARAMETERS,budget=BUDGET,selection_policy='none',selection_sample_ids=[],validation_sample_ids=[],
        shared_validation_calibration=False,fresh_final_test=False,scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED',
        environment={'python':platform.python_version(),'sklearn':sklearn.__version__},implementations=[artifact(Path(f)) for f in FILES],
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    return seal(p,'protocol_checksum')


def check(p):
    verify_seal(p,'protocol_checksum')
    if p['version']!='exp15_discriminative_prototypes_v1' or p['arms']!=ARMS or p['parameters']!=PARAMETERS or p['budget']!=BUDGET or p['reliability_contract']!=CONTRACT:raise ValueError('fixed definitions changed')
    if p['selection_policy']!='none' or p['selection_sample_ids'] or p['validation_sample_ids'] or p['shared_validation_calibration'] or p['fresh_final_test']:raise ValueError('selection/exposure violation')
    if p['environment']!={'python':platform.python_version(),'sklearn':sklearn.__version__}:raise ValueError('native environment required')
    if [a['path'] for a in p['implementations']]!=[str(Path(f).resolve()) for f in FILES]:raise ValueError('source inventory')
    for a in p['implementations']+[p['parent_protocol']]:
        if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('source SHA changed')
    ep=read(p['parent_protocol']['path']);q,pp,ms,old,audits=parent_check(ep)
    for k in ['dataset_fingerprint','known_labels','unknown_labels','rpms','folds','seeds','factory_parameters','exposure_ledger_checksum','manifest_checksums','reliability_contract']:
        if p[k]!=ep[k]:raise ValueError('parent binding '+k)
    if p['parent_protocol_checksum']!=pp['protocol_checksum']:raise ValueError('baseline protocol mismatch')
    return ep,pp,ms,old,audits


def expected_audits(p,m,pa,ix):
    tr=records_for(m,'train');cal=records_for(m,'calibration');check_cell(tr,cal,p['known_labels'])
    ids=[r['sample_id'] for r in tr];ci=[r['sample_id'] for r in cal];sub=[ids[i] for i in ix]
    if set(ids)&set(ci) or set(ids+ci)&set(m['sample_ids']['test']) or len(set(m['motor_roles'].values()))!=3:raise ValueError('role overlap')
    definitions={d['id']:d for d in MODELS}
    return [dict(definition=d,protocol_checksum=p['protocol_checksum'],manifest_checksum=m['manifest_checksum'],dataset_fingerprint=p['dataset_fingerprint'],
        seed=pa['seed'],motor_roles=m['motor_roles'],parent_sha256=pa['sha256'],scaler_fit_ids=ids,representation_fit_ids=ids,
        classifier_initialization_ids=ids,classifier_fit_ids=ids,prototype_loss_fit_ids=sub if definitions[d['model']]['variant']!='static' else [],
        metric_fit_ids=sub if definitions[d['model']]['geometry']=='metric' else [],reference_fit_ids=ids,calibration_sample_ids=ci,
        selection_sample_ids=[],selection_policy='none',shared_validation_calibration=False) for d in ARMS]


def fit_node(definition,Z,C,y,ix,seed):
    model=DiscriminativePrototypes(definition['centers'],definition['variant'],seed).fit(Z,y,ix,seconds=120)
    active=model.optimizer_['success']
    return {'model':model,'status':'completed' if active else 'INCOMPLETE',
        'threshold':calibrate_ambiguity(model,C) if active else None,
        'train_array_checksum':digest(Z.tolist()),'calibration_array_checksum':digest(C.tolist()),
        'train_predictions_checksum':digest(model.predict(Z).tolist()) if active else None}


def verify_node(actual,definition,Z,C,y,ix,seed):
    expected=fit_node(definition,Z,C,y,ix,seed)
    if (actual['model'].signature()!=actual['model'].checksum_ or actual['model'].checksum_!=expected['model'].checksum_ or
        any(actual[k]!=expected[k] for k in ['status','threshold','train_array_checksum','calibration_array_checksum','train_predictions_checksum'])):
        raise ValueError('actual train/calibration prototype source mismatch')
    return {'state_checksum':expected['model'].checksum_,'status':expected['status'],
        'optimizer':expected['model'].optimizer_,'threshold':expected['threshold']}


def source_arrays(pools,parent,p,m,weights):
    tr=records_for(m,'train');cal=records_for(m,'calibration');check_cell(tr,cal,p['known_labels'])
    y=np.array([p['known_labels'].index(r['label']) for r in tr]);rep=parent['references']['harmonic69/mixed']['transformer']
    H=rep.transform(pools.load(tr));C=rep.transform(pools.load(cal))
    return y,{'identity':(H,C),'metric':(weight_transform(H,weights),weight_transform(C,weights))}


def budget(start):
    if time.perf_counter()-start>BUDGET['seconds_per_action'] or shutil.disk_usage('C:/').free<BUDGET['reserve_C_bytes']:raise RuntimeError('resource budget reached; preserve checkpoints')


def load_model(a,p,m,pa,ep):
    if _sha256_file(Path(a['path']))!=a['sha256'] or _sha256_file(Path(a['fit_audits']['path']))!=a['fit_audits']['sha256']:raise ValueError('model/audit SHA')
    b=joblib.load(a['path']);c,ix=weight_cell(ep,m,pa)
    if (b['protocol_checksum']!=p['protocol_checksum'] or b['manifest_checksum']!=m['manifest_checksum'] or b['seed']!=pa['seed'] or
        b['parent_sha256']!=pa['sha256'] or a['parent_artifact']!=pa or b['weights']!=c['optimizer']['weights'] or
        b['audits']!=expected_audits(p,m,pa,ix) or read_gzip(a['fit_audits']['path'])!=b['audits']):raise ValueError('model/source/audit binding')
    if set(b['nodes'])!={d['id'] for d in MODELS}:raise ValueError('prototype inventory')
    for d in MODELS:
        node=b['nodes'][d['id']];model=node['model']
        if model.centers!=d['centers'] or model.variant!=d['variant'] or model.seed!=pa['seed'] or model.signature()!=model.checksum_ or model.options_!=OPTIONS:raise ValueError('prototype definition/signature')
        if (node['status']=='completed')!=model.optimizer_['success'] or (node['threshold'] is None)==model.optimizer_['success']:raise ValueError('convergence/status mismatch')
    return b


def validate_lock(p,lock):
    verify_seal(lock,'locked_checksum');expected={(f['fold_id'],s) for f in p['folds'] for s in p['seeds']}
    if (lock['protocol_checksum']!=p['protocol_checksum'] or lock['environment']!=p['environment'] or lock['selection_policy']!='none' or lock['selection_sample_ids'] or
        len(lock['artifacts'])!=9 or {(a['fold_id'],a['seed']) for a in lock['artifacts']}!=expected):raise ValueError('locked source/policy/inventory')


def fit(pools,p,output):
    ep,pp,ms,old,audits=check(p);before=verify_sources(pools.root,ms[0]);start=time.perf_counter();arts=[]
    with threadpool_limits(limits=1):
        for pa in old['artifacts']:
            budget(start);m=next(x for x in ms if x['fold_id']==pa['fold_id']);cell=output/(m['fold_id']+'_seed'+str(pa['seed']));cell.mkdir(exist_ok=True);cp=cell/'checkpoint.json'
            if cp.exists():
                saved=read(cp);verify_seal(saved,'checkpoint_checksum');load_model(saved['artifact'],p,m,pa,ep);arts.append(saved['artifact']);continue
            t=time.perf_counter();parent=load_bundle(pa,old,pp,ms,audits);c,ix=weight_cell(ep,m,pa);w=c['optimizer']['weights'];y,spaces=source_arrays(pools,parent,p,m,w)
            nodes={d['id']:fit_node(d,*spaces[d['geometry']],y,ix,pa['seed']) for d in MODELS}
            b={'protocol_checksum':p['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],'seed':pa['seed'],'parent_sha256':pa['sha256'],
                'weights':w,'nodes':nodes,'audits':expected_audits(p,m,pa,ix)}
            joblib.dump(b,cell/'model.joblib',compress=3);write_gzip(cell/'fit_audits.json.gz',b['audits'])
            a=dict(artifact(cell/'model.joblib'),fold_id=m['fold_id'],seed=pa['seed'],parent_artifact=pa,fit_audits=artifact(cell/'fit_audits.json.gz'),seconds=time.perf_counter()-t,process_peak_memory_bytes=peak_memory_bytes())
            load_model(a,p,m,pa,ep);save_json(cp,seal({'artifact':a,'protocol_checksum':p['protocol_checksum']},'checkpoint_checksum'));arts.append(a)
            logger.info('封存 {}，成功{}原型模型',cell.name,sum(n['status']=='completed' for n in nodes.values()))
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('formal sources changed')
    return save_immutable(output/'locked_study.json',seal({'protocol_checksum':p['protocol_checksum'],'artifacts':arts,'source_before':before,'source_after':after,
        'selection_policy':'none','selection_sample_ids':[],'environment':p['environment'],'code_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()},'locked_checksum'),'locked_checksum')


def source_verify(pools,p,lock,output):
    ep,pp,ms,old,audits=check(p);validate_lock(p,lock);before=verify_sources(pools.root,ms[0]);cells=[];start=time.perf_counter()
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start);m=next(x for x in ms if x['fold_id']==a['fold_id']);pa=next(x for x in old['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']))
            b=load_model(a,p,m,pa,ep);parent=load_bundle(pa,old,pp,ms,audits);_,ix=weight_cell(ep,m,pa);y,spaces=source_arrays(pools,parent,p,m,b['weights']);verified={}
            for d in MODELS:
                verified[d['id']]=verify_node(b['nodes'][d['id']],d,*spaces[d['geometry']],y,ix,a['seed'])
            cells.append({'fold_id':a['fold_id'],'seed':a['seed'],'model_sha256':a['sha256'],'verified':verified});logger.info('來源重建 {} seed{}',a['fold_id'],a['seed'])
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('formal sources changed')
    result=seal({'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'cells':cells,'source_before':before,'source_after':after,
        'test_numeric_reads':0,'status':'VERIFIED_AVAILABLE_NUMERIC_SOURCES','fresh_final_test':False},'source_verification_checksum');save_json(output/'source_verified.json',result);return result


def infer(parent,b,p,X):
    H=parent['references']['harmonic69/mixed']['transformer'].transform(X);spaces={'identity':H,'metric':weight_transform(H,b['weights'])}
    base=parent['references']['base75/mixed'];base_score=base['detectors']['mahalanobis'].score_samples(base['transformer'].transform(X));cache={};values={};definitions={d['id']:d for d in MODELS}
    for d in ARMS:
        key=d['model'];node=b['nodes'][key]
        if node['status']!='completed':continue
        if key not in cache:
            z=spaces[definitions[key]['geometry']];cache[key]=(node['model'].predict(z),node['model'].ambiguity(z))
        pred,ambiguity=cache[key]
        values[d['id']]=(pred,base_score if d['detector']=='C02/M' else ambiguity,1. if d['detector']=='C02/M' else node['threshold'])
    return values


def evaluate(pools,p,lock,source,output,evaluation=None):
    ep,pp,ms,old,audits=check(p);validate_lock(p,lock);verify_seal(source,'source_verification_checksum');verify=evaluation is not None
    if (source['protocol_checksum']!=p['protocol_checksum'] or source['locked_checksum']!=lock['locked_checksum'] or source['test_numeric_reads']!=0 or
        source['status']!='VERIFIED_AVAILABLE_NUMERIC_SOURCES' or {(c['fold_id'],c['seed'],c['model_sha256']) for c in source['cells']}!={(a['fold_id'],a['seed'],a['sha256']) for a in lock['artifacts']}):raise ValueError('source verification required')
    if verify:
        verify_seal(evaluation,'evaluation_checksum')
        if evaluation['protocol_checksum']!=p['protocol_checksum'] or evaluation['locked_checksum']!=lock['locked_checksum'] or evaluation['source_verification_checksum']!=source['source_verification_checksum']:raise ValueError('evaluation source binding')
    before=verify_sources(pools.root,ms[0]);start=time.perf_counter();runs=[];failed=[];unique=set();count=0
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start);m=next(x for x in ms if x['fold_id']==a['fold_id']);pa=next(x for x in old['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']));b=load_model(a,p,m,pa,ep)
            parent=load_bundle(pa,old,pp,ms,audits);rr=records_for(m,'test');X=pools.load(rr);t=time.perf_counter();values=infer(parent,b,p,X);seconds=time.perf_counter()-t
            altered=pools.load([dict(r,label='MUTATED_TRUTH') for r in rr])
            if not np.array_equal(X,altered):raise ValueError('truth entered features')
            if verify:
                second=infer(parent,b,p,altered)
                if any(not np.array_equal(values[k][j],second[k][j]) for k in values for j in [0,1]):raise ValueError('truth entered inference')
            for d in ARMS:
                rid=d['id']+'_'+a['fold_id']+'_seed'+str(a['seed']);cp=output/(rid+'.checkpoint.json')
                if d['id'] not in values:
                    failed.append({'run_id':rid,'arm_id':d['id'],'fold_id':a['fold_id'],'seed':a['seed'],'status':'INCOMPLETE','reason':b['nodes'][d['model']]['model'].optimizer_['message']});continue
                pred,score,threshold=values[d['id']]
                if verify or cp.exists():
                    r=next(r for r in evaluation['runs'] if r['run_id']==rid) if verify else read(cp);verify_seal(r,'checkpoint_checksum');rows=predictions(r);check_rows(rows,r,m,p,lock)
                    if r['model_artifact']!=a or not np.array_equal(pred,[p['known_labels'].index(x['predicted_known_class']) for x in rows]) or not np.array_equal(score,[x['openset_score'] for x in rows]) or any(x['threshold']!=threshold for x in rows):raise ValueError('reinference mismatch')
                else:
                    rows=make_rows(rr,pred,score,threshold,p['known_labels'],d['id'],a['sha256'],p['protocol_checksum'],lock['locked_checksum'])
                    for row in rows:row.update(seed=a['seed'],split_sha=m['manifest_checksum'],final_decision=decision(row['predicted_known_class'],row['openset_score'],threshold))
                    path=output/(rid+'.jsonl.gz');path.write_bytes(gzip.compress('\n'.join(json.dumps(x,sort_keys=True,allow_nan=False) for x in rows).encode(),compresslevel=3,mtime=0))
                    r=dict(run_id=rid,arm_id=d['id'],fold_id=m['fold_id'],seed=a['seed'],motor_roles=m['motor_roles'],samples=len(rows),model_artifact=a,prediction_artifact=artifact(path),
                        threshold=threshold,test_ids_checksum=digest(m['sample_ids']['test']),protocol_checksum=p['protocol_checksum'],locked_checksum=lock['locked_checksum'],status='completed',
                        shared_bundle_inference_seconds=seconds,process_peak_memory_bytes=peak_memory_bytes())
                    r.update(summarized(rows,p));check_rows(rows,r,m,p,lock);r=seal(r,'checkpoint_checksum');save_json(cp,r)
                runs.append(r);count+=len(rows);unique.update(x['sample_id'] for x in rows)
            logger.info('配對 {} seed{}，完成{}方法',a['fold_id'],a['seed'],len(values))
    after=verify_sources(pools.root,ms[0]);inventory=[r['run_id'] for r in runs+failed]
    if before!=after or len(inventory)!=216 or len(set(inventory))!=216:raise ValueError('source/matrix mismatch')
    if verify and failed!=evaluation['failed_runs']:raise ValueError('failure inventory changed')
    key='verification_checksum' if verify else 'evaluation_checksum';name='verified' if verify else 'evaluation'
    result=seal(dict(protocol_checksum=p['protocol_checksum'],locked_checksum=lock['locked_checksum'],source_verification_checksum=source['source_verification_checksum'],runs=runs,
        failed_runs=failed,planned_runs=216,completed_runs=len(runs),prediction_records=count,unique_samples=len(unique),source_before=before,source_after=after,
        seconds=time.perf_counter()-start,fresh_final_test=False,scope=p['scope']),key)
    result=save_immutable(output/(name+'.json'),result,key);write_gzip(output/(name+'.json.gz'),result);return result


def report(p,e,v,baseline,previous,output):
    check(p)
    for x,key in [(e,'evaluation_checksum'),(v,'verification_checksum'),(baseline,'metrics_checksum'),(previous,'evaluation_checksum')]:verify_seal(x,key)
    if e['runs']!=v['runs'] or e['failed_runs']!=v['failed_runs'] or e['protocol_checksum']!=p['protocol_checksum'] or v['protocol_checksum']!=p['protocol_checksum'] or baseline['protocol_checksum']!=p['parent_protocol_checksum']:raise ValueError('report source binding')
    controls={c:[r for r in baseline['runs'] if r['arm_id']==c and r['score_id']=='mahalanobis'] for c in ['C02','C17','C24']};controls['D01']=[r for r in previous['runs'] if r['arm_id']=='D01']
    groups={**controls,**{d['id']:[r for r in e['runs'] if r['arm_id']==d['id']] for d in ARMS}};tables={};gates={};paired=[]
    for name,rr in groups.items():
        if len(rr)!=9:
            tables[name]={'status':'INCOMPLETE','completed_runs':len(rr),'failures':[r for r in e['failed_runs'] if r['arm_id']==name]};continue
        rows=[];derived=[]
        for r in rr:
            x=predictions(r);re=summarized(x,p)
            if re['metrics']!=r['metrics'] or re['rpm_metrics']!=r['rpm_metrics']:raise ValueError('saved metrics mismatch')
            derived.append(dict(r,configuration_metrics=re['configuration_metrics']))
            if r['seed']==0:rows+=x
        if len(rows)!=28910 or len({r['sample_id'] for r in rows})!=28910:raise ValueError('unique samples mismatch')
        tables[name]=summarize(derived,rows,p)
        truth=['unknown' if r['true_label'] in p['unknown_labels'] else r['true_label'] for r in rows];final=[decision(r['predicted_known_class'],r['openset_score'],r['threshold']) for r in rows]
        tables[name]['final_fault_all_samples']=classification(truth,final,p['known_labels']+['unknown'],p['known_labels'][1:])
        tables[name]['conditional_fault_f1_scope']='僅true known faulty；完整分母另列'
        if name not in controls:gates[name]=assess(derived,controls,CONTRACT)
    comparisons=[(d['id'],c) for d in ARMS for c in controls]
    for i,d in enumerate(MODELS):
        for old_i in ([i-1] if d['variant']=='glvq' else [i-1,i-2] if d['variant']=='anchored' else []):
            comparisons +=[(ARMS[i*2+j]['id'],ARMS[old_i*2+j]['id']) for j in [0,1]]
        if d['geometry']=='metric':comparisons +=[(ARMS[i*2+j]['id'],ARMS[(i-6)*2+j]['id']) for j in [0,1]]
        if d['centers']==3:comparisons +=[(ARMS[i*2+j]['id'],ARMS[(i-3)*2+j]['id']) for j in [0,1]]
    for new,old in comparisons:
        for r in groups[new]:
            prior=next((x for x in groups[old] if (x['fold_id'],x['seed'])==(r['fold_id'],r['seed'])),None)
            if prior is None:continue
            x=predictions(r);y=predictions(prior)
            if [(a['sample_id'],a['true_label'],a['source_sha256']) for a in x]!=[(a['sample_id'],a['true_label'],a['source_sha256']) for a in y]:raise ValueError('paired IDs/truth/source')
            paired.append(dict(method=new,control=old,fold_id=r['fold_id'],seed=r['seed'],samples=len(x),fault_accuracy_delta_pp=100*(r['metrics']['known_fault_classification']['accuracy']-prior['metrics']['known_fault_classification']['accuracy'])))
    result=seal(dict(protocol_checksum=p['protocol_checksum'],evaluation_checksum=e['evaluation_checksum'],verification_checksum=v['verification_checksum'],methods=tables,reliability=gates,
        paired_differences=paired,completed_runs=e['completed_runs'],failed_runs=e['failed_runs'],prediction_records=e['prediction_records'],unique_samples=e['unique_samples'],
        subsets_tested=1,fresh_final_test=False,production_replacement=False,conclusion='固定原型探索比較，無global winner；採集來源UNKNOWN、獨立final guard INCOMPLETE'),'report_checksum')
    save_json(output/'summary.json',result);write_gzip(output/'summary.json.gz',result);return result


def run(pools,*,action,p,output,lock=None,source_verification=None,evaluation=None,verification=None,baseline=None,previous=None):
    if action=='fit':return fit(pools,p,output)
    if action=='source-verify':return source_verify(pools,p,lock,output)
    if action in ['evaluate','verify']:return evaluate(pools,p,lock,source_verification,output,evaluation if action=='verify' else None)
    if action=='report':return report(p,evaluation,verification,baseline,previous,output)
    raise ValueError('unsupported action')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['lock','fit','source-verify','evaluate','verify','report','smoke','backup'])
    for key in ['parent-protocol','protocol','lock','source-verification','evaluation','verification','baseline','previous','data-root','resume']:parser.add_argument('--'+key,type=Path)
    parser.add_argument('--archive-root',type=Path,action='append');a=parser.parse_args();log,paths=setup_run('fault_type_discriminative_prototypes_'+a.action.replace('-','_'));out=paths.output_dir
    if a.action in ['fit','evaluate','verify']:
        out=ARTIFACT_BASE/paths.output_dir.parent.name/paths.output_dir.name;out.mkdir(parents=True,exist_ok=False)
    if a.resume:
        candidate=a.resume.resolve()
        if candidate.parent!=ARTIFACT_BASE.resolve()/paths.output_dir.parent.name or not candidate.is_dir():raise ValueError('explicit same-action experiment resume root')
        out=candidate
    if a.action=='backup':
        if not a.archive_root:parser.error('archive-root required')
        roots=[r.resolve() for r in a.archive_root]
        if len({r.name for r in roots})!=len(roots):raise ValueError('archive timestamp collision')
        for r in roots:
            if ARTIFACT_BASE.resolve() not in r.parents or not r.is_dir() or not any((r/n).is_file() for n in ['locked_study.json','evaluation.json','verified.json']):raise ValueError('only completed experiment outputs')
        from experiments.fault_type_archive import run as archive
        from experiments.fault_type_fixed_delivery import run as verify_archive
        result=archive(roots,destination=ARTIFACT_BASE.parents[1]/'archives',paths=paths,log=log)
        save_json(out/'member_verification.json',verify_archive(None,indices=[out/'archive_index.json']))
    elif a.action=='lock':
        if not a.parent_protocol:parser.error('parent-protocol required')
        result=build(a.parent_protocol);check(result);save_json(out/'protocol.json',result)
    elif a.action=='smoke':
        rng=np.random.default_rng(42);X=np.r_[rng.normal(-1,.3,(30,5)),rng.normal(1,.3,(30,5))];y=np.repeat([0,1],30)
        model=DiscriminativePrototypes(1,'anchored').fit(X,y,np.arange(60))
        if not model.optimizer_['success']:raise ValueError('synthetic optimizer failed')
        result={'scope':'SYNTHETIC_ENGINEERING_ONLY','state_checksum':model.checksum_,'optimizer':model.optimizer_,'threshold':calibrate_ambiguity(model,X)};save_json(out/'smoke.json',result)
    else:
        if not a.protocol:parser.error('protocol required')
        if a.action in ['fit','source-verify','evaluate','verify'] and not a.data_root:parser.error('data-root required')
        if a.action in ['source-verify','evaluate','verify'] and not a.lock:parser.error('lock required')
        if a.action in ['evaluate','verify'] and not a.source_verification:parser.error('source-verification required')
        if a.action in ['verify','report'] and not a.evaluation:parser.error('evaluation required')
        if a.action=='report' and any(getattr(a,k) is None for k in ['verification','baseline','previous']):parser.error('report sources required')
        kwargs={k:read(getattr(a,k)) if getattr(a,k) else None for k in ['lock','source_verification','evaluation','verification','baseline','previous']}
        result=run(FeatureStore(a.data_root) if a.data_root else None,action=a.action,p=read(a.protocol),output=out,**kwargs)
    if a.action in ['fit','evaluate','verify']:
        name={'fit':'locked_study.json','evaluate':'evaluation.json.gz','verify':'verified.json.gz'}[a.action];shutil.copyfile(out/name,paths.output_dir/name)
        save_json(paths.output_dir/'artifact_location.json',{'primary_output':str(out.resolve()),'compact_artifact':artifact(paths.output_dir/name),'primary_artifact':artifact(out/name),'contains_raw_data':False})
    log.info('{} 完成，輸出 {}',a.action,out)
if __name__=='__main__':main()
