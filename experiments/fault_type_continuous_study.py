"""Checkpointed bounded matched research batch; no global method selector."""
import argparse
import gzip
import json
import shutil
import subprocess
import time
import warnings
from pathlib import Path
import joblib
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from threadpoolctl import threadpool_limits
from loguru import logger
from core.fault_type_continuous import GainRepresentation,DiagonalMargin,stratified_subset
from core.fault_type_mechanisms import peak_memory_bytes
from core.fault_type_accuracy_pipeline import records_for,check_cell
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal,verify_seal,digest
from core.fault_type_metrics_v2 import decision
from core.openset import create_openset_detector
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run
from experiments.fault_type_continuous_registry import check,read,ARMS,PARAMS
from experiments.fault_type_literature_study import load_bundle,artifact,write_gzip,read_gzip,make_rows
from experiments.fault_type_fixed_calibration import verify_sources
from experiments.fault_type_mechanism_study import summarized,check_rows,save_immutable


def budget(p,start,action):
    if time.perf_counter()-start>p['budget']['max_'+action+'_seconds']:raise RuntimeError(action+' wall budget exhausted; resume same checkpoint')
    if shutil.disk_usage('C:/').free<p['budget']['reserve_C_bytes']:raise RuntimeError('C reserve exhausted; preserve checkpoint')


def check_audit(a,m,p):
    train=records_for(m,'train');cal=records_for(m,'calibration');test=records_for(m,'test')
    ids=[r['sample_id'] for r in train];calids=[r['sample_id'] for r in cal]
    roles=m['motor_roles']
    if len(set(roles.values()))!=3 or any(set(ids)&set(x['sample_id'] for x in rr) for rr in [cal,test]) or set(calids)&set(r['sample_id'] for r in test):raise ValueError('motor/sample role overlap')
    if any(r['label'] not in p['known_labels'] for r in train+cal):raise ValueError('unknown fit/calibration')
    d=a['definition']
    if d not in p['arms'] or a['motor_roles']!=roles or a['protocol_checksum']!=p['protocol_checksum'] or a['manifest_checksum']!=m['manifest_checksum'] or a['dataset_fingerprint']!=p['dataset_fingerprint']:raise ValueError('audit source/config binding')
    y=[p['known_labels'].index(r['label']) for r in train]
    ix=stratified_subset(y,[r['rpm'] for r in train],a['seed'])
    subset=[ids[i] for i in ix]
    expected={'representation_fit_ids':ids,'scaler_fit_ids':ids,'detector_transform_fit_ids':ids,
        'classifier_fit_ids':subset if d['kind']=='neighbors' and d['subset_classifier'] else ids,
        'metric_fit_ids':subset if d.get('metric') else [],'reference_fit_ids':ids,
        'calibration_sample_ids':calids,'selection_sample_ids':[]}
    for k,v in expected.items():
        if a[k]!=v:raise ValueError(k+' contains wrong role, unknown or omitted source')
    if a['selection_policy']!='none' or a['shared_validation_calibration']:raise ValueError('selector/shared calibration')
    return True


def load_new(a,p,m,pa):
    path=Path(a['path']).resolve()
    if path.parent.name!=m['fold_id']+'_seed'+str(a['seed']) or path.name!='model.joblib' or _sha256_file(path)!=a['sha256']:raise ValueError('model root/SHA')
    b=joblib.load(path)
    if b['protocol_checksum']!=p['protocol_checksum'] or b['manifest_checksum']!=m['manifest_checksum'] or b['parent_sha256']!=pa['sha256'] or b['seed']!=a['seed']:raise ValueError('model source binding')
    if _sha256_file(Path(a['fit_audits']['path']))!=a['fit_audits']['sha256'] or read_gzip(a['fit_audits']['path'])!=b['audits']:raise ValueError('audit SHA')
    if [v['definition']['id'] for v in b['audits']]!=[d['id'] for d in p['arms'] if d['id'] not in b['arm_failures']]:raise ValueError('fit coverage')
    for au in b['audits']:check_audit(au,m,p)
    train=records_for(m,'train');y=[p['known_labels'].index(x['label']) for x in train]
    ix=stratified_subset(y,[x['rpm'] for x in train],a['seed'])
    if b['subset_indices']!=ix.tolist():raise ValueError('model subset altered')
    for d in p['arms']:
        if d['id'] in b['arm_failures']:continue
        if d['kind']=='neighbors':
            model=b['models'][d['id']]
            if any(model.get_params()[k]!=v for k,v in p['parameters']['neighbors'].items()):raise ValueError('classifier parameters changed')
            actual=model._y
            expected=np.asarray(y)[ix] if d['subset_classifier'] else np.asarray(y)
            if not np.array_equal(actual,expected):raise ValueError('classifier actual fit rows differ from audit')
            if d['metric'] and (not b['metric'].optimizer['success'] or b['metric'].optimizer!=next(au['optimizer'] for au in b['audits'] if au['definition']==d)):raise ValueError('metric optimizer audit')
        else:
            dim=str(d['dimension']);model=b['models']['gain'+dim];rep=b['representations'][dim]
            if model.solver!='lsqr' or model.shrinkage!='auto' or not np.array_equal(model.priors_,np.ones(len(p['known_labels']))/len(p['known_labels'])) or rep.dimension!=d['dimension']:raise ValueError('gain model config')
    return b


