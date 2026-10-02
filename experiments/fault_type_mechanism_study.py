"""Checkpointed fit/evaluate/reinfer for nine fixed, exploratory mechanisms."""
from __future__ import annotations
import argparse
import gzip
import json
import subprocess
import time
import warnings
from pathlib import Path
import joblib
import numpy as np
from loguru import logger
from threadpoolctl import threadpool_limits
from core.fault_type_mechanisms import RPMPartialPooling,BlockGeometry,calibrate,peak_memory_bytes
from core.fault_type_metrics_v2 import metrics_v2,decision
from core.fault_type_accuracy_pipeline import records_for,check_cell
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal,verify_seal,digest
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_mechanism_registry import check,read
from experiments.fault_type_literature_study import load_bundle,artifact,write_gzip,read_gzip,audit_roles,make_rows
from experiments.fault_type_fixed_calibration import verify_sources


def check_audit(a,m,p):
    audit_roles(a,m,'mixed')
    train=records_for(m,'train');expected=[r['sample_id'] for r in train]
    for key in ['classifier_transform_fit_ids','detector_transform_fit_ids']:
        if a[key]!=expected:raise ValueError(key+' includes non-train or omits train')
    if a['background_fit_ids']!=(expected if a['definition']['kind']=='block' else []):raise ValueError('background fit IDs')
    if a['prototype_fit_ids']!=(expected if a['definition']['kind'] in ['block','partial_pool'] else []):raise ValueError('prototype fit IDs')
    if a['protocol_checksum']!=p['protocol_checksum'] or a['dataset_fingerprint']!=p['dataset_fingerprint'] or a['definition'] not in p['arms']:raise ValueError('audit definition/source binding')
    rpmids={rpm:[r['sample_id'] for r in train if r['rpm']==rpm] for rpm in p['rpms']}
    if a['classifier_rpm_fit_ids']!=(rpmids if a['definition']['classifier']=='C24' or a['definition']['kind']=='partial_pool' else {}):raise ValueError('RPM fit IDs')
    return True


def transforms(parent):
    return {key:ref['transformer'].transform_checksum for key,ref in parent['references'].items() if key in
        ['base75/mixed','harmonic69/mixed',*['base75/'+r for r in ['6000rpm','8000rpm','11000rpm']]]}


def load_new(a,p,m,parent_artifact,root):
    path=Path(a['path']).resolve()
    if path.parent!=Path(root).resolve() or _sha256_file(path)!=a['sha256']:raise ValueError('new model root/SHA')
    b=joblib.load(path)
    if b['protocol_checksum']!=p['protocol_checksum'] or b['manifest_checksum']!=m['manifest_checksum'] or b['parent_sha256']!=parent_artifact['sha256'] or b['seed']!=a['seed'] or b['fold_id']!=m['fold_id']:raise ValueError('new model bindings')
    for au in b['audits']:check_audit(au,m,p)
    if [x['definition'] for x in b['audits']]!=p['arms'] or len(b['audits'])!=9:raise ValueError('audit inventory')
    return b


