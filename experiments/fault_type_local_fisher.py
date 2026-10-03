"""實驗14：固定 LFDA/PCA 配對與來源重建，正式預設不變。"""
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
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neighbors import KNeighborsClassifier
from threadpoolctl import threadpool_limits
from loguru import logger
from core.fault_type_local_fisher import LocalProjection
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
from experiments.fault_type_continuous_registry import read, check as parent_check
from experiments.fault_type_fixed_calibration import verify_sources
from experiments.fault_type_literature_study import load_bundle, artifact, write_gzip, make_rows
from experiments.fault_type_mechanism_study import summarized, check_rows, save_immutable
from experiments.fault_type_mechanism_report import predictions, summarize

REPRESENTATIONS = [{'id':kind+str(rank),'kind':kind,'dimension':rank} for kind in ['pca','lfda'] for rank in [10,20]]
ARMS = [{'id':'F'+str(i*4+j+1).zfill(2),'representation':rep['id'],'classifier':classifier,'detector':detector}
        for i,rep in enumerate(REPRESENTATIONS) for j,(classifier,detector) in enumerate([
            ('lda','C02/M'),('knn','C02/M'),('knn','mahalanobis'),('knn','knn')])]
PARAMETERS = {'representation':{'k':7,'ridge_relative':1e-6,'scale_floor_relative':1e-12,'scale_floor_absolute':1e-12,
    'embedding':'weighted','pca_solver':'full','pca_whiten':False,'subset_per_class_rpm':20},
    'lda':{'solver':'lsqr','shrinkage':'auto','priors':'uniform'},
    'knn':{'n_neighbors':5,'weights':'distance','algorithm':'brute','p':2,'n_jobs':1}}
FILES = ['core/fault_type_local_fisher.py','experiments/fault_type_local_fisher.py','docs/experiments/exp14_local_fisher.md']
BUDGET = {'planned_runs':144,'seconds_per_action':1800,'reserve_C_bytes':1000000000,'artifact_estimate_bytes':300000000}
ARTIFACT_BASE=Path('D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/local_fisher_v1/workspace/output')


