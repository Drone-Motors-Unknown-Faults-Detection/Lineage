"""Registry-driven bounded study. No implicit defaults or global selection."""
from __future__ import annotations
import argparse
import gzip
import json
import platform
import time
import warnings
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from core.fault_type_accuracy_pipeline import StudyRepresentation, records_for, check_cell, validate_node_audit
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal, verify_seal, digest
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run
from core.openset import create_openset_detector
from experiments.fault_type_accuracy_registry import check_registry, classifier
from experiments.fault_type_accuracy_baseline import context
from experiments.fault_type_fixed_calibration import verify_sources, load_bound_model
from experiments.fault_type_fixed_calibration import raw_class_scores
from core.fault_type_accuracy_scores import PooledWithinLW, ResearchScore
from core.fault_type_accuracy import study_metrics

IMPLEMENTATIONS=['core/fault_type_accuracy.py','core/fault_type_accuracy_pipeline.py','core/fault_type_accuracy_scores.py',
                 'experiments/fault_type_accuracy_study.py']


def fit_classifier(arm, seed, registry, X, y):
    model=classifier(arm['classifier'],seed,len(registry['known_labels']))
    if model.get_params()!=registry['classifier_resolved'][arm['classifier']][str(seed)]: raise ValueError('classifier resolved parameters changed')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning)
        model.fit(X,y)
    if any(issubclass(w.category,ConvergenceWarning) for w in caught): raise RuntimeError('nonconvergent fixed classifier')
    return model


def fit_a(pools, *, registry, manifests, output, code_head):
    known=registry['known_labels']; artifacts=[]; audits=[]; failures=[]
    counts={'classifier_fits':0,'factory_reference_fits':0,'pooled_reference_fits':0,'representation_fits':0}
    with threadpool_limits(limits=1):
        for m in manifests:
            for seed in registry['seeds']:
                a1=None; a1_artifact=None
                for arm in registry['arms'][1:]:
                    start=time.perf_counter(); nodes={}
                    node_rpms=registry['expected_rpms'] if arm['rpm_strategy']=='separate' else [None]
                    for rpm in node_rpms:
                        key=rpm or 'mixed'
                        train=records_for(m,'train',rpm); cal=records_for(m,'calibration',rpm)
                        try: cell=check_cell(train,cal,known,registry['rules']['minimum_reference_per_class'])
                        except ValueError as e:
                            failures.append({'arm_id':arm['id'],'fold_id':m['fold_id'],'seed':seed,'rpm':key,'status':'INCOMPLETE','reason':str(e)})
                            continue
                        raw=pools.load(train); calibration=pools.load(cal)
                        y=np.array([known.index(r['label']) for r in train]); cy=np.array([known.index(r['label']) for r in cal])
                        reuse=arm.get('reference_arm')=='A1'
                        if reuse:
                            if a1 is None or key not in a1['nodes']: raise ValueError('A1 reference unavailable')
                            ref=a1['nodes'][key]; transformer=ref['transformer']; detectors=ref['detectors']
                        else:
                            try: transformer=StudyRepresentation(arm,registry['scaler_resolved']).fit(raw)
                            except ValueError as e:
                                failures.append({'arm_id':arm['id'],'fold_id':m['fold_id'],'seed':seed,'rpm':key,'status':'CONTRACT_MISMATCH','reason':str(e)});continue
                            X,C=transformer.transform(raw),transformer.transform(calibration)
                            detectors={method:create_openset_detector(method,**registry['detectors']).fit(X,y,C,cy) for method in ['mahalanobis','knn']}
                            counts['factory_reference_fits']+=2;counts['representation_fits']+=1
                        X=transformer.transform(raw)
                        clf=fit_classifier(arm,seed,registry,X,y);counts['classifier_fits']+=1
                        audit={'arm_id':arm['id'],'fold_id':m['fold_id'],'rpm':key,'seed':seed,'registry_checksum':registry['registry_checksum'],
                            'manifest_checksum':m['manifest_checksum'],'motor_roles':m['motor_roles'],'dataset_fingerprint':registry['dataset_fingerprint'],
                            'selection_policy':'none','selection_sample_ids':[],'shared_validation_calibration':False,
                            'calibration_sample_ids':[r['sample_id'] for r in cal],'class_counts':cell,
                            'train_label_counts_for_weight':np.bincount(y,minlength=len(known)).tolist(),
                            'classifier_parameters':clf.get_params(),'transform_checksum':transformer.transform_checksum,
                            'redundancy_check':transformer.redundancy_check,'reference_reused_from':a1_artifact if reuse else None,
                            'detector_calibration':{method:d.class_summaries() for method,d in detectors.items()},
                            'code_head':code_head}
                        for field in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids']:
                            audit[field]=[r['sample_id'] for r in train]
                        validate_node_audit(audit,m,rpm,arm,registry);audits.append(audit)
                        node={'classifier':clf,'audit_checksum':digest(audit),'fit_ids_checksum':digest(audit['classifier_fit_ids'])}
                        if not reuse: node.update(transformer=transformer,detectors=detectors)
                        nodes[key]=node
                    model={'arm_id':arm['id'],'fold_id':m['fold_id'],'seed':seed,'registry_checksum':registry['registry_checksum'],
                        'manifest_checksum':m['manifest_checksum'],'labels':known,'nodes':nodes,'reference_artifact':a1_artifact if arm.get('reference_arm') else None}
                    path=output/f"{arm['id']}_{m['fold_id']}_seed{seed}.joblib";joblib.dump(model,path,compress=3)
                    artifact={k:model[k] for k in ['arm_id','fold_id','seed','manifest_checksum']}
                    artifact.update(path=str(path.resolve()),sha256=_sha256_file(path),node_count=len(nodes),seconds=time.perf_counter()-start)
                    artifacts.append(artifact)
                    if arm['id']=='A1': a1=model;a1_artifact=artifact
    return artifacts,audits,failures,counts


