"""實驗21：有限表格自挑戰；來源與事前參數見exp21。

封存／逐筆重算改編本站exp20；未複製或執行原作者RSC程式。
"""
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
from core.fault_type_risk_extrapolation import RiskExtrapolationClassifier,RIDGE,OPTIMIZER
from core.fault_type_self_challenging import SelfChallengingClassifier,VARIANTS,TRAINING
from core.fault_type_axis_kernel import array_checksum
from experiments.fault_type_axis_kernel import factory_signature
from core.fault_type_literature import LiteratureRepresentation,NoveltyReference
from core.openset import create_openset_detector
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
from experiments import fault_type_discriminative_prototypes as G
from experiments.fault_type_context_prototypes import validate_policy
from experiments.fault_type_fixed_calibration import verify_sources
from experiments.fault_type_literature_study import artifact,write_gzip,read_gzip,load_bundle,make_rows
from experiments.fault_type_mechanism_study import summarized,check_rows,save_immutable
from experiments.fault_type_mechanism_report import predictions,summarize


KEYS=['dataset_fingerprint','known_labels','unknown_labels','rpms','folds','seeds','factory_parameters','exposure_ledger_checksum','manifest_checksums','reliability_contract']
REPRESENTATIONS=['base75','harmonic69']
MODELS=[dict(id=rep+'_'+variant,representation=rep,variant=variant) for rep in REPRESENTATIONS for variant in VARIANTS]
ARMS=[dict(id=f'M{i*3+j+1:02}',model=d['id'],detector=method) for i,d in enumerate(MODELS) for j,method in enumerate(['C02/M','C02/kNN','MSP'])]
PARAMETERS=dict(models=MODELS,training=TRAINING,warm_optimizer=OPTIMIZER,ridge=RIDGE,
    initialization='same known train re-fitted beta0 ERM',risk='equal RPM/class masked CE; last fixed iterate',
    training_rpms=['6000rpm','8000rpm','11000rpm'],
    scaler=dict(with_centering=True,with_scaling=True,quantile_range=[25.,75.],copy=True,unit_variance=False),
    calibration_quantile=.95,quantile_method='linear',MSP_definition=dict(kind='msp'),MSP_score='1-max softmax probability',strict_reject='score > threshold')
BUDGET=dict(planned_runs=216,seconds_per_action=1800,reserve_C_bytes=1000000000)
FILES=['core/fault_type_self_challenging.py','experiments/fault_type_self_challenging.py','docs/experiments/exp21_feature_self_challenging.md',
       'core/fault_type_risk_extrapolation.py','experiments/fault_type_risk_extrapolation.py']
ARTIFACT_BASE=Path('D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-04/feature_self_challenging_v1/workspace/output')


def read(path):
    path=Path(path)
    return read_gzip(path) if path.suffix=='.gz' else json.loads(path.read_text(encoding='utf-8'))


def normalized(value):
    return json.loads(json.dumps(value))


