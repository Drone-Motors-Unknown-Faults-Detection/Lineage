"""Post-seal T1 failure diagnostics. Read-only, no fitting/threshold search."""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from core.fault_type_features import FeatureStore
from core.fault_type_fixed_calibration import fixed_manifests
from core.fault_type_final_guard import digest,verify_seal,seal
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run,save_plot
from experiments.fault_type_model_selection import load_prior_manifests
from experiments.fault_type_fixed_calibration import check_protocol,raw_class_scores,load_bound_model,verify_sources
from experiments.fault_type_fixed_report import load_predictions,verify_rows
from experiments.fault_type_metrics import _score_distribution


def score_groups(records, raw, thresholds, ratios, labels, known):
    scores=np.min(ratios,axis=1)
    groups=[]
    for rpm in [None,*sorted({r['rpm'] for r in records})]:
        for label in [None,*sorted({r['label'] for r in records})]:
            mask=np.array([(rpm is None or r['rpm']==rpm) and (label is None or r['label']==label) for r in records])
            if not mask.any(): continue
            groups.append({'rpm':rpm or 'ALL','configuration':label or 'ALL','samples':int(mask.sum()),
                'sample_ids_checksum':digest([r['sample_id'] for r,yes in zip(records,mask) if yes]),
                'normalized_min_score':_score_distribution(scores[mask]),'rejection_rate':float(np.mean(scores[mask]>1)),
                'nearest_normalized_class_counts':dict(Counter(known[int(labels[j])] for j in np.argmin(ratios[mask],axis=1))),
                'per_reference_class':[{ 'label':known[int(c)],'threshold':float(thresholds[j]),
                    'raw_distance':_score_distribution(raw[mask,j]),'score_over_threshold':_score_distribution(ratios[mask,j])} for j,c in enumerate(labels)]})
    return groups


def healthy_shift(parts, transformed, healthy):
    rows=[]
    for rpm in sorted({r['rpm'] for r in parts['train']}):
        masks={p:np.array([r['label']==healthy and r['rpm']==rpm for r in records]) for p,records in parts.items()}
        train=transformed['train'][masks['train']]
        reference=np.median(train,axis=0)
        for part in ['calibration','test']:
            values=transformed[part][masks[part]]
            if not len(values) or not len(train):
                rows.append({'rpm':rpm,'partition':part,'status':'NA_MISSING_HEALTHY'})
                continue
            median=np.median(values,axis=0)
            rows.append({'rpm':rpm,'partition':part,'motor':parts[part][0]['t_code'],
                'train_samples':len(train),'samples':len(values),
                'mean_absolute_median_shift_train_scaled_units':float(np.mean(np.abs(median-reference))),
                'per_feature_median_shift_train_scaled_units':(median-reference).tolist(),
                'train_feature_medians':reference.tolist(),'partition_feature_medians':median.tolist(),
                'status':'DESCRIPTIVE_NO_PHYSICAL_CAUSE_CLAIM'})
    return rows