def run(pools, *, registry, output, code_head):
    baseline=check_registry(registry)
    _,_,manifests,_=context(baseline['baseline_index'])
    before=verify_sources(pools.root,manifests[0])
    output.mkdir(parents=True,exist_ok=True)
    artifacts,audits,failures,counts=fit_a(pools,registry=registry,manifests=manifests,output=output,code_head=code_head)
    b_artifacts,b_audits,b_failures=fit_b(pools,registry=registry,manifests=manifests,a_artifacts=artifacts,output=output,code_head=code_head)
    counts['pooled_reference_fits']=sum(a['node_count'] for a in b_artifacts)
    counts['new_score_calibrations']=sum(a['node_count']*6 for a in b_artifacts)
    artifacts+=b_artifacts;audits+=b_audits;failures+=b_failures
    audit_path=output/'fit_audits.json.gz'
    audit_path.write_bytes(gzip.compress(json.dumps(audits,sort_keys=True,allow_nan=False).encode(),mtime=0))
    after=verify_sources(pools.root,manifests[0])
    if before!=after: raise ValueError('formal source changed')
    result=seal({'schema_version':1,'registry_checksum':registry['registry_checksum'],'selection_policy':'none','selection_sample_ids':[],
        'shared_validation_calibration':False,'artifacts':artifacts,'fit_counts':counts,'failures':failures,
        'audit_artifact':{'path':str(audit_path.resolve()),'sha256':_sha256_file(audit_path)},'source_before':before,'source_after':after,
        'code_head':code_head,'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__},
        'implementation_artifacts':[{'path':s,'sha256':_sha256_file(Path(s))} for s in IMPLEMENTATIONS],
        'scope':registry['scope'],'fresh_final_test':False,'independent_validation_status':'INCOMPLETE'},'locked_checksum')
    save_json(output/'locked_study.json',result)
    return result