def fit(pools,*,p,output):
    pp,ms,oldlock,oldaudits=check(p);before=verify_sources(pools.root,ms[0]);start=time.perf_counter();artifacts=[]
    with threadpool_limits(limits=1):
        for pa in oldlock['artifacts']:
            budget(p,start,'fit');m=next(x for x in ms if x['fold_id']==pa['fold_id']);seed=pa['seed']
            cell=output/(m['fold_id']+'_seed'+str(seed));cell.mkdir(exist_ok=True);cp=cell/'checkpoint.json'
            if cp.exists():
                c=read(cp);verify_seal(c,'checkpoint_checksum')
                if c['protocol_checksum']!=p['protocol_checksum']:raise ValueError('resume protocol')
                load_new(c['artifact'],p,m,pa);artifacts.append(c['artifact']);continue
            t=time.perf_counter();parent=load_bundle(pa,oldlock,pp,ms,oldaudits)
            train=records_for(m,'train');cal=records_for(m,'calibration');counts=check_cell(train,cal,p['known_labels'])
            X=pools.load(train);C=pools.load(cal);y=np.array([p['known_labels'].index(v['label']) for v in train]);cy=np.array([p['known_labels'].index(v['label']) for v in cal])
            h=parent['references']['harmonic69/mixed']['transformer'].transform(X)
            ix=stratified_subset(y,[v['rpm'] for v in train],seed);ids=[v['sample_id'] for v in train];calids=[v['sample_id'] for v in cal]
            b={'protocol_checksum':p['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],'seed':seed,'parent_sha256':pa['sha256'],
                'models':{},'representations':{},'detectors':{},'audits':[],'subset_indices':ix.tolist(),'arm_failures':{}}
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                try:metric=DiagonalMargin().fit(h[ix],y[ix],seconds=p['parameters']['metric']['max_seconds']);b['metric']=metric
                except RuntimeError as err:
                    b['metric']=None;b['arm_failures']={d['id']:str(err) for d in p['arms'] if d.get('metric')}
                for d in p['arms']:
                    if d['id'] in b['arm_failures']:continue
                    if d['kind']=='neighbors':
                        z=metric.transform(h) if d['metric'] else h
                        jj=ix if d['subset_classifier'] else np.arange(len(X))
                        b['models'][d['id']]=KNeighborsClassifier(**p['parameters']['neighbors']).fit(z[jj],y[jj])
                    else:
                        dim=str(d['dimension'])
                        if dim not in b['representations']:
                            rep=GainRepresentation(d['dimension']).fit(X);z=rep.transform(X);cz=rep.transform(C)
                            b['representations'][dim]=rep
                            b['models']['gain'+dim]=LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto',priors=np.ones(len(p['known_labels']))/len(p['known_labels'])).fit(z,y)
                            b['detectors'][dim]=create_openset_detector('mahalanobis',**p['factory_parameters']).fit(z,y,cz,cy)
                    au={'definition':d,'seed':seed,'fold_id':m['fold_id'],'motor_roles':m['motor_roles'],'protocol_checksum':p['protocol_checksum'],
                        'manifest_checksum':m['manifest_checksum'],'dataset_fingerprint':p['dataset_fingerprint'],'parent_sha256':pa['sha256'],
                        'representation_fit_ids':ids,'scaler_fit_ids':ids,'detector_transform_fit_ids':ids,'reference_fit_ids':ids,
                        'classifier_fit_ids':[ids[i] for i in ix] if d['kind']=='neighbors' and d['subset_classifier'] else ids,
                        'metric_fit_ids':[ids[i] for i in ix] if d.get('metric') else [],'calibration_sample_ids':calids,
                        'selection_sample_ids':[],'selection_policy':'none','shared_validation_calibration':False,'counts':counts,
                        'optimizer':metric.optimizer if d.get('metric') else None,'transform_checksum':parent['references']['harmonic69/mixed']['transformer'].transform_checksum if d['kind']=='neighbors' else b['representations'][str(d['dimension'])].checksum,
                        'parent_reuse':'C02/M reference/cal; harmonic69 train representation for Q01-04','fit_semantics':'classifier subset explicit; detector uses ALL train, never calibration as reference'}
                    check_audit(au,m,p);b['audits'].append(au)
            b['warnings']=[{'category':w.category.__name__,'message':str(w.message)} for w in caught]
            joblib.dump(b,cell/'model.joblib',compress=3);write_gzip(cell/'fit_audits.json.gz',b['audits'])
            a=dict(artifact(cell/'model.joblib'),fold_id=m['fold_id'],seed=seed,parent_artifact=pa,fit_audits=artifact(cell/'fit_audits.json.gz'),
                seconds=time.perf_counter()-t,arm_failures=b['arm_failures'],optimizer=metric.optimizer if b['metric'] is not None else None,
                process_peak_memory_bytes=peak_memory_bytes(),warnings=b['warnings'])
            load_new(a,p,m,pa);save_json(cp,seal({'protocol_checksum':p['protocol_checksum'],'artifact':a},'checkpoint_checksum'));artifacts.append(a)
            logger.info('fit {} {:.1f}s incomplete={}',cell.name,a['seconds'],a['arm_failures'])
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('source changed')
    result=seal({'protocol_checksum':p['protocol_checksum'],'environment':p['environment'],'artifacts':artifacts,'source_before':before,'source_after':after,
        'selection_policy':'none','selection_sample_ids':[],'code_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()},'locked_checksum')
    return save_immutable(output/'locked_study.json',result,'locked_checksum')


def infer(parent,new,p,X):
    # No label, path, T-code or motor argument in numeric inference.
    refs=parent['references'];h=refs['harmonic69/mixed']['transformer'].transform(X)
    base=refs['base75/mixed']['detectors']['mahalanobis'].score_samples(refs['base75/mixed']['transformer'].transform(X))
    result={};gain={};hg=new['metric'].transform(h) if new['metric'] is not None else None
    for d in p['arms']:
        if d['id'] in new['arm_failures']:continue
        if d['kind']=='neighbors':pred=new['models'][d['id']].predict(hg if d['metric'] else h);score=base
        else:
            dim=str(d['dimension'])
            if dim not in gain:
                z=new['representations'][dim].transform(X)
                gain[dim]=(new['models']['gain'+dim].predict(z),new['detectors'][dim].score_samples(z))
            pred,own=gain[dim];score=base if d['detector']=='C02/M' else own
        result[d['id']]=(pred,score,1.)
    return result


def evaluate(pools,*,p,lock,output,evaluation=None):
    pp,ms,oldlock,oldaudits=check(p);verify_seal(lock,'locked_checksum');verify=evaluation is not None
    if lock['protocol_checksum']!=p['protocol_checksum'] or lock['environment']!=p['environment'] or lock['selection_sample_ids'] or len(lock['artifacts'])!=9:raise ValueError('lock binding')
    if verify:
        verify_seal(evaluation,'evaluation_checksum')
        if evaluation['protocol_checksum']!=p['protocol_checksum'] or evaluation['locked_checksum']!=lock['locked_checksum']:raise ValueError('evaluation binding')
    start=time.perf_counter();before=verify_sources(pools.root,ms[0]);runs=[];unique=set();failures=[];records_count=0
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            budget(p,start,'verify' if verify else 'evaluate');m=next(x for x in ms if x['fold_id']==a['fold_id'])
            pa=next(x for x in oldlock['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']))
            if pa!=a['parent_artifact']:raise ValueError('parent replaced')
            parent=load_bundle(pa,oldlock,pp,ms,oldaudits);new=load_new(a,p,m,pa);records=records_for(m,'test');X=pools.load(records)
            t=time.perf_counter();scores=infer(parent,new,p,X);seconds=time.perf_counter()-t
            X2=pools.load([dict(x,label='MUTATED_TRUTH') for x in records])
            if not np.array_equal(X,X2):raise ValueError('feature truth dependence')
            if verify:
                alt=infer(parent,new,p,X2)
                if any(not np.array_equal(scores[k][j],alt[k][j]) for k in scores for j in [0,1]):raise ValueError('truth-dependent inference')
            for d in p['arms']:
                rid=d['id']+'_'+a['fold_id']+'_seed'+str(a['seed']);cp=output/(rid+'.checkpoint.json')
                if d['id'] in new['arm_failures']:
                    failures.append({'run_id':rid,'status':'INCOMPLETE','reason':new['arm_failures'][d['id']]});continue
                pred,score,threshold=scores[d['id']]
                if verify or cp.exists():
                    rr=next(x for x in evaluation['runs'] if x['run_id']==rid) if verify else read(cp)
                    if not verify:verify_seal(rr,'checkpoint_checksum')
                    if _sha256_file(Path(rr['prediction_artifact']['path']))!=rr['prediction_artifact']['sha256']:raise ValueError('prediction SHA')
                    rows=[json.loads(line) for line in gzip.decompress(Path(rr['prediction_artifact']['path']).read_bytes()).splitlines()]
                    check_rows(rows,rr,m,p,lock)
                    if not np.array_equal(pred,[p['known_labels'].index(x['predicted_known_class']) for x in rows]) or not np.array_equal(score,[x['openset_score'] for x in rows]):raise ValueError('reinference not exact')
                else:
                    rows=make_rows(records,pred,score,threshold,p['known_labels'],d['id'],a['sha256'],p['protocol_checksum'],lock['locked_checksum'])
                    for row in rows:row.update(seed=a['seed'],split_sha=m['manifest_checksum'],final_decision=decision(row['predicted_known_class'],row['openset_score'],threshold))
                    path=output/(rid+'.jsonl.gz');path.write_bytes(gzip.compress('\n'.join(json.dumps(x,sort_keys=True,allow_nan=False) for x in rows).encode(),compresslevel=3,mtime=0))
                    rr={'run_id':rid,'arm_id':d['id'],'fold_id':m['fold_id'],'seed':a['seed'],'motor_roles':m['motor_roles'],'samples':len(rows),
                        'test_ids_checksum':digest(m['sample_ids']['test']),'prediction_artifact':artifact(path),'model_artifact':a,'threshold':threshold,
                        'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'status':'completed',
                        'shared_bundle_inference_seconds':seconds,'runtime_note':'eight arms share transforms; not eight independent times',
                        'process_peak_memory_bytes':peak_memory_bytes()}
                    rr.update(summarized(rows,p));check_rows(rows,rr,m,p,lock);rr=seal(rr,'checkpoint_checksum');save_json(cp,rr)
                runs.append({'run_id':rid,'rows':len(rows),'reinference_exact':True,'truth_mutation_invariant':True} if verify else rr)
                unique.update(x['sample_id'] for x in rows);records_count+=len(rows)
            logger.info('{} fold={} seed={} arms={} incomplete={}', 'verify' if verify else 'evaluate',a['fold_id'],a['seed'],len(scores),len(new['arm_failures']))
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('formal changed')
    if len(runs)+len(failures)!=p['budget']['planned_runs'] or len({x['run_id'] for x in runs+failures})!=72:raise ValueError('matrix coverage')
    result=seal({'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'runs':runs,'failed_runs':failures,
        'planned_runs':72,'completed_runs':len(runs),'prediction_records':records_count,'unique_samples':len(unique),'source_before':before,'source_after':after,
        'seconds':time.perf_counter()-start,'scope':p['scope'],'fresh_final_test':False,'selection_policy':'none'},'verification_checksum' if verify else 'evaluation_checksum')
    key='verification_checksum' if verify else 'evaluation_checksum';name='verified' if verify else 'evaluation'
    result=save_immutable(output/(name+'.json'),result,key)
    compact=output/(name+'.json.gz')
    if compact.exists():
        if read_gzip(compact)!=result:raise ValueError('compact changed')
    else:write_gzip(compact,result)
    return result


def run(pools,*,action,p,output,lock=None,evaluation=None):
    if action=='fit':return fit(pools,p=p,output=output)
    if action in ['evaluate','verify']:return evaluate(pools,p=p,lock=lock,output=output,evaluation=evaluation if action=='verify' else None)
    raise ValueError('action')
def main():
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('action',choices=['fit','evaluate','verify']);q.add_argument('--protocol',type=Path,required=True)
    q.add_argument('--data-root',type=Path,required=True);q.add_argument('--lock',type=Path);q.add_argument('--evaluation',type=Path);q.add_argument('--resume',type=Path)
    a=q.parse_args();log,paths=setup_run('fault_type_continuous_'+a.action);out=paths.output_dir
    if a.resume:
        out=a.resume.resolve()
        if out.parent!=(Path('output')/('fault_type_continuous_'+a.action)).resolve() or not out.is_dir():raise ValueError('resume explicit action directory')
    if a.action!='fit' and (not a.lock or a.action=='verify' and not a.evaluation):q.error('lock/evaluation required')
    result=run(FeatureStore(a.data_root),action=a.action,p=read(a.protocol),output=out,lock=read(a.lock) if a.lock else None,evaluation=read(a.evaluation) if a.evaluation else None)
    log.info('{} completed={} output={}',a.action,len(result.get('runs',result.get('artifacts',[]))),out)
if __name__=='__main__':main()