def run(pools, *, manifests,protocol,ledger,locked,evaluation,output,trusted_root,paths=None):
    check_protocol(protocol,manifests,ledger)
    verify_seal(evaluation,'evaluation_checksum'); verify_seal(locked,'locked_checksum')
    if evaluation['locked_checksum']!=locked['locked_checksum'] or len(evaluation['runs'])!=36:
        raise ValueError('diagnostics require sealed complete fixed evaluation')
    m=next(m for m in manifests if m['motor_roles']['test']=='T1')
    known,unknown=locked['known_labels'],locked['unknown_labels']
    by={r['sample_id']:r for r in m['records']}
    parts={p:[by[s] for s in m['sample_ids'][p]] for p in ['train','calibration','test']}
    output.mkdir(parents=True,exist_ok=True)
    diagnostics=[]
    with threadpool_limits(limits=1):
        for candidate in protocol['representations']:
            artifact=next(a for a in locked['training_artifacts'] if a['fold_id']==m['fold_id'] and a['representation']==candidate['name'] and a['seed']==0)
            model=load_bound_model(artifact,trusted_root)
            transformed={p:model['transformer'].transform(pools.load(records)) for p,records in parts.items()}
            shift=healthy_shift(parts,transformed,known[0])
            for method in protocol['methods']:
                saved_run=next(r for r in evaluation['runs'] if (r['fold_id'],r['representation'],r['seed'],r['method'])==(m['fold_id'],candidate['name'],0,method))
                saved=load_predictions(saved_run['prediction_artifact'])
                verify_rows(saved,saved_run,m,protocol,locked)
                detector=model['detectors'][method]
                decomposition={p:raw_class_scores(detector,X) for p,X in transformed.items()}
                scores={p:np.min(d[2],axis=1) for p,d in decomposition.items()}
                if not np.allclose(scores['test'],[r['openset_score'] for r in saved],rtol=1e-12,atol=1e-12):
                    raise ValueError('diagnostic model scores differ from saved predictions')
                truth=np.array([r['label'] in unknown for r in parts['test']])
                thresholds=decomposition['test'][1]; reference_labels=decomposition['test'][3]
                calibration_checks=[]
                for j,c in enumerate(reference_labels):
                    label=known[int(c)]
                    train_mask=np.array([r['label']==label for r in parts['train']])
                    cal_mask=np.array([r['label']==label for r in parts['calibration']])
                    q_train=float(np.quantile(decomposition['train'][0][train_mask,j],.95))
                    q_cal=float(np.quantile(decomposition['calibration'][0][cal_mask,j],.95))
                    if not np.isclose(q_cal,thresholds[j],rtol=1e-12,atol=1e-12): raise ValueError('actual calibration quantile mismatch')
                    calibration_checks.append({'class':label,'threshold':float(thresholds[j]),'train_own_distance_q95':q_train,
                        'calibration_own_distance_q95':q_cal,'calibration_over_train_q95':q_cal/max(q_train,np.finfo(float).eps)})
                summaries={p:score_groups(records,*decomposition[p],known) for p,records in parts.items()}
                diag={'representation':candidate['name'],'method':method,'motor_roles':m['motor_roles'],
                      'seed_scope':'seed0 diagnosis; all three algorithm repeats verified identical in sealed report',
                      'unknown_samples':int(truth.sum()),'healthy_test_samples':sum(r['label']==known[0] for r in parts['test']),
                      'engineering_checks':'SHA/IDs/truth roles/strict>1/finite/raw ratios/actual model scores and own-class .95 quantiles VERIFIED',
                      'saved_metrics':saved_run['metrics'],'score_distributions':summaries,
                      'calibration_checks':calibration_checks,'healthy_same_rpm_feature_shift':shift,
                      'readonly_rank_diagnostic':{'normalized_min_auroc':float(roc_auc_score(truth,scores['test'])),
                          'uncalibrated_min_distance_auroc':float(roc_auc_score(truth,np.min(decomposition['test'][0],axis=1))),
                          'not_new_method_result':'posthoc ranking only; raw distances have class-dependent scales; no threshold/model selected'},
                      'score_highest_unknown':float(scores['test'][truth].max()),
                      'score_highest_known':float(scores['test'][~truth].max())}
                diagnostics.append(diag)
                if paths:
                    import matplotlib
                    matplotlib.use('Agg')
                    import matplotlib.pyplot as plt
                    fig,ax=plt.subplots(figsize=(7,4))
                    groups={'train known':scores['train'],'calibration known':scores['calibration'],
                            'test healthy':scores['test'][np.array([r['label']==known[0] for r in parts['test']])],
                            'test known faulty':scores['test'][np.array([r['label'] in known[1:] for r in parts['test']])],
                            'test unknown':scores['test'][truth]}
                    for name,values in groups.items():
                        ordered=np.sort(values); ax.plot(np.maximum(ordered,np.finfo(float).eps),np.arange(1,len(ordered)+1)/len(ordered),label=name)
                    ax.axvline(1,color='black',linestyle='--',label='fixed reject >1'); ax.set_xscale('log')
                    ax.set(xlabel='Normalized factory score (log)',ylabel='Empirical cumulative fraction',title=f'T1 / {candidate["name"]} / {method}')
                    ax.legend(fontsize=8); fig.tight_layout(); save_plot(fig,paths,f'{candidate["name"]}_{method}_scores.png'); plt.close(fig)
            if _sha256_file(Path(artifact['path']))!=artifact['sha256']: raise ValueError('diagnosis changed model bytes')
    result=seal({'scope':'POSTHOC_READONLY_DIAGNOSIS_NOT_MODEL_SELECTION','test_motor':'T1','diagnostics':diagnostics,
        'model_modified':False,'threshold_search':False,'evaluation_checksum':evaluation['evaluation_checksum'],
        'limitations':['Raw/time/session/physical units/alignment/mount/load unknown; cannot identify causal mechanism',
                       'Three distinct motors, not degradation trajectory; no RUL/hourly rates/delays',
                       'Historical per-file cleaning and stage-specific feature semantics confound physical domain-shift interpretation']},'diagnosis_checksum')
    save_json(output/'diagnosis.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['matrix','protocol','ledger','locked','evaluation','data-root']: p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args(); log,paths=setup_run('fault_type_fixed_diagnosis')
    protocol=json.loads(args.protocol.read_text(encoding='utf-8')); priors,_=load_prior_manifests(args.matrix)
    manifests=fixed_manifests(priors,protocol); ledger=json.loads(gzip.decompress(args.ledger.read_bytes()))
    locked=json.loads(args.locked.read_text(encoding='utf-8')); evaluation=json.loads(args.evaluation.read_text(encoding='utf-8'))
    before=verify_sources(args.data_root,manifests[0])
    result=run(FeatureStore(args.data_root),manifests=manifests,protocol=protocol,ledger=ledger,locked=locked,evaluation=evaluation,
               output=paths.output_dir,trusted_root=Path.cwd()/'output',paths=paths)
    after=verify_sources(args.data_root,manifests[0]); save_json(paths.output_dir/'source_verification.json',{'before':before,'after':after,'unchanged':before==after})
    log.info('{} read-only diagnostics complete; no fit/no threshold search',len(result['diagnostics']))


if __name__=='__main__': main()