def fit_b(pools, *, registry, manifests, a_artifacts, output, code_head):
    artifacts=[];audits=[];failures=[];known=registry['known_labels']
    with threadpool_limits(limits=1):
        for m in manifests:
            for seed in registry['seeds']:
                base_artifact=next(a for a in a_artifacts if (a['arm_id'],a['fold_id'],a['seed'])==('A1',m['fold_id'],seed))
                base=load_bound_model(base_artifact,output.parent);nodes={};start=time.perf_counter()
                for rpm in registry['expected_rpms']:
                    if rpm not in base['nodes']:
                        failures.append({'arm_id':'B1-B6','fold_id':m['fold_id'],'seed':seed,'rpm':rpm,'status':'INCOMPLETE','reason':'A1 unavailable'});continue
                    train=records_for(m,'train',rpm);cal=records_for(m,'calibration',rpm)
                    trans=base['nodes'][rpm]['transformer']
                    X,C=trans.transform(pools.load(train)),trans.transform(pools.load(cal))
                    y=np.array([known.index(r['label']) for r in train]);cy=np.array([known.index(r['label']) for r in cal])
                    pooled=PooledWithinLW().fit(X,y,len(known))
                    raw={'pooled_within_lw':pooled.raw_scores(C),
                         'class_mahalanobis':raw_class_scores(base['nodes'][rpm]['detectors']['mahalanobis'],C)[0],
                         'class_knn':raw_class_scores(base['nodes'][rpm]['detectors']['knn'],C)[0]}
                    scores={s['id']:ResearchScore(s,registry['rules']['conformal_alpha']).calibrate(raw[s['reference']],cy) for s in registry['score_arms']}
                    audit={'arm_id':'B','fold_id':m['fold_id'],'seed':seed,'rpm':rpm,'registry_checksum':registry['registry_checksum'],
                        'manifest_checksum':m['manifest_checksum'],'motor_roles':m['motor_roles'],'selection_policy':'none','selection_sample_ids':[],
                        'shared_validation_calibration':False,'reference_fit_ids':[r['sample_id'] for r in train],
                        'pooled_covariance_fit_ids':[r['sample_id'] for r in train],'calibration_sample_ids':[r['sample_id'] for r in cal],
                        'base_A1_artifact':base_artifact,'pooled_formula':'train own-class residuals; LedoitWolf assume_centered=True; sqrt distance',
                        'calibration_summaries':{k:v.summaries() for k,v in scores.items()},'code_head':code_head}
                    audits.append(audit);nodes[rpm]={'pooled':pooled,'scores':scores,'audit_checksum':digest(audit)}
                model={'arm_id':'B','fold_id':m['fold_id'],'seed':seed,'registry_checksum':registry['registry_checksum'],
                    'manifest_checksum':m['manifest_checksum'],'labels':known,'nodes':nodes,'reference_artifact':base_artifact}
                path=output/f"B_{m['fold_id']}_seed{seed}.joblib";joblib.dump(model,path,compress=3)
                artifacts.append({'arm_id':'B','fold_id':m['fold_id'],'seed':seed,'manifest_checksum':m['manifest_checksum'],
                    'path':str(path.resolve()),'sha256':_sha256_file(path),'node_count':len(nodes),'seconds':time.perf_counter()-start})
    return artifacts,audits,failures


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['fit','evaluate'])
    p.add_argument('--registry',type=Path,required=True)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--code-head',required=True)
    p.add_argument('--locked',type=Path)
    args=p.parse_args();log,paths=setup_run('fault_type_accuracy_study')
    registry=json.loads(args.registry.read_text(encoding='utf-8'))
    if args.action=='fit':
        result=run(FeatureStore(args.data_root),registry=registry,output=paths.output_dir,code_head=args.code_head)
        log.info('fixed fits sealed {} output={}',result['fit_counts'],paths.output_dir)
    else:
        if not args.locked:p.error('evaluate requires committed sealed lock')
        locked=json.loads(args.locked.read_text(encoding='utf-8'))
        result=evaluate(FeatureStore(args.data_root),registry=registry,locked=locked,output=paths.output_dir,trusted_root=Path.cwd()/'output',code_head=args.code_head,log=log)
        log.info('{} new logical evaluations completed; output={}',result['completed_runs'],paths.output_dir)