def build(parent_path):
    gp=read(parent_path)
    G.check(gp)
    p={k:gp[k] for k in KEYS}
    p.update(version='exp21_feature_self_challenging_v1',parent_protocol=artifact(parent_path),parent_protocol_checksum=gp['parent_protocol_checksum'],
        arms=ARMS,parameters=normalized(PARAMETERS),budget=BUDGET,selection_policy='none',selection_sample_ids=[],validation_sample_ids=[],
        shared_validation_calibration=False,fresh_final_test=False,scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED',
        environment={'python':platform.python_version(),'sklearn':sklearn.__version__},implementations=[artifact(Path(f)) for f in FILES],
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    return seal(p,'protocol_checksum')


def check(p):
    verify_seal(p,'protocol_checksum')
    validate_policy(p)
    if (p['version']!='exp21_feature_self_challenging_v1' or p['arms']!=ARMS or p['parameters']!=normalized(PARAMETERS) or
        p['budget']!=BUDGET or p['reliability_contract']!=CONTRACT):
        raise ValueError('fixed self challenging definitions changed')
    if p['environment']!={'python':platform.python_version(),'sklearn':sklearn.__version__}:
        raise ValueError('native environment required')
    if [a['path'] for a in p['implementations']]!=[str(Path(f).resolve()) for f in FILES]:
        raise ValueError('source inventory')
    for a in p['implementations']+[p['parent_protocol']]:
        if _sha256_file(Path(a['path']))!=a['sha256']:
            raise ValueError('self challenging source SHA changed')
    gp=read(p['parent_protocol']['path'])
    context=G.check(gp)
    if any(p[k]!=gp[k] for k in KEYS) or p['parent_protocol_checksum']!=gp['parent_protocol_checksum']:
        raise ValueError('parent risk binding')
    return context


def expected_audits(p,m,pa):
    tr,ca=records_for(m,'train'),records_for(m,'calibration')
    check_cell(tr,ca,p['known_labels'])
    ids,cis=[r['sample_id'] for r in tr],[r['sample_id'] for r in ca]
    if set(ids)&set(cis) or set(ids+cis)&set(m['sample_ids']['test']) or len(set(m['motor_roles'].values()))!=3:
        raise ValueError('challenge purpose overlap')
    rpms=PARAMETERS['training_rpms']
    if sorted(p.get('rpms',rpms))!=sorted(rpms) or any(r['rpm'] not in rpms for r in tr+ca):
        raise ValueError('fixed known RPM inventory')
    coverage=check_rpm_coverage(tr,p['known_labels'])
    return [dict(definition=d,protocol_checksum=p['protocol_checksum'],manifest_checksum=m['manifest_checksum'],
        dataset_fingerprint=p['dataset_fingerprint'],seed=pa['seed'],motor_roles=m['motor_roles'],parent_sha256=pa['sha256'],
        scaler_fit_ids=ids,representation_fit_ids=ids,classifier_fit_ids=ids,reference_fit_ids=ids,
        loss_environment_ids={rpm:[r['sample_id'] for r in tr if r['rpm']==rpm] for rpm in rpms},
        loss_environment_counts=coverage,calibration_sample_ids=cis,selection_sample_ids=[],selection_policy='none',
        shared_validation_calibration=False,classifier_parameters=PARAMETERS) for d in ARMS]

def check_rpm_coverage(rows,known):
    counts={rpm:{label:sum(r['rpm']==rpm and r['label']==label for r in rows) for label in known} for rpm in PARAMETERS['training_rpms']}
    if any(n==0 for labels in counts.values() for n in labels.values()):
        raise ValueError('INCOMPLETE known training RPM/class cell absent')
    return counts


def budget(start):
    if time.perf_counter()-start>BUDGET['seconds_per_action'] or shutil.disk_usage('C:/').free<BUDGET['reserve_C_bytes']:
        raise RuntimeError('challenge resource budget; preserve checkpoints')


def source_arrays(pools,p,m):
    tr,ca=records_for(m,'train'),records_for(m,'calibration')
    check_cell(tr,ca,p['known_labels']);check_rpm_coverage(tr,p['known_labels'])
    y=np.array([p['known_labels'].index(r['label']) for r in tr],dtype=int)
    cy=np.array([p['known_labels'].index(r['label']) for r in ca],dtype=int)
    env=np.array([r['rpm'] for r in tr])
    if sorted(np.unique(env).tolist())!=sorted(PARAMETERS['training_rpms']):
        raise ValueError('fixed train RPM environments')
    return pools.load(tr),pools.load(ca),y,cy,env

def representation_signature(rep):
    params=rep.scaler.get_params()
    return digest(dict(state=rep.checksum(),stored_state=rep.transform_checksum,scaler=normalized(params),name=rep.name,seed=rep.seed))

def novelty_signature(ref):
    return digest(dict(definition=ref.definition,seed=ref.seed,kind=ref.kind,parameter=ref.parameter,
        threshold=ref.threshold,calibration_count=ref.calibration_count,classifier=ref.classifier.checksum_,
        model_is_none=ref.model is None))

def node_signature(n):
    return digest(dict(model=n['model'].signature(),representation=representation_signature(n['representation']),
        warm=n['warm_start'].signature(),novelty=novelty_signature(n['rejector']),train=n['train_array_checksum'],cal=n['calibration_array_checksum'],
        cal_score=n['calibration_score_checksum'],environments=n['environment_checksum']))

def fit_nodes(X,C,y,env,seed):
    nodes={}
    for repname in REPRESENTATIONS:
        rep=LiteratureRepresentation(repname,seed).fit(X,y)
        Z,ZC=rep.transform(X),rep.transform(C)
        warm=None;warm_reason=None
        try:
            warm=RiskExtrapolationClassifier(0.,seed).fit(Z,y,env)
        except (ValueError,RuntimeError,np.linalg.LinAlgError) as exc:
            warm_reason=str(exc)
        for d in [x for x in MODELS if x['representation']==repname]:
            attempted=warm is not None
            try:
                if not attempted:raise RuntimeError('INCOMPLETE same-source ERM failed: '+warm_reason)
                model=SelfChallengingClassifier(d['variant'],seed).fit(Z,y,env,warm)
                ref=NoveltyReference(dict(kind='msp'),seed).fit(Z,y,model,None).calibrate(ZC)
                n=dict(model=model,warm_start=warm,representation=rep,rejector=ref,status='completed',optimizer_attempted=True,
                    train_array_checksum=array_checksum(Z),calibration_array_checksum=array_checksum(ZC),
                    calibration_score_checksum=array_checksum(ref.raw(ZC)),environment_checksum=digest(env.tolist()))
                n['node_checksum']=node_signature(n);nodes[d['id']]=n
            except (ValueError,RuntimeError,np.linalg.LinAlgError) as exc:
                nodes[d['id']]=dict(status='INCOMPLETE',reason=str(exc),model=None,rejector=None,warm_start=warm,
                    representation=rep,optimizer_attempted=attempted)
    return nodes


def load_model(a,p,m,pa,unused):
    for f in [a,a['fit_audits']]:
        if _sha256_file(Path(f['path']))!=f['sha256']:raise ValueError('challenge model/audit SHA')
    b=joblib.load(a['path'])
    if (b['protocol_checksum']!=p['protocol_checksum'] or b['manifest_checksum']!=m['manifest_checksum'] or
        b['seed']!=pa['seed'] or b['parent_sha256']!=pa['sha256'] or a['parent_artifact']!=pa or
        b['audits']!=expected_audits(p,m,pa) or read_gzip(a['fit_audits']['path'])!=b['audits']):
        raise ValueError('challenge model/source/audit binding')
    if set(b['nodes'])!={d['id'] for d in MODELS}:raise ValueError('challenge inventory')
    for d in MODELS:
        n=b['nodes'][d['id']]
        if n['status']=='completed':
            model=n['model'];model.validate();n['warm_start'].validate()
            if (model.variant!=d['variant'] or model.seed!=pa['seed'] or model.warm_start_checksum_!=n['warm_start'].checksum_ or n['representation'].name!=d['representation'] or
                n['representation'].seed!=pa['seed'] or n['node_checksum']!=node_signature(n) or
                normalized(n['representation'].scaler.get_params())!=PARAMETERS['scaler'] or
                n['rejector'].definition!=dict(kind='msp') or n['rejector'].classifier is not model):
                raise ValueError('challenge definition/state')
        elif n['status']!='INCOMPLETE' or n['model'] is not None or not n['reason']:
            raise ValueError('challenge failure state')
    return b


def validate_lock(p,lock):
    G.validate_lock(p,lock)


def fit(pools,p,output):
    ep,pp,ms,old,audits=check(p)
    before=verify_sources(pools.root,ms[0]); start=time.perf_counter(); arts=[]; fits=0
    with threadpool_limits(limits=1):
        for pa in old['artifacts']:
            budget(start)
            m=next(x for x in ms if x['fold_id']==pa['fold_id'])
            cell=output/(m['fold_id']+'_seed'+str(pa['seed'])); cell.mkdir(exist_ok=True); cp=cell/'checkpoint.json'
            if cp.exists():
                saved=read(cp); verify_seal(saved,'checkpoint_checksum')
                b=load_model(saved['artifact'],p,m,pa,ep); arts.append(saved['artifact'])
                fits+=sum(n['status']=='completed' for n in b['nodes'].values())
                continue
            t=time.perf_counter()
            load_bundle(pa,old,pp,ms,audits)
            X,C,y,cy,env=source_arrays(pools,p,m)
            b=dict(protocol_checksum=p['protocol_checksum'],manifest_checksum=m['manifest_checksum'],seed=pa['seed'],
                parent_sha256=pa['sha256'],nodes=fit_nodes(X,C,y,env,pa['seed']),audits=expected_audits(p,m,pa))
            joblib.dump(b,cell/'model.joblib',compress=3); write_gzip(cell/'fit_audits.json.gz',b['audits'])
            a=dict(artifact(cell/'model.joblib'),fold_id=m['fold_id'],seed=pa['seed'],parent_artifact=pa,
                fit_audits=artifact(cell/'fit_audits.json.gz'),seconds=time.perf_counter()-t,process_peak_memory_bytes=peak_memory_bytes())
            load_model(a,p,m,pa,ep);save_json(cp,seal(dict(artifact=a,protocol_checksum=p['protocol_checksum']),'checkpoint_checksum'))
            arts.append(a);fits+=sum(n['status']=='completed' for n in b['nodes'].values())
            logger.info('封存 {}，成功{}固定自挑戰分類器',cell.name,sum(n['status']=='completed' for n in b['nodes'].values()))
    after=verify_sources(pools.root,ms[0])
    if before!=after: raise ValueError('formal source changed')
    return save_immutable(output/'locked_study.json',seal(dict(protocol_checksum=p['protocol_checksum'],artifacts=arts,
        source_before=before,source_after=after,classifier_fits_completed=fits,classifier_fits_planned=72,classifier_fits_attempted=sum(sum(n['optimizer_attempted'] for n in joblib.load(a['path'])['nodes'].values()) for a in arts),
        warm_fits_planned=18,warm_fits_attempted=18,warm_fits_completed=sum(sum(joblib.load(a['path'])['nodes'][rep+'_unmasked']['warm_start'] is not None for rep in REPRESENTATIONS) for a in arts),
        selection_policy='none',selection_sample_ids=[],environment=p['environment'],
        code_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()),'locked_checksum'),'locked_checksum')


def verify_actual_sources(b,parent,X,C,y,cy,env,p,seed):
    verified={}
    rebuilt_nodes=fit_nodes(X,C,y,env,seed)
    for d in MODELS:
        n=b['nodes'][d['id']];expected=rebuilt_nodes[d['id']]
        if n['status']!=expected['status']:raise ValueError('actual challenge convergence state mismatch')
        if n['status']!='completed':
            if n['reason']!=expected['reason'] or n['optimizer_attempted']!=expected['optimizer_attempted']:
                raise ValueError('actual challenge failure mismatch')
            verified[d['id']]=dict(status=n['status'],reason=n['reason'],test_numeric_reads=0);continue
        if n['node_checksum']!=node_signature(n) or node_signature(n)!=node_signature(expected):
            raise ValueError('actual known challenge source/calibration mismatch')
        verified[d['id']]=dict(status='completed',node_checksum=n['node_checksum'],
            classifier_checksum=n['model'].checksum_,source=n['model'].source_,optimizer=n['model'].optimizer_,warm_checksum=n['warm_start'].checksum_,warm_optimizer=n['warm_start'].optimizer_,
            representation_checksum=representation_signature(n['representation']),
            calibration_score_checksum=n['calibration_score_checksum'],threshold=n['rejector'].threshold,
            test_numeric_reads=0)
    base=parent['references']['base75/mixed']
    rep=LiteratureRepresentation('base75',seed).fit(X,y)
    if representation_signature(rep)!=representation_signature(base['transformer']):
        raise ValueError('actual factory representation mismatch')
    B,BC=rep.transform(X),rep.transform(C)
    if not np.array_equal(B,base['transformer'].transform(X)) or not np.array_equal(BC,base['transformer'].transform(C)):
        raise ValueError('actual factory transform mismatch')
    for method in ['mahalanobis','knn']:
        expected_detector=create_openset_detector(method,**p['factory_parameters']).fit(B,y,BC,cy)
        if factory_signature(expected_detector,method)!=factory_signature(base['detectors'][method],method):
            raise ValueError('actual factory reference/calibration mismatch')
    return verified


def source_verify(pools,p,lock,output):
    ep,pp,ms,old,audits=check(p);validate_lock(p,lock)
    before=verify_sources(pools.root,ms[0]);cells=[];start=time.perf_counter()
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(start)
            m=next(x for x in ms if x['fold_id']==a['fold_id'])
            pa=next(x for x in old['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']))
            b=load_model(a,p,m,pa,ep); parent=load_bundle(pa,old,pp,ms,audits)
            X,C,y,cy,env=source_arrays(pools,p,m)
            verified=verify_actual_sources(b,parent,X,C,y,cy,env,p,a['seed'])
            cells.append(dict(fold_id=a['fold_id'],seed=a['seed'],model_sha256=a['sha256'],verified=verified))
            logger.info('重建known RPM／ERM／自挑戰／MSP及factory {} seed{}',a['fold_id'],a['seed'])
    after=verify_sources(pools.root,ms[0])
    if before!=after: raise ValueError('formal source changed')
    result=seal(dict(protocol_checksum=p['protocol_checksum'],locked_checksum=lock['locked_checksum'],cells=cells,
        source_before=before,source_after=after,test_numeric_reads=0,status='VERIFIED_AVAILABLE_NUMERIC_SOURCES',
        fresh_final_test=False),'source_verification_checksum')
    save_json(output/'source_verified.json',result);return result


