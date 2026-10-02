"""Read-only mechanism diagnosis of existing sealed C17 models and exposed data."""
from __future__ import annotations
import argparse
import json
import time
from collections import Counter
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from core.fault_type_accuracy_pipeline import records_for
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import seal, verify_seal
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run
from core.fault_type_metrics_v2 import classification
from experiments.fault_type_literature_registry import check
from experiments.fault_type_literature_study import validate_lock, load_bundle
from experiments.fault_type_fixed_calibration import verify_sources


def distribution(values):
    values=np.asarray(values,float)
    if values.ndim != 1 or not np.isfinite(values).all():raise ValueError('finite diagnostic vector required')
    return {'n':len(values),'min':float(values.min()),'median':float(np.median(values)),
            'q95':float(np.quantile(values,.95)),'max':float(values.max())} if len(values) else {'n':0}


def run(pools, *, index, output):
    verify_seal(index,'delivery_index_checksum')
    for name in ['protocol','locked','summary_compact']:
        a=index['artifacts'][name]
        if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('artifact SHA')
    read=lambda name:json.loads(Path(index['paths'][name]).read_text(encoding='utf-8'))
    p=read('protocol');ms=check(p);lock=read('locked');audits=validate_lock(lock,p,ms)
    before=verify_sources(pools.root,ms[0]);results=[];start=time.perf_counter()
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            if a['seed']!=0:continue # Deterministic C17; other seeds remain old verified results.
            b=load_bundle(a,lock,p,ms,audits);m=next(m for m in ms if m['fold_id']==a['fold_id'])
            node=b['models']['C17']['mixed'];ref=b['references'][node['reference_key']];clf=node['classifier']
            parts={part:records_for(m,part) for part in ['train','calibration','test']}
            # Test only diagnostics, NEVER normalization/refitting or method selection.
            parts['test']=[r for r in parts['test'] if r['label'] in p['known_labels']]
            Z={part:ref['transformer'].transform(pools.load(rows)) for part,rows in parts.items()}
            y={part:np.array([p['known_labels'].index(r['label']) for r in rows]) for part,rows in parts.items()}
            train=Z['train'];ty=y['train'];means=np.array([train[ty==c].mean(0) for c in range(6)])
            classes=[]
            for c,label in enumerate(p['known_labels']):
                X=train[ty==c];cov=np.cov(X,rowvar=False,bias=True);d=np.linalg.norm(means-means[c],axis=1);d[c]=np.inf
                competitor=int(d.argmin());dsp=float(np.sqrt(np.trace(cov)))
                parts_summary={}
                for part in parts:
                    ix=y[part]==c;zz=Z[part][ix];pred=clf.predict(zz);logits=clf.decision_function(zz)
                    margin=logits[:,c]-np.max(np.delete(logits,c,axis=1),axis=1)
                    parts_summary[part]={'samples':len(zz),'classifier_recall':float(np.mean(pred==c)),
                        'predicted_counts':dict(Counter(p['known_labels'][int(i)] for i in pred)),
                        'margin':distribution(margin),'centroid_to_train_effect_size':float(np.linalg.norm(zz.mean(0)-means[c])/max(dsp,1e-12))}
                classes.append({'label':label,'train_samples':len(X),'train_mean':means[c].tolist(),
                    'within_class_cov_trace':float(np.trace(cov)),'covariance_rank':int(np.linalg.matrix_rank(cov)),
                    'nearest_centroid_class':p['known_labels'][competitor],'nearest_centroid_distance':float(d[competitor]),
                    'nearest_separation_over_within_dispersion':float(d[competitor]/max(dsp,1e-12)),
                    'parts':parts_summary})
            shifts=[]
            for c,label in enumerate(p['known_labels']):
                for rpm in p['rpms']:
                    blocks={part:Z[part][[i for i,r in enumerate(parts[part]) if r['label']==label and r['rpm']==rpm]] for part in parts}
                    tr=blocks['train'];scale=max(float(np.sqrt(np.var(tr,axis=0).sum())),1e-12)
                    for part in ['calibration','test']:
                        shifts.append({'class':label,'rpm':rpm,'comparison':'train-'+part,
                            'motor':m['motor_roles'][part],'samples':len(blocks[part]),
                            'centroid_effect_size_train_dispersion':float(np.linalg.norm(blocks[part].mean(0)-tr.mean(0))/scale)})
                for r1,r2 in [('6000rpm','8000rpm'),('8000rpm','11000rpm'),('6000rpm','11000rpm')]:
                    x1=train[[i for i,r in enumerate(parts['train']) if r['label']==label and r['rpm']==r1]]
                    x2=train[[i for i,r in enumerate(parts['train']) if r['label']==label and r['rpm']==r2]]
                    scale=max(float(np.sqrt((np.var(x1,axis=0).sum()+np.var(x2,axis=0).sum())/2)),1e-12)
                    shifts.append({'class':label,'rpm':r1+'/'+r2,'comparison':'within-train-RPM','motor':m['motor_roles']['train'],
                        'samples':len(x1)+len(x2),'centroid_effect_size_train_dispersion':float(np.linalg.norm(x1.mean(0)-x2.mean(0))/scale)})
            same_rpm=[]
            for rpm in p['rpms']:
                blocks=[train[[i for i,r in enumerate(parts['train']) if r['label']==label and r['rpm']==rpm]] for label in p['known_labels']]
                for c in range(6):
                    d=[float(np.linalg.norm(blocks[c].mean(0)-v.mean(0))) if j!=c else float('inf') for j,v in enumerate(blocks)]
                    j=int(np.argmin(d));scale=max(float(np.sqrt((np.var(blocks[c],axis=0).sum()+np.var(blocks[j],axis=0).sum())/2)),1e-12)
                    same_rpm.append({'rpm':rpm,'class':p['known_labels'][c],'competitor':p['known_labels'][j],'separation_effect_size':d[j]/scale})
            band=[axis*22+i for axis in range(3) for i in range(12,22)]
            groups={'stats':[i for i in range(66) if i not in band],'harmonic_shape':band,'amplitude':[66,67,68]}
            contributions={name:{'dimension':len(ix),'train_rms_logit_contribution':float(np.sqrt(np.mean((train[:,ix]@clf.coef_[:,ix].T)**2)))} for name,ix in groups.items()}
            calpred=clf.predict(Z['calibration'])
            routing=[{'class':label,'raw_true_cal_count':int(sum(y['calibration']==c)),
                      'predicted_cal_count':int(sum(calpred==c))} for c,label in enumerate(p['known_labels'])]
            results.append({'fold':m['fold_id'],'seed':0,'model_sha256':a['sha256'],'motor_roles':m['motor_roles'],
                'classes':classes,'shift_effects':shifts,'same_rpm_separations':same_rpm,'feature_blocks':contributions,
                'constant_scaled_train_columns':np.flatnonzero(np.ptp(train,axis=0)==0).tolist(),
                'scaled_train_max_abs':float(np.max(np.abs(train))),
                'training_confusion':classification([p['known_labels'][i] for i in ty],[p['known_labels'][int(i)] for i in clf.predict(train)],p['known_labels']),
                'C17_calibration_routing':routing,
                'R17_actual_C01_routing':[{'class':label,'raw_true_cal_count':int(sum(y['calibration']==c)),
                    'predicted_cal_count':int(sum(b['models']['C01']['mixed']['classifier'].predict(b['references']['base75/mixed']['transformer'].transform(pools.load(parts['calibration'])))==c))} for c,label in enumerate(p['known_labels'])]})
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('source changed')
    result=seal({'scope':p['scope'],'models_refit':False,'thresholds_modified':False,'selection_performed':False,
        'in_sample_train_is_optimistic':True,'independent_development_group':'UNKNOWN',
        'test_is_historically_exposed_diagnosis_only':True,'unit_physical_semantics':'UNKNOWN; use ordered formal contract only',
        'source_before':before,'source_after':after,'folds':results,'seconds':time.perf_counter()-start},'diagnosis_checksum')
    save_json(output/'mechanism_diagnosis.json',result)
    import matplotlib;matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,ax=plt.subplots(figsize=(8,4))
    names=[];effects=[]
    for f in results:
        for c in f['classes']:
            if c['label']=='2screws':
                for part in ['train','calibration','test']:
                    names.append(f['motor_roles'][part]+' '+f['fold']+' '+part);effects.append(c['parts'][part]['classifier_recall'])
    ax.bar(names,effects);ax.tick_params(axis='x',rotation=70);ax.set_ylabel('2screws recall');ax.set_ylim(0,1)
    ax.set_title('C17: in-sample train vs cross-motor cal/test (exposed diagnosis)');fig.tight_layout()
    fig.savefig(output/'class_collapse.png');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4))
    for f in results:
        xs=[s['centroid_effect_size_train_dispersion'] for s in f['shift_effects'] if s['class']=='2screws']
        ax.plot(xs,marker='o',label=f['fold'])
    ax.set_ylabel('centroid displacement / train dispersion');ax.set_xlabel('6 cross-motor/RPM comparisons then 3 within-train RPM pairs')
    ax.legend();fig.tight_layout();fig.savefig(output/'shift_effects.png');plt.close(fig)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--index',type=Path,default=Path('reports/literature_expansion/result_index.json'))
    p.add_argument('--data-root',type=Path,required=True);a=p.parse_args();log,paths=setup_run('fault_type_mechanism_diagnosis')
    r=run(FeatureStore(a.data_root),index=json.loads(a.index.read_text(encoding='utf-8')),output=paths.output_dir)
    log.info('readonly diagnosis={} output={}',r['diagnosis_checksum'],paths.output_dir)


if __name__=='__main__':main()