def validate_lock(locked,registry,manifests):
    verify_seal(locked,'locked_checksum')
    if (locked['registry_checksum']!=registry['registry_checksum'] or locked['selection_policy']!='none' or
        locked['selection_sample_ids'] or locked['shared_validation_calibration'] or
        locked['environment']!={'python':platform.python_version(),'sklearn':sklearn.__version__} or
        any(k in locked for k in ['global_winner','selected_representation'])):raise ValueError('lock config/runtime/selection mismatch')
    if [a['path'] for a in locked['implementation_artifacts']]!=IMPLEMENTATIONS:raise ValueError('implementation inventory differs')
    for a in locked['implementation_artifacts']:
        if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('fit implementation changed after lock')
    expected={(arm['id'],m['fold_id'],s) for arm in registry['arms'][1:]+[{'id':'B'}] for m in manifests for s in registry['seeds']}
    keys=[(a['arm_id'],a['fold_id'],a['seed']) for a in locked['artifacts']]
    if len(keys)!=len(expected) or set(keys)!=expected:raise ValueError('fit inventory mismatch')
    if _sha256_file(Path(locked['audit_artifact']['path']))!=locked['audit_artifact']['sha256']:raise ValueError('audit SHA mismatch')
    audits=json.loads(gzip.decompress(Path(locked['audit_artifact']['path']).read_bytes()))
    audit_by={}
    for a in audits:
        key=(a['arm_id'],a['fold_id'],a['seed'],a['rpm'])
        if key in audit_by:raise ValueError('duplicate fit audit')
        m=next(m for m in manifests if m['fold_id']==a['fold_id'])
        rpm=None if a['rpm']=='mixed' else a['rpm']
        if a['arm_id']=='B':
            train=[r['sample_id'] for r in records_for(m,'train',rpm)]
            cal=[r['sample_id'] for r in records_for(m,'calibration',rpm)]
            if (a['reference_fit_ids']!=train or a['pooled_covariance_fit_ids']!=train or a['calibration_sample_ids']!=cal or
                a['registry_checksum']!=registry['registry_checksum'] or a['manifest_checksum']!=m['manifest_checksum'] or
                a['selection_policy']!='none' or a['selection_sample_ids'] or a['shared_validation_calibration']):raise ValueError('B audit input/config mismatch')
        else:
            arm=next(x for x in registry['arms'] if x['id']==a['arm_id'])
            validate_node_audit(a,m,rpm,arm,registry)
        audit_by[key]=a
    expected_audits={(a['arm_id'],a['fold_id'],a['seed'],rpm) for a in locked['artifacts']
        for rpm in (['mixed'] if a['arm_id']=='A2' else registry['expected_rpms'])}
    if not locked['failures'] and set(audit_by)!=expected_audits:raise ValueError('audit inventory incomplete')
    return audit_by


def resolved_model(artifact,locked,registry,manifests,audits,trusted_root):
    model=load_bound_model(artifact,trusted_root)
    for key in ['arm_id','fold_id','seed','manifest_checksum']:
        if model[key]!=artifact[key]:raise ValueError('model identity mismatch')
    if model['registry_checksum']!=registry['registry_checksum'] or model['labels']!=registry['known_labels']:raise ValueError('model class/config mismatch')
    expected_nodes={a[3] for a in audits if a[:3]==(artifact['arm_id'],artifact['fold_id'],artifact['seed'])}
    if set(model['nodes'])!=expected_nodes or len(model['nodes'])!=artifact['node_count']:raise ValueError('model node inventory differs')
    base_artifact=None;base=None
    if model['reference_artifact'] is not None:
        base_artifact=next(a for a in locked['artifacts'] if (a['arm_id'],a['fold_id'],a['seed'])==('A1',artifact['fold_id'],artifact['seed']))
        if base_artifact!=model['reference_artifact']:raise ValueError('reference SHA/identity differs')
        base=resolved_model(base_artifact,locked,registry,manifests,audits,trusted_root)
    for rpm,node in model['nodes'].items():
        audit=audits[(artifact['arm_id'],artifact['fold_id'],artifact['seed'],rpm)]
        if node['audit_checksum']!=digest(audit):raise ValueError('model/audit checksum differs')
        if artifact['arm_id']=='B':
            if {k:s.summaries() for k,s in node['scores'].items()}!=audit['calibration_summaries']:raise ValueError('score calibration differs')
            if not node['pooled'].covariance.assume_centered or node['pooled'].train_rows!=len(audit['pooled_covariance_fit_ids']):raise ValueError('pooled reference differs')
        else:
            arm=next(a for a in registry['arms'] if a['id']==artifact['arm_id'])
            if node['classifier'].get_params()!=registry['classifier_resolved'][arm['classifier']][str(artifact['seed'])]:raise ValueError('classifier params differ')
            if node['fit_ids_checksum']!=digest(audit['classifier_fit_ids']):raise ValueError('classifier input checksum differs')
            if base is not None:
                node.update({k:base['nodes'][rpm][k] for k in ['transformer','detectors']})
            if node['transformer'].checksum()!=audit['transform_checksum']:raise ValueError('transform differs')
            if {k:d.class_summaries() for k,d in node['detectors'].items()}!=audit['detector_calibration']:raise ValueError('reference calibration differs')
    model['resolved_reference_model']=base
    return model