def infer(parent,b,p,X):
    base=parent['references']['base75/mixed'];B=base['transformer'].transform(X)
    scores={method:base['detectors'][method].score_samples(B) for method in ['mahalanobis','knn']}
    cache={}
    for d in MODELS:
        n=b['nodes'][d['id']]
        if n['status']=='completed':
            if n['node_checksum']!=node_signature(n):raise ValueError('challenge node tampered')
            Z=n['representation'].transform(X);pred=n['model'].predict(Z)
            cache[d['id']]=(pred,n['rejector'].raw(Z),n['rejector'].threshold)
    return {d['id']:(cache[d['model']][0],
        cache[d['model']][1] if d['detector']=='MSP' else scores['mahalanobis' if d['detector']=='C02/M' else 'knn'],
        cache[d['model']][2] if d['detector']=='MSP' else 1.) for d in ARMS if d['model'] in cache}


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
                    failed.append({'run_id':rid,'arm_id':d['id'],'fold_id':a['fold_id'],'seed':a['seed'],'status':'INCOMPLETE','reason':b['nodes'][d['model']]['reason']});continue
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
    if (e['runs']!=v['runs'] or e['failed_runs']!=v['failed_runs'] or e['protocol_checksum']!=p['protocol_checksum'] or
        v['protocol_checksum']!=p['protocol_checksum'] or baseline['protocol_checksum']!=p['parent_protocol_checksum'] or
        e['locked_checksum']!=v['locked_checksum'] or e['source_verification_checksum']!=v['source_verification_checksum']):
        raise ValueError('report source binding')
    controls={c:[r for r in baseline['runs'] if r['arm_id']==c and r['score_id']=='mahalanobis'] for c in ['C02','C17','C24']};controls['D01']=[r for r in previous['runs'] if r['arm_id']=='D01']
    groups={**controls,**{d['id']:[r for r in e['runs'] if r['arm_id']==d['id']] for d in ARMS}};tables={};gates={};paired=[]
    for name,rr in groups.items():
        if len(rr)!=9:
            tables[name]={'status':'INCOMPLETE','completed_runs':len(rr),'failures':[r for r in e['failed_runs'] if r['arm_id']==name]};continue
        rows=[];derived=[];final_groups=[]
        for r in rr:
            x=predictions(r);re=summarized(x,p)
            if re['metrics']!=r['metrics'] or re['rpm_metrics']!=r['rpm_metrics']:raise ValueError('saved metrics mismatch')
            derived.append(dict(r,configuration_metrics=re['configuration_metrics']))
            truth=['unknown' if a['true_label'] in p['unknown_labels'] else a['true_label'] for a in x]
            final=[decision(a['predicted_known_class'],a['openset_score'],a['threshold']) for a in x]
            final_groups.append(dict(motor=r['motor_roles']['test'],seed=r['seed'],samples=len(x),
                classification=classification(truth,final,p['known_labels']+['unknown'],p['known_labels'][1:])))
            if r['seed']==0:rows+=x
        if len(rows)!=28910 or len({r['sample_id'] for r in rows})!=28910:raise ValueError('unique samples mismatch')
        tables[name]=summarize(derived,rows,p)
        truth=['unknown' if r['true_label'] in p['unknown_labels'] else r['true_label'] for r in rows];final=[decision(r['predicted_known_class'],r['openset_score'],r['threshold']) for r in rows]
        tables[name]['final_fault_all_samples']=classification(truth,final,p['known_labels']+['unknown'],p['known_labels'][1:])
        tables[name]['final_fault_all_samples_by_motor_seed']=final_groups
        tables[name]['conditional_fault_f1_scope']='僅true known faulty；完整分母另列'
        if name not in controls:gates[name]=assess(derived,controls,CONTRACT)
    comparisons=paired_methods(controls)
    for new,old in comparisons:
        for r in groups[new]:
            prior=next((x for x in groups[old] if (x['fold_id'],x['seed'])==(r['fold_id'],r['seed'])),None)
            if prior is None:continue
            x=predictions(r);y=predictions(prior)
            if [(a['sample_id'],a['true_label'],a['source_sha256']) for a in x]!=[(a['sample_id'],a['true_label'],a['source_sha256']) for a in y]:raise ValueError('paired IDs/truth/source')
            paired.append(dict(method=new,control=old,fold_id=r['fold_id'],seed=r['seed'],samples=len(x),fault_accuracy_delta_pp=100*(r['metrics']['known_fault_classification']['accuracy']-prior['metrics']['known_fault_classification']['accuracy'])))
    result=seal(dict(protocol_checksum=p['protocol_checksum'],evaluation_checksum=e['evaluation_checksum'],verification_checksum=v['verification_checksum'],methods=tables,reliability=gates,
        paired_differences=paired,completed_runs=e['completed_runs'],failed_runs=e['failed_runs'],prediction_records=e['prediction_records'],unique_samples=e['unique_samples'],
        subsets_tested=1,fresh_final_test=False,production_replacement=False,conclusion='固定表格自挑戰探索比較，無global winner；採集來源UNKNOWN、獨立final guard INCOMPLETE'),'report_checksum')
    save_json(output/'summary.json',result);write_gzip(output/'summary.json.gz',result);return result