def build(parent_path):
    q=read(parent_path);pp,ms,old,audits=parent_check(q)
    p={k:q[k] for k in ['dataset_fingerprint','known_labels','unknown_labels','rpms','folds','seeds','factory_parameters',
        'exposure_ledger_checksum','manifest_checksums','reliability_contract']}
    p.update(version='exp14_local_fisher_v1',q_protocol=artifact(parent_path),parent_protocol_checksum=pp['protocol_checksum'],
        representations=REPRESENTATIONS,arms=ARMS,parameters=PARAMETERS,budget=BUDGET,
        selection_policy='none',selection_sample_ids=[],validation_sample_ids=[],shared_validation_calibration=False,
        fresh_final_test=False,scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED',
        environment={'python':platform.python_version(),'sklearn':sklearn.__version__},
        implementations=[artifact(Path(f)) for f in FILES],source_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    return seal(p,'protocol_checksum')


def check(p):
    verify_seal(p,'protocol_checksum')
    if (p['version']!='exp14_local_fisher_v1' or p['representations']!=REPRESENTATIONS or p['arms']!=ARMS or
        p['parameters']!=PARAMETERS or p['budget']!=BUDGET or p['reliability_contract']!=CONTRACT):raise ValueError('fixed protocol changed')
    if p['selection_policy']!='none' or p['selection_sample_ids'] or p['validation_sample_ids'] or p['shared_validation_calibration'] or p['fresh_final_test']:raise ValueError('selection/exposure policy')
    if p['environment']!={'python':platform.python_version(),'sklearn':sklearn.__version__}:raise ValueError('native runtime required')
    if [a['path'] for a in p['implementations']]!=[str(Path(f).resolve()) for f in FILES]:raise ValueError('implementation inventory')
    for a in p['implementations']+[p['q_protocol']]:
        if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('source SHA changed')
    q=read(p['q_protocol']['path']);pp,ms,old,audits=parent_check(q)
    for k in ['dataset_fingerprint','known_labels','unknown_labels','rpms','folds','seeds','factory_parameters',
        'exposure_ledger_checksum','manifest_checksums','reliability_contract']:
        if p[k]!=q[k]:raise ValueError('parent binding '+k)
    if p['parent_protocol_checksum']!=pp['protocol_checksum']:raise ValueError('parent protocol')
    return pp,ms,old,audits


def expected_audits(p,m,pa,ix):
    tr=records_for(m,'train');cal=records_for(m,'calibration');check_cell(tr,cal,p['known_labels'])
    ids=[r['sample_id'] for r in tr];ci=[r['sample_id'] for r in cal];sub=[ids[i] for i in ix]
    if set(ids)&set(ci) or set(ids+ci)&set(m['sample_ids']['test']) or len(set(m['motor_roles'].values()))!=3:raise ValueError('role overlap')
    return [{'definition':d,'protocol_checksum':p['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],
        'dataset_fingerprint':p['dataset_fingerprint'],'seed':pa['seed'],'motor_roles':m['motor_roles'],'parent_sha256':pa['sha256'],
        'scaler_fit_ids':ids,'upstream_representation_fit_ids':ids,'projection_fit_ids':sub,
        'classifier_fit_ids':ids,'reference_fit_ids':ids,'calibration_sample_ids':ci,'selection_sample_ids':[],
        'selection_policy':'none','shared_validation_calibration':False} for d in p['arms']]


def indices(train,p,seed):
    y=np.array([p['known_labels'].index(r['label']) for r in train])
    return y,stratified_subset(y,[r['rpm'] for r in train],seed)


def fit_representation(definition,H,C,y,cy,ix,p):
    projection=LocalProjection(definition['kind'],definition['dimension']).fit(H[ix],y[ix])
    Z=projection.transform(H);ZC=projection.transform(C)
    models={'knn':KNeighborsClassifier(**PARAMETERS['knn']).fit(Z,y),
        'lda':LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto',priors=np.full(len(p['known_labels']),1/len(p['known_labels']))).fit(Z,y)}
    detectors={method:create_openset_detector(method,**p['factory_parameters']).fit(Z,y,ZC,cy) for method in ['mahalanobis','knn']}
    return {'projection':projection,'classifiers':models,'detectors':detectors,'train_array_checksum':digest(Z.tolist()),
        'calibration_array_checksum':digest(ZC.tolist())}


def detector_state(model):
    if hasattr(model,'distributions_'):
        if model.pca_ is not None:raise ValueError('undeclared detector PCA')
        return digest([model.confidence,model.method,[(a.label,a.threshold,a.location.tolist(),a.precision.tolist()) for a in model.distributions_]])
    return digest([model.confidence,model.n_neighbors,[(a.label,a.threshold,a.n_train,a.n_neighbors,a.neighbors._fit_X.tolist()) for a in model.models_]])


def verify_numeric(node,definition,H,C,y,cy,ix,p):
    expected=fit_representation(definition,H,C,y,cy,ix,p)
    if node['projection'].signature()!=expected['projection'].signature() or node['projection'].checksum_!=expected['projection'].checksum_:raise ValueError('projection actual source')
    for key in ['train_array_checksum','calibration_array_checksum']:
        if node[key]!=expected[key]:raise ValueError('source array checksum')
    a=node['classifiers']['knn'];b=expected['classifiers']['knn']
    if a.get_params()!=b.get_params() or not np.array_equal(a._fit_X,b._fit_X) or not np.array_equal(a._y,b._y):raise ValueError('classifier actual train reference')
    a=node['classifiers']['lda'];b=expected['classifiers']['lda']
    for key in ['coef_','intercept_','priors_','classes_']:
        if not np.array_equal(getattr(a,key),getattr(b,key)):raise ValueError('LDA actual train source')
    for method in ['mahalanobis','knn']:
        if detector_state(node['detectors'][method])!=detector_state(expected['detectors'][method]):raise ValueError('detector reference/calibration actual source')
    return {'projection_checksum':expected['projection'].checksum_,'train_array_checksum':expected['train_array_checksum'],
        'calibration_array_checksum':expected['calibration_array_checksum'],'diagnostics':expected['projection'].diagnostics_}


def load_model(a,p,m,pa):
    if _sha256_file(Path(a['path']))!=a['sha256'] or _sha256_file(Path(a['fit_audits']['path']))!=a['fit_audits']['sha256']:raise ValueError('model/audit SHA')
    b=joblib.load(a['path']);tr=records_for(m,'train');_,ix=indices(tr,p,a['seed'])
    if (b['protocol_checksum']!=p['protocol_checksum'] or b['manifest_checksum']!=m['manifest_checksum'] or b['seed']!=a['seed'] or
        b['parent_sha256']!=pa['sha256'] or a['parent_artifact']!=pa or b['audits']!=expected_audits(p,m,pa,ix)):raise ValueError('model source binding')
    if json.loads(gzip.decompress(Path(a['fit_audits']['path']).read_bytes()))!=b['audits']:raise ValueError('audit file binding')
    if set(b['nodes'])|set(b['failures'])!={d['id'] for d in REPRESENTATIONS} or set(b['nodes'])&set(b['failures']):raise ValueError('representation inventory')
    for definition in REPRESENTATIONS:
        if definition['id'] not in b['nodes']:continue
        node=b['nodes'][definition['id']];proj=node['projection']
        if proj.kind!=definition['kind'] or proj.dimension!=definition['dimension'] or proj.signature()!=proj.checksum_:raise ValueError('projection definition/signature')
    return b


def budget(start):
    if time.perf_counter()-start>BUDGET['seconds_per_action'] or shutil.disk_usage('C:/').free<BUDGET['reserve_C_bytes']:raise RuntimeError('resource budget reached; preserve checkpoints')


def fit(pools,p,output):
    pp,ms,old,audits=check(p);before=verify_sources(pools.root,ms[0]);arts=[];start=time.perf_counter()
    with threadpool_limits(limits=1):
        for pa in old['artifacts']:
            budget(start);m=next(x for x in ms if x['fold_id']==pa['fold_id']);cell=output/(m['fold_id']+'_seed'+str(pa['seed']));cell.mkdir(exist_ok=True);cp=cell/'checkpoint.json'
            if cp.exists():
                c=read(cp);verify_seal(c,'checkpoint_checksum');load_model(c['artifact'],p,m,pa);arts.append(c['artifact']);continue
            t=time.perf_counter();parent=load_bundle(pa,old,pp,ms,audits);tr=records_for(m,'train');cal=records_for(m,'calibration');check_cell(tr,cal,p['known_labels'])
            y,ix=indices(tr,p,pa['seed']);cy=np.array([p['known_labels'].index(r['label']) for r in cal]);rep=parent['references']['harmonic69/mixed']['transformer']
            H=rep.transform(pools.load(tr));C=rep.transform(pools.load(cal));nodes={};failures={}
            for definition in REPRESENTATIONS:
                try:nodes[definition['id']]=fit_representation(definition,H,C,y,cy,ix,p)
                except (ValueError,np.linalg.LinAlgError) as error:failures[definition['id']]={'status':'INCOMPLETE','reason':str(error)}
            b={'protocol_checksum':p['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],'seed':pa['seed'],'parent_sha256':pa['sha256'],
                'nodes':nodes,'failures':failures,'audits':expected_audits(p,m,pa,ix)}
            joblib.dump(b,cell/'model.joblib',compress=3);write_gzip(cell/'fit_audits.json.gz',b['audits'])
            a=dict(artifact(cell/'model.joblib'),fold_id=m['fold_id'],seed=pa['seed'],parent_artifact=pa,fit_audits=artifact(cell/'fit_audits.json.gz'),
                seconds=time.perf_counter()-t,process_peak_memory_bytes=peak_memory_bytes())
            load_model(a,p,m,pa);save_json(cp,seal({'artifact':a,'protocol_checksum':p['protocol_checksum']},'checkpoint_checksum'));arts.append(a)
            logger.info('封存 {}，成功{}表示法，缺失{}',cell.name,len(nodes),failures)
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('formal source changed')
    return save_immutable(output/'locked_study.json',seal({'protocol_checksum':p['protocol_checksum'],'artifacts':arts,'source_before':before,
        'source_after':after,'selection_policy':'none','selection_sample_ids':[],'environment':p['environment'],
        'code_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()},'locked_checksum'),'locked_checksum')


def validate_lock(p,lock):
    verify_seal(lock,'locked_checksum')
    expected={(f['fold_id'],seed) for f in p['folds'] for seed in p['seeds']}
    if (lock['protocol_checksum']!=p['protocol_checksum'] or lock['environment']!=p['environment'] or lock['selection_policy']!='none' or
        lock['selection_sample_ids'] or len(lock['artifacts'])!=9 or {(a['fold_id'],a['seed']) for a in lock['artifacts']}!=expected):raise ValueError('locked inventory/policy')


def source_verify(pools,p,lock,output):
    pp,ms,old,audits=check(p);validate_lock(p,lock);before=verify_sources(pools.root,ms[0]);cells=[];start=time.perf_counter()
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start);m=next(x for x in ms if x['fold_id']==a['fold_id']);pa=next(x for x in old['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']))
            b=load_model(a,p,m,pa);parent=load_bundle(pa,old,pp,ms,audits);tr=records_for(m,'train');cal=records_for(m,'calibration');y,ix=indices(tr,p,a['seed'])
            cy=np.array([p['known_labels'].index(r['label']) for r in cal]);rep=parent['references']['harmonic69/mixed']['transformer'];H=rep.transform(pools.load(tr));C=rep.transform(pools.load(cal))
            verified={d['id']:verify_numeric(b['nodes'][d['id']],d,H,C,y,cy,ix,p) for d in REPRESENTATIONS if d['id'] in b['nodes']}
            cells.append({'fold_id':a['fold_id'],'seed':a['seed'],'model_sha256':a['sha256'],'verified':verified,'failures':b['failures']})
            logger.info('來源重建 {} seed{}',a['fold_id'],a['seed'])
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('formal source changed')
    result=seal({'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'cells':cells,
        'source_before':before,'source_after':after,'test_numeric_reads':0,'fresh_final_test':False,'status':'VERIFIED_AVAILABLE_NUMERIC_SOURCES'},'source_verification_checksum')
    save_json(output/'source_verified.json',result);return result


def infer(parent,b,p,X):
    H=parent['references']['harmonic69/mixed']['transformer'].transform(X)
    values={};cache={};baseline=parent['references']['base75/mixed'];base_score=baseline['detectors']['mahalanobis'].score_samples(baseline['transformer'].transform(X))
    for d in p['arms']:
        if d['representation'] not in b['nodes']:continue
        node=b['nodes'][d['representation']];key=d['representation']
        if key not in cache:cache[key]={'Z':node['projection'].transform(H)}
        z=cache[key]['Z'];ck='classifier/'+d['classifier'];dk='detector/'+d['detector']
        if ck not in cache[key]:cache[key][ck]=node['classifiers'][d['classifier']].predict(z)
        if dk not in cache[key]:cache[key][dk]=base_score if d['detector']=='C02/M' else node['detectors'][d['detector']].score_samples(z)
        values[d['id']]=(cache[key][ck],cache[key][dk],1.)
    return values


def evaluate(pools,p,lock,source,output,evaluation=None):
    pp,ms,old,audits=check(p);validate_lock(p,lock);verify_seal(source,'source_verification_checksum')
    if source['protocol_checksum']!=p['protocol_checksum'] or source['locked_checksum']!=lock['locked_checksum'] or source['status']!='VERIFIED_AVAILABLE_NUMERIC_SOURCES':raise ValueError('source verification required')
    if {(c['fold_id'],c['seed'],c['model_sha256']) for c in source['cells']}!={(a['fold_id'],a['seed'],a['sha256']) for a in lock['artifacts']}:raise ValueError('source coverage')
    verify=evaluation is not None
    if verify:
        verify_seal(evaluation,'evaluation_checksum')
        if evaluation['protocol_checksum']!=p['protocol_checksum'] or evaluation['locked_checksum']!=lock['locked_checksum'] or evaluation['source_verification_checksum']!=source['source_verification_checksum']:raise ValueError('evaluation source binding')
    before=verify_sources(pools.root,ms[0]);start=time.perf_counter();runs=[];failed=[];unique=set();count=0
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start);m=next(x for x in ms if x['fold_id']==a['fold_id']);pa=next(x for x in old['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']))
            b=load_model(a,p,m,pa);parent=load_bundle(pa,old,pp,ms,audits);rr=records_for(m,'test');X=pools.load(rr);t=time.perf_counter();values=infer(parent,b,p,X);seconds=time.perf_counter()-t
            altered=pools.load([dict(r,label='MUTATED_TRUTH') for r in rr])
            if not np.array_equal(X,altered):raise ValueError('truth entered features')
            if verify:
                second=infer(parent,b,p,altered)
                if any(not np.array_equal(values[k][j],second[k][j]) for k in values for j in [0,1]):raise ValueError('truth entered inference')
            for d in p['arms']:
                rid=d['id']+'_'+a['fold_id']+'_seed'+str(a['seed']);cp=output/(rid+'.checkpoint.json')
                if d['id'] not in values:
                    failed.append({'run_id':rid,'arm_id':d['id'],'fold_id':a['fold_id'],'seed':a['seed'],'status':'INCOMPLETE','reason':b['failures'][d['representation']]['reason']});continue
                pred,score,threshold=values[d['id']]
                if verify or cp.exists():
                    r=next(r for r in evaluation['runs'] if r['run_id']==rid) if verify else read(cp);verify_seal(r,'checkpoint_checksum');rows=predictions(r);check_rows(rows,r,m,p,lock)
                    if r['model_artifact']!=a or not np.array_equal(pred,[p['known_labels'].index(x['predicted_known_class']) for x in rows]) or not np.array_equal(score,[x['openset_score'] for x in rows]) or any(x['threshold']!=threshold for x in rows):raise ValueError('replay prediction mismatch')
                else:
                    rows=make_rows(rr,pred,score,threshold,p['known_labels'],d['id'],a['sha256'],p['protocol_checksum'],lock['locked_checksum'])
                    for row in rows:row.update(seed=a['seed'],split_sha=m['manifest_checksum'],final_decision=decision(row['predicted_known_class'],row['openset_score'],threshold))
                    path=output/(rid+'.jsonl.gz');path.write_bytes(gzip.compress('\n'.join(json.dumps(x,sort_keys=True,allow_nan=False) for x in rows).encode(),compresslevel=3,mtime=0))
                    r={'run_id':rid,'arm_id':d['id'],'fold_id':m['fold_id'],'seed':a['seed'],'motor_roles':m['motor_roles'],'samples':len(rows),
                        'model_artifact':a,'prediction_artifact':artifact(path),'threshold':threshold,'test_ids_checksum':digest(m['sample_ids']['test']),
                        'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'status':'completed',
                        'shared_bundle_inference_seconds':seconds,'process_peak_memory_bytes':peak_memory_bytes()}
                    r.update(summarized(rows,p));check_rows(rows,r,m,p,lock);r=seal(r,'checkpoint_checksum');save_json(cp,r)
                runs.append(r);count+=len(rows);unique.update(x['sample_id'] for x in rows)
            logger.info('配對 {} seed{}，本cell{}方法',a['fold_id'],a['seed'],len(values))
    after=verify_sources(pools.root,ms[0]);inventory=[r['run_id'] for r in runs+failed]
    if before!=after or len(inventory)!=144 or len(set(inventory))!=144:raise ValueError('source/inventory mismatch')
    if verify and failed!=evaluation['failed_runs']:raise ValueError('failure inventory changed')
    key='verification_checksum' if verify else 'evaluation_checksum';name='verified' if verify else 'evaluation'
    result=seal({'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'source_verification_checksum':source['source_verification_checksum'],
        'runs':runs,'failed_runs':failed,'planned_runs':144,'completed_runs':len(runs),'prediction_records':count,'unique_samples':len(unique),
        'source_before':before,'source_after':after,'seconds':time.perf_counter()-start,'fresh_final_test':False,'scope':p['scope']},key)
    result=save_immutable(output/(name+'.json'),result,key);write_gzip(output/(name+'.json.gz'),result);return result


def report(p,e,v,baseline,previous,output):
    check(p)
    for x,key in [(e,'evaluation_checksum'),(v,'verification_checksum'),(baseline,'metrics_checksum'),(previous,'evaluation_checksum')]:verify_seal(x,key)
    if (e['protocol_checksum']!=p['protocol_checksum'] or v['protocol_checksum']!=p['protocol_checksum'] or e['locked_checksum']!=v['locked_checksum'] or
        e['completed_runs']!=v['completed_runs'] or e['prediction_records']!=v['prediction_records'] or baseline['protocol_checksum']!=p['parent_protocol_checksum']):raise ValueError('report source binding')
    controls={c:[r for r in baseline['runs'] if r['arm_id']==c and r['score_id']=='mahalanobis'] for c in ['C02','C17','C24']};controls['D01']=[r for r in previous['runs'] if r['arm_id']=='D01']
    groups={**controls,**{d['id']:[r for r in e['runs'] if r['arm_id']==d['id']] for d in ARMS}};tables={};gates={};paired=[]
    for name,rr in groups.items():
        if len(rr)!=9:
            tables[name]={'status':'INCOMPLETE','completed_runs':len(rr),'failures':[r for r in e['failed_runs'] if r['arm_id']==name]};continue
        rows=[];derived=[]
        for r in rr:
            x=predictions(r);re=summarized(x,p)
            if re['metrics']!=r['metrics'] or re['rpm_metrics']!=r['rpm_metrics']:raise ValueError('metrics mismatch')
            derived.append(dict(r,configuration_metrics=re['configuration_metrics']))
            if r['seed']==0:rows+=x
        if len(rows)!=28910 or len({r['sample_id'] for r in rows})!=28910:raise ValueError('unique samples')
        tables[name]=summarize(derived,rows,p)
        def final_fault(x):
            truth=['unknown' if r['true_label'] in p['unknown_labels'] else r['true_label'] for r in x]
            final=[decision(r['predicted_known_class'],r['openset_score'],r['threshold']) for r in x]
            return classification(truth,final,p['known_labels']+['unknown'],p['known_labels'][1:])
        tables[name]['final_fault_all_samples']=final_fault(rows)
        tables[name]['final_fault_all_samples_per_motor_seed']=[{'motor':r['motor_roles']['test'],'seed':r['seed'],'classification':final_fault(predictions(r))} for r in rr]
        tables[name]['conditional_fault_f1_scope']='known_fault_classification 僅 true known faulty；完整分母另列'
        if name not in controls:gates[name]=assess(derived,controls,CONTRACT)
    comparisons=[(d['id'],c) for d in ARMS for c in controls]+[(ARMS[i]['id'],ARMS[i-8]['id']) for i in range(8,16)]+[(ARMS[i]['id'],ARMS[i-4]['id']) for i in [4,5,6,7,12,13,14,15]]
    for new,old in comparisons:
        for r in groups[new]:
            prior=next((x for x in groups[old] if (x['fold_id'],x['seed'])==(r['fold_id'],r['seed'])),None)
            if prior is None:continue
            x=predictions(r);y=predictions(prior)
            if [(a['sample_id'],a['true_label'],a['source_sha256']) for a in x]!=[(a['sample_id'],a['true_label'],a['source_sha256']) for a in y]:raise ValueError('paired IDs/truth/source')
            paired.append({'method':new,'control':old,'fold_id':r['fold_id'],'seed':r['seed'],'samples':len(x),
                'classification_flips':sum(a['predicted_known_class']!=b['predicted_known_class'] for a,b in zip(x,y)),
                'fault_accuracy_delta_pp':100*(r['metrics']['known_fault_classification']['accuracy']-prior['metrics']['known_fault_classification']['accuracy'])})
    result=seal({'protocol_checksum':p['protocol_checksum'],'evaluation_checksum':e['evaluation_checksum'],'verification_checksum':v['verification_checksum'],
        'methods':tables,'reliability':gates,'paired_differences':paired,'completed_runs':e['completed_runs'],'failed_runs':e['failed_runs'],
        'prediction_records':e['prediction_records'],'unique_samples':e['unique_samples'],'subsets_tested':1,'fresh_final_test':False,
        'production_replacement':False,'conclusion':'固定方法探索性比較，無global winner；採集來源UNKNOWN，獨立final guard仍INCOMPLETE'},'report_checksum')
    save_json(output/'summary.json',result);write_gzip(output/'summary.json.gz',result);return result


def run(pools,*,action,p,output,lock=None,source_verification=None,evaluation=None,verification=None,baseline=None,previous=None):
    if action=='fit':return fit(pools,p,output)
    if action=='source-verify':return source_verify(pools,p,lock,output)
    if action in ['evaluate','verify']:return evaluate(pools,p,lock,source_verification,output,evaluation if action=='verify' else None)
    if action=='report':return report(p,evaluation,verification,baseline,previous,output)
    raise ValueError('action')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['lock','fit','source-verify','evaluate','verify','report','smoke','backup'])
    for key in ['parent-protocol','protocol','lock','source-verification','evaluation','verification','baseline','previous','data-root','resume']:parser.add_argument('--'+key,type=Path)
    parser.add_argument('--archive-root',type=Path,action='append')
    a=parser.parse_args();log,paths=setup_run('fault_type_local_fisher_'+a.action.replace('-','_'));out=paths.output_dir
    if a.action in ['fit','evaluate','verify']:
        out=ARTIFACT_BASE/paths.output_dir.parent.name/paths.output_dir.name;out.mkdir(parents=True,exist_ok=False)
    if a.resume:
        out=a.resume.resolve()
        if out.parent!=paths.output_dir.parent.resolve() or not out.is_dir():raise ValueError('explicit same-action resume root')
    if a.action=='backup':
        if not a.archive_root:parser.error('explicit archive-root required')
        roots=[r.resolve() for r in a.archive_root]
        for r in roots:
            if ARTIFACT_BASE.resolve() not in r.parents or not r.is_dir() or not any((r/name).is_file() for name in ['locked_study.json','evaluation.json','verified.json']):raise ValueError('only this experiment completed output roots')
        from experiments.fault_type_archive import run as archive
        from experiments.fault_type_fixed_delivery import run as verify_archive
        result=archive(roots,destination=ARTIFACT_BASE.parents[1]/'archives',paths=paths,log=log)
        verified=verify_archive(None,indices=[paths.output_dir/'archive_index.json']);save_json(paths.output_dir/'member_verification.json',verified)
    elif a.action=='lock':
        if not a.parent_protocol:parser.error('parent-protocol required')
        result=build(a.parent_protocol);check(result);save_json(out/'protocol.json',result)
    elif a.action=='smoke':
        rng=np.random.default_rng(42);X=rng.normal(size=(60,24));y=np.repeat(np.arange(3),20)
        result={'scope':'SYNTHETIC_ENGINEERING_ONLY','checksums':{kind:LocalProjection(kind,10).fit(X,y).checksum_ for kind in ['pca','lfda']}}
        save_json(out/'smoke.json',result)
    else:
        if not a.protocol:parser.error('protocol required')
        if a.action in ['fit','source-verify','evaluate','verify'] and not a.data_root:parser.error('data-root required')
        if a.action in ['source-verify','evaluate','verify'] and not a.lock:parser.error('lock required')
        if a.action in ['evaluate','verify'] and not a.source_verification:parser.error('source-verification required')
        if a.action in ['verify','report'] and not a.evaluation:parser.error('evaluation required')
        if a.action=='report' and any(getattr(a,k) is None for k in ['verification','baseline','previous']):parser.error('verification/baseline/previous required')
        kwargs={k:read(getattr(a,k)) if getattr(a,k) else None for k in ['lock','source_verification','evaluation','verification','baseline','previous']}
        result=run(FeatureStore(a.data_root) if a.data_root else None,action=a.action,p=read(a.protocol),output=out,**kwargs)
    if a.action in ['fit','evaluate','verify']:
        name={'fit':'locked_study.json','evaluate':'evaluation.json.gz','verify':'verified.json.gz'}[a.action]
        shutil.copyfile(out/name,paths.output_dir/name)
        save_json(paths.output_dir/'artifact_location.json',{'primary_output':str(out.resolve()),'compact_artifact':artifact(paths.output_dir/name),
            'primary_artifact':artifact(out/name),'contains_raw_data':False,'storage_note':'本批D槽衍生產物；標準output保留compact索引'})
    log.info('{} 完成，輸出 {}',a.action,out)
if __name__=='__main__':main()