def evaluate(pools, *, registry, locked, output, trusted_root, code_head, log=None):
    baseline=check_registry(registry);_,_,manifests,_=context(baseline['baseline_index'])
    before=verify_sources(pools.root,manifests[0]);audits=validate_lock(locked,registry,manifests)
    output.mkdir(parents=True,exist_ok=True);runs=[];known=registry['known_labels'];unknown=registry['unknown_labels']
    with threadpool_limits(limits=1):
        for artifact in locked['artifacts']:
            start=time.perf_counter();m=next(m for m in manifests if m['fold_id']==artifact['fold_id'])
            model=resolved_model(artifact,locked,registry,manifests,audits,trusted_root)
            arm=artifact['arm_id'];score_ids=[s['id'] for s in registry['score_arms']] if arm=='B' else ['mahalanobis','knn']
            all_rows={s:[] for s in score_ids}
            test=records_for(m,'test');position={r['sample_id']:i for i,r in enumerate(test)}
            for key,node in model['nodes'].items():
                rpm=None if key=='mixed' else key
                records=records_for(m,'test',rpm)
                base=model['resolved_reference_model']['nodes'][key] if arm=='B' else node
                X=base['transformer'].transform(pools.load(records));pred=base['classifier'].predict(X)
                raw_cache={}
                for method in ['mahalanobis','knn']:
                    raw,thresholds,ratios,labels=raw_class_scores(base['detectors'][method],X)
                    raw_cache[method]=(raw,thresholds,ratios)
                if arm=='B':raw_cache['pooled']=node['pooled'].raw_scores(X)
                for sid in score_ids:
                    if arm=='B':
                        score_model=node['scores'][sid]
                        ref=score_model.definition['reference']
                        raw=raw_cache['pooled'] if ref=='pooled_within_lw' else raw_cache['knn' if ref=='class_knn' else 'mahalanobis'][0]
                        details=score_model.details(raw);thresholds=score_model.thresholds
                        calibration_summary=score_model.summaries()
                    else:
                        raw,thresholds,ratios=raw_cache[sid]
                        details={'score':ratios.min(1),'reject':ratios.min(1)>1,'nearest':ratios.argmin(1),'ratios':ratios,'p_values':None,'candidate_size':None,'threshold':1.}
                        calibration_summary={'thresholds':thresholds.tolist(),'calibration':'class_quantile'}
                    for i,r in enumerate(records):
                        reject=bool(details['reject'][i])
                        rows=all_rows[sid]
                        rows.append({'sample_id':r['sample_id'],'motor_id':r['t_code'],'rpm':r['rpm'],'source_file':r['source_file'],
                            'source_sha256':r['source_sha256'],'true_label':r['label'],'true_role':'unknown_test' if r['label'] in unknown else 'healthy' if r['label']==known[0] else 'known_fault',
                            'predicted_known_class':known[int(pred[i])],'openset_score':float(details['score'][i]),'is_unknown':reject,'accepted':not reject,
                            'final_class':'unknown' if reject else known[int(pred[i])],'nearest_known_class':known[int(details['nearest'][i])],
                            'raw_class_scores':dict(zip(known,raw[i].tolist())),
                            'class_thresholds':None if thresholds is None else dict(zip(known,(np.repeat(thresholds,len(known)) if len(thresholds)==1 else thresholds).tolist())),
                            'normalized_class_scores':None if details['ratios'] is None else dict(zip(known,details['ratios'][i].tolist())),
                            'class_p_values':None if details['p_values'] is None else dict(zip(known,details['p_values'][i].tolist())),
                            'candidate_set_size':None if details['candidate_size'] is None else int(details['candidate_size'][i]),
                            'threshold':details['threshold'],'arm_id':sid if arm=='B' else arm,'score_id':sid,
                            'seed':artifact['seed'],'fold_id':m['fold_id'],'registry_checksum':registry['registry_checksum'],'locked_checksum':locked['locked_checksum'],
                            'manifest_checksum':m['manifest_checksum'],'model_sha256':artifact['sha256'],
                            'classifier_model_sha256':model['reference_artifact']['sha256'] if arm=='B' else artifact['sha256'],
                            'reference_model_sha256':model['reference_artifact']['sha256'] if model['reference_artifact'] is not None else artifact['sha256'],
                            'historical_test_exposed':True})
            for sid,rows in all_rows.items():
                rows.sort(key=lambda r:position[r['sample_id']])
                name=f"{sid if arm=='B' else arm}_{m['fold_id']}_seed{artifact['seed']}"+(('_'+sid) if arm!='B' else '')
                if len(rows)!=len(test):
                    runs.append({'run_id':name,'status':'INCOMPLETE','reason':'submodel/RPM missing','samples':len(rows),'arm_id':sid if arm=='B' else arm,'score_id':sid,'fold_id':m['fold_id'],'seed':artifact['seed']});continue
                path=output/(name+'.jsonl.gz')
                with gzip.GzipFile(filename=str(path),mode='wb',mtime=0) as writer:
                    for row in rows:writer.write((json.dumps(row,sort_keys=True,allow_nan=False)+'\n').encode())
                metric=study_metrics(rows,known,unknown)
                runs.append({'run_id':name,'status':'completed','arm_id':sid if arm=='B' else arm,'score_id':sid,'fold_id':m['fold_id'],'seed':artifact['seed'],
                    'motor_roles':m['motor_roles'],'samples':len(rows),'test_ids_checksum':digest([r['sample_id'] for r in rows]),'metrics':metric,
                    'rpm_metrics':[{'rpm':rpm,'samples':len(rr),'metrics':study_metrics(rr,known,unknown)} for rpm in registry['expected_rpms'] for rr in [[r for r in rows if r['rpm']==rpm]]],
                    'configuration_metrics':[{'label':label,'samples':len(rr),'classifier_recall':float(np.mean([r['predicted_known_class']==label for r in rr])) if label in known else None,
                        'rejection_rate':float(np.mean([r['is_unknown'] for r in rr]))} for label in known+unknown for rr in [[r for r in rows if r['true_label']==label]]],
                    'nearest_reference_counts':{label:sum(r['nearest_known_class']==label for r in rows) for label in known},
                    'conformal_set_size_counts':{str(k):sum(r['candidate_set_size']==k for r in rows) for k in range(len(known)+1)} if arm=='B' and sid in ['B5','B6'] else None,
                    'prediction_artifact':{'path':str(path.resolve()),'sha256':_sha256_file(path),'rows':len(rows)},'model_artifact':artifact,
                    'seconds_including_shared_work':time.perf_counter()-start})
            if log:log.info('evaluated arm={} fold={} seed={} logical_runs={}',arm,m['fold_id'],artifact['seed'],len(runs))
    after=verify_sources(pools.root,manifests[0])
    if before!=after:raise ValueError('source changed during evaluation')
    if len(runs)!=198:raise ValueError('declared198 logical inventory differs')
    result=seal({'schema_version':1,'registry_checksum':registry['registry_checksum'],'locked_checksum':locked['locked_checksum'],
        'runs':runs,'completed_runs':sum(r['status']=='completed' for r in runs),'failed_runs':[r for r in runs if r['status']!='completed'],
        'selection_policy':'none','selection_sample_ids':[],'scope':registry['scope'],'fit_counts':locked['fit_counts'],
        'source_before':before,'source_after':after,'code_head':code_head,'fresh_final_test':False,'independent_validation_status':'INCOMPLETE'},'evaluation_checksum')
    save_json(output/'evaluation_report.json',result)
    return result


if __name__=='__main__': main()