def paired_methods(controls):
    return ([(d['id'],c) for d in ARMS for c in controls]+[
        (ARMS[rep*12+variant*3+j]['id'],ARMS[rep*12+j]['id'])
        for rep in range(2) for variant in [1,2,3] for j in range(3)]+[
        (ARMS[rep*12+variant*3+j]['id'],ARMS[rep*12+3+j]['id'])
        for rep in range(2) for variant in [2,3] for j in range(3)])


def run(pools,*,action,p,output,lock=None,source_verification=None,evaluation=None,verification=None,baseline=None,previous=None):
    if action=='fit':return fit(pools,p,output)
    if action=='source-verify':return source_verify(pools,p,lock,output)
    if action in ['evaluate','verify']:return evaluate(pools,p,lock,source_verification,output,evaluation if action=='verify' else None)
    if action=='report':return report(p,evaluation,verification,baseline,previous,output)
    raise ValueError('unsupported action')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['lock','fit','source-verify','evaluate','verify','report','smoke','backup'])
    for key in ['parent-protocol','protocol','lock','source-verification','evaluation','verification','baseline','previous','data-root','resume']:parser.add_argument('--'+key,type=Path)
    parser.add_argument('--archive-root',type=Path,action='append');a=parser.parse_args();log,paths=setup_run('fault_type_self_challenging_'+a.action.replace('-','_'));out=paths.output_dir
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
        rng=np.random.default_rng(42);X=rng.normal(size=(36,4));y=np.arange(36)%3;env=np.repeat([6000,8000,11000],12)
        erm=RiskExtrapolationClassifier(0.,42).fit(X,y,env)
        models=[SelfChallengingClassifier(variant,42).fit(X,y,env,erm) for variant in VARIANTS]
        result=dict(scope='SYNTHETIC_ENGINEERING_ONLY',models=[dict(variant=m.variant,state_checksum=m.checksum_,optimizer=m.optimizer_) for m in models])
        save_json(out/'smoke.json',result)
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