def fit(pools,*,p,output):
    pp,ms,oldlock,oldaudits=check(p);before=verify_sources(pools.root,ms[0]);artifacts=[];failures=[]
    with threadpool_limits(limits=1):
        for pa in oldlock['artifacts']:
            m=next(m for m in ms if m['fold_id']==pa['fold_id']);cell=output/(m['fold_id']+'_seed'+str(pa['seed']));cell.mkdir(exist_ok=True)
            checkpoint=cell/'checkpoint.json'
            if checkpoint.exists():
                c=read(checkpoint);verify_seal(c,'checkpoint_checksum')
                if c['protocol_checksum']!=p['protocol_checksum']:raise ValueError('resume protocol changed')
                if c['status']=='completed':load_new(c['artifact'],p,m,pa,cell);artifacts.append(c['artifact'])
                else:failures.append(c)
                logger.info('resume sealed fit {}',cell.name);continue
            start=time.perf_counter()
            try:
                parent=load_bundle(pa,oldlock,pp,ms,oldaudits)
                train=records_for(m,'train');cal=records_for(m,'calibration');counts=check_cell(train,cal,p['known_labels'])
                X=pools.load(train);C=pools.load(cal);y=np.array([p['known_labels'].index(r['label']) for r in train]);rpms=[r['rpm'] for r in train]
                refs=parent['references'];Z=refs['base75/mixed']['transformer'].transform(X)
                H=refs['harmonic69/mixed']['transformer'].transform(X);CH=refs['harmonic69/mixed']['transformer'].transform(C)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    models={d['id']:RPMPartialPooling(d['beta'],p['rpms'],len(p['known_labels'])).fit(Z,y,rpms) for d in p['arms'] if d['kind']=='partial_pool'}
                    geometry=BlockGeometry(len(p['known_labels'])).fit(H,y)
                    thresholds={str(w):calibrate(geometry.score(CH,w)) for w in [0.,1.]}
                ids=[r['sample_id'] for r in train];calids=[r['sample_id'] for r in cal];audits=[]
                for d in p['arms']:
                    au={'arm_id':d['id'],'definition':d,'fold_id':m['fold_id'],'seed':pa['seed'],'motor_roles':m['motor_roles'],
                        'protocol_checksum':p['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],'dataset_fingerprint':p['dataset_fingerprint'],
                        'selection_sample_ids':[],'selection_policy':'none','shared_validation_calibration':False,
                        'calibration_sample_ids':calids,'metric_fit_ids':ids,'parent_sha256':pa['sha256'],
                        'parent_transform_checksums':transforms(parent),'classifier_parent':'C24' if d['classifier']=='C24' else 'C17' if d['classifier']=='C17' else None,
                        'detector_parent':'C02' if d['detector'].startswith('C02') else None,
                        'classifier_rpm_fit_ids':{rpm:[r['sample_id'] for r in train if r['rpm']==rpm] for rpm in p['rpms']} if d['classifier']=='C24' or d['kind']=='partial_pool' else {},
                        'counts':counts,'optimizer':'closed-form eigendecomposition/LW; no iterative optimizer',
                        'geometry_shrinkages':geometry.shrinkages if d['kind']=='block' else None,
                        'partial_pool_shrinkages':models[d['id']].shrinkages if d['kind']=='partial_pool' else None,
                        'calibration_threshold':thresholds[str(d['background_weight'])] if d['kind']=='block' else 1.}
                    for k in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids','classifier_transform_fit_ids','detector_transform_fit_ids']:au[k]=ids
                    au['background_fit_ids']=ids if d['kind']=='block' else []
                    au['prototype_fit_ids']=ids if d['kind'] in ['block','partial_pool'] else []
                    au['fit_semantics']='parent transform/classifier/detector IDs are REUSED; D has no new fit; P only new classifier; G only new geometry, G03 uses geometry classifier'
                    check_audit(au,m,p);audits.append(au)
                b={'protocol_checksum':p['protocol_checksum'],'manifest_checksum':m['manifest_checksum'],'fold_id':m['fold_id'],'seed':pa['seed'],
                    'parent_sha256':pa['sha256'],'models':models,'geometry':geometry,'thresholds':thresholds,'audits':audits,
                    'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught]}
                path=cell/'model.joblib';joblib.dump(b,path,compress=3)
                a=dict(artifact(path),fold_id=m['fold_id'],seed=pa['seed'],parent_artifact=pa,seconds=time.perf_counter()-start,
                    process_peak_memory_bytes=peak_memory_bytes(),memory_definition='cumulative process peak including parent load',warnings=b['warnings'])
                write_gzip(cell/'fit_audits.json.gz',audits);a['fit_audits']=artifact(cell/'fit_audits.json.gz')
                load_new(a,p,m,pa,cell)
                c=seal({'status':'completed','protocol_checksum':p['protocol_checksum'],'artifact':a},'checkpoint_checksum');save_json(checkpoint,c);artifacts.append(a)
                logger.info('fit/sealed {} elapsed={:.1f}s',cell.name,a['seconds'])
            except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:
                c=seal({'status':'INCOMPLETE','fold_id':m['fold_id'],'seed':pa['seed'],'protocol_checksum':p['protocol_checksum'],'reason':str(e)},'checkpoint_checksum')
                save_json(checkpoint,c);failures.append(c);logger.error('fit failed {}: {}',cell.name,e)
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('formal changed')
    lock=seal({'protocol_checksum':p['protocol_checksum'],'environment':p['environment'],'source_before':before,'source_after':after,
        'artifacts':artifacts,'failures':failures,'selection_policy':'none','selection_sample_ids':[],
        'new_classifier_fits':len(artifacts)*3,'new_geometry_fits':len(artifacts),'parent_fits_reused':True,
        'code_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()},'locked_checksum')
    save_json(output/'locked_study.json',lock);return lock


def infer(parent,new,p,X,rpms):
    """NO sample records/truth argument. Routing uses only declared RPM."""
    rpms=np.asarray(rpms);refs=parent['references'];z=refs['base75/mixed']['transformer'].transform(X);h=refs['harmonic69/mixed']['transformer'].transform(X)
    c17=parent['models']['C17']['mixed']['classifier'].predict(h);c24=np.empty(len(X),int)
    for rpm in p['rpms']:
        ix=np.flatnonzero(rpms==rpm)
        if len(ix):
            node=parent['models']['C24'][rpm];zz=refs[node['reference_key']]['transformer'].transform(X[ix]);c24[ix]=node['classifier'].predict(zz)
    if not set(rpms)<=set(p['rpms']):raise ValueError('unknown RPM')
    factory={k:d.score_samples(z) for k,d in refs['base75/mixed']['detectors'].items()}
    result={}
    for d in p['arms']:
        if d['kind']=='partial_pool':pred=new['models'][d['id']].predict(z,rpms)
        elif d['classifier']=='block nearest':pred=new['geometry'].predict(h)
        else:pred=c17 if d['classifier']=='C17' else c24
        if d['kind']=='block':score=new['geometry'].score(h,d['background_weight']);threshold=new['thresholds'][str(d['background_weight'])]
        else:score=factory['knn' if d['detector'].endswith('/K') else 'mahalanobis'];threshold=1.
        result[d['id']]=(pred,score,threshold)
    return result


def summarized(rows,p):
    return {'metrics':metrics_v2(rows,p['known_labels'],p['unknown_labels']),
        'rpm_metrics':[{'rpm':rpm,'metrics':metrics_v2([r for r in rows if r['rpm']==rpm],p['known_labels'],p['unknown_labels'])} for rpm in p['rpms']],
        'configuration_metrics':[{'label':label,'samples':len(rr),'classifier_recall':float(np.mean([r['predicted_known_class']==label for r in rr])) if label in p['known_labels'] and rr else None,
            'rejection_rate':float(np.mean([r['is_unknown'] for r in rr])) if rr else None} for label in p['known_labels']+p['unknown_labels'] for rr in [[r for r in rows if r['true_label']==label]]]}


def check_rows(rows,r,m,p,lock):
    if [x['sample_id'] for x in rows]!=m['sample_ids']['test'] or r['test_ids_checksum']!=digest(m['sample_ids']['test']):raise ValueError('paired test IDs/order')
    by={x['sample_id']:x for x in m['records']}
    for x in rows:
        source=by[x['sample_id']]
        if any(x[k]!=source[v] for k,v in [('motor_id','t_code'),('rpm','rpm'),('true_label','label'),('source_file','source_file'),('source_sha256','source_sha256')]):raise ValueError('provenance/truth mismatch')
        if x['method_id']!=r['arm_id'] or x['seed']!=r['seed'] or x['split_sha']!=m['manifest_checksum'] or x['model_sha256']!=r['model_artifact']['sha256'] or x['protocol_checksum']!=p['protocol_checksum'] or x['locked_checksum']!=lock['locked_checksum'] or x['historical_test_exposed'] is not True:raise ValueError('prediction binding')
        if x['threshold']!=r['threshold'] or x['final_decision']!=decision(x['predicted_known_class'],x['openset_score'],x['threshold']):raise ValueError('decision/threshold')
    if summarized(rows,p)!={k:r[k] for k in ['metrics','rpm_metrics','configuration_metrics']}:raise ValueError('metrics recompute')


def evaluate(pools,*,p,lock,output,verify=False,evaluation=None):
    pp,ms,oldlock,oldaudits=check(p);verify_seal(lock,'locked_checksum')
    if lock['protocol_checksum']!=p['protocol_checksum'] or lock['environment']!=p['environment'] or lock['selection_sample_ids'] or lock['selection_policy']!='none':raise ValueError('lock binding')
    if len(lock['artifacts'])+len(lock['failures'])!=9:raise ValueError('lock bundle count')
    if verify:
        verify_seal(evaluation,'evaluation_checksum')
        if evaluation['protocol_checksum']!=p['protocol_checksum'] or evaluation['locked_checksum']!=lock['locked_checksum']:raise ValueError('evaluation binding')
    before=verify_sources(pools.root,ms[0]);runs=[];failed=[];unique=set();verified=0;start=time.perf_counter()
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            m=next(m for m in ms if m['fold_id']==a['fold_id']);pa=next(x for x in oldlock['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']))
            if a['parent_artifact']!=pa:raise ValueError('parent replaced')
            parent=load_bundle(pa,oldlock,pp,ms,oldaudits);new=load_new(a,p,m,pa,Path(a['path']).parent)
            if new['audits'][0]['parent_transform_checksums']!=transforms(parent):raise ValueError('parent transforms changed')
            if _sha256_file(Path(a['fit_audits']['path']))!=a['fit_audits']['sha256'] or read_gzip(a['fit_audits']['path'])!=new['audits']:raise ValueError('fit audit file replaced')
            records=records_for(m,'test');X=pools.load(records);rpms=[r['rpm'] for r in records];t=time.perf_counter();inferred=infer(parent,new,p,X,rpms)
            # Controlled truth mutation: feature access + infer remain unchanged even if all labels change.
            mutated=[dict(r,label='MUTATED_NOT_A_FEATURE') for r in records]
            X2=pools.load(mutated)
            if not np.array_equal(X,X2):raise ValueError('truth affected numeric inputs')
            if verify:
                inferred2=infer(parent,new,p,X2,[r['rpm'] for r in mutated])
                if any(not np.array_equal(inferred[k][j],inferred2[k][j]) for k in inferred for j in [0,1]):raise ValueError('truth-dependent inference')
            shared_seconds=time.perf_counter()-t
            for d in p['arms']:
                method=d['id'];pred,score,threshold=inferred[method];rid=f"{method}_{a['fold_id']}_seed{a['seed']}"
                checkpoint=output/(rid+'.checkpoint.json');path=output/(rid+'.jsonl.gz')
                if verify:
                    r=next(x for x in evaluation['runs'] if x['run_id']==rid);preda=r['prediction_artifact']
                    if _sha256_file(Path(preda['path']))!=preda['sha256']:raise ValueError('prediction SHA')
                    rows=[json.loads(line) for line in gzip.decompress(Path(preda['path']).read_bytes()).splitlines()]
                    check_rows(rows,r,m,p,lock)
                    if not np.array_equal(pred,[p['known_labels'].index(x['predicted_known_class']) for x in rows]) or not np.array_equal(score,[x['openset_score'] for x in rows]) or any(x['threshold']!=threshold for x in rows):raise ValueError('reinference differs')
                    verified+=len(rows);unique.update(x['sample_id'] for x in rows)
                    runs.append({'run_id':rid,'rows':len(rows),'prediction_sha256':preda['sha256'],'reinference_exact':True,'truth_mutation_invariant':True});continue
                if checkpoint.exists():
                    r=read(checkpoint);verify_seal(r,'checkpoint_checksum')
                    if r['protocol_checksum']!=p['protocol_checksum'] or r['locked_checksum']!=lock['locked_checksum']:raise ValueError('resume version mismatch')
                    if _sha256_file(Path(r['prediction_artifact']['path']))!=r['prediction_artifact']['sha256']:raise ValueError('resume prediction SHA')
                    rows=[json.loads(line) for line in gzip.decompress(Path(r['prediction_artifact']['path']).read_bytes()).splitlines()];check_rows(rows,r,m,p,lock)
                else:
                    rows=make_rows(records,pred,score,threshold,p['known_labels'],method,a['sha256'],p['protocol_checksum'],lock['locked_checksum'])
                    for row in rows:
                        row.update(seed=a['seed'],split_sha=m['manifest_checksum'],final_decision=decision(row['predicted_known_class'],row['openset_score'],threshold))
                    path.write_bytes(gzip.compress('\n'.join(json.dumps(x,sort_keys=True,allow_nan=False) for x in rows).encode(),compresslevel=3,mtime=0))
                    r={'run_id':rid,'arm_id':method,'fold_id':m['fold_id'],'seed':a['seed'],'motor_roles':m['motor_roles'],'samples':len(rows),
                        'test_ids_checksum':digest(m['sample_ids']['test']),'prediction_artifact':artifact(path),'model_artifact':a,'threshold':threshold,
                        'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'status':'completed',
                        'shared_bundle_inference_seconds':shared_seconds,'runtime_note':'nine arms share transforms/parent inference; not nine independent timings',
                        'process_peak_memory_bytes':peak_memory_bytes()}
                    r.update(summarized(rows,p));check_rows(rows,r,m,p,lock);r=seal(r,'checkpoint_checksum');save_json(checkpoint,r)
                runs.append(r);unique.update(x['sample_id'] for x in rows)
            logger.info('{} fold={} seed={} methods=9', 'verified' if verify else 'evaluated',a['fold_id'],a['seed'])
    expected={(d['id'],m['fold_id'],s) for d in p['arms'] for m in ms for s in p['seeds']}
    if not verify:
        got={(r['arm_id'],r['fold_id'],r['seed']) for r in runs}
        if len(got)!=len(runs) or not got<=expected:raise ValueError('matrix duplicates/identity')
        failed=[{'arm_id':d,'fold_id':f,'seed':s,'status':'INCOMPLETE','fit_reasons':lock['failures']} for d,f,s in sorted(expected-got)]
    elif len(runs)!=evaluation['completed_runs']:raise ValueError('verify inventory')
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('source changed')
    result=seal({'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'runs':runs,'failed_runs':failed,
        'planned_runs':81,'completed_runs':len(runs),'prediction_records':verified if verify else sum(r['samples'] for r in runs),
        'unique_samples':len(unique),'source_before':before,'source_after':after,'seconds':time.perf_counter()-start,
        'scope':p['scope'],'fresh_final_test':False,'selection_policy':'none'},'verification_checksum' if verify else 'evaluation_checksum')
    name='verified' if verify else 'evaluation';save_json(output/(name+'.json'),result);write_gzip(output/(name+'.json.gz'),result);return result


def run(pools,*,action,p,output,lock=None,evaluation=None):
    if action=='fit':return fit(pools,p=p,output=output)
    if action in ['evaluate','verify']:return evaluate(pools,p=p,lock=lock,output=output,verify=action=='verify',evaluation=evaluation)
    raise ValueError('action')


def main():
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('action',choices=['fit','evaluate','verify']);q.add_argument('--protocol',type=Path,required=True)
    q.add_argument('--data-root',type=Path,required=True);q.add_argument('--lock',type=Path);q.add_argument('--evaluation',type=Path);q.add_argument('--resume',type=Path)
    a=q.parse_args();log,paths=setup_run('fault_type_mechanism_'+a.action)
    out=paths.output_dir
    if a.resume:
        candidate=a.resume.resolve();base=(Path('output')/('fault_type_mechanism_'+a.action)).resolve()
        if candidate.parent!=base or not candidate.is_dir():raise ValueError('resume must be explicit existing action run directory')
        out=candidate
    r=run(FeatureStore(a.data_root),action=a.action,p=read(a.protocol),output=out,lock=read(a.lock) if a.lock else None,evaluation=read(a.evaluation) if a.evaluation else None)
    log.info('{} completed={} output={}',a.action,len(r.get('runs',r.get('artifacts',[]))),out)


if __name__=='__main__':main()
