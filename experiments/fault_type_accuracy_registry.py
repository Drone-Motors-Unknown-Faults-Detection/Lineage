"""Preregister exactly198 new logical evaluations; no selector or test fit."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import platform
import sklearn
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import RobustScaler
from core.fault_type_accuracy import VIBRATION75, VIBRATION66, REMOVED, RELATION_RTOL, RELATION_ATOL
from core.fault_type_final_guard import seal, verify_seal
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file, FEATURE_NAMES
from core.logger import setup_run
from experiments.fault_type_openset import CLASSIFIER_CONFIG, DETECTOR_CONFIG

PROTOCOL = 'fault_type_accuracy_study_v2_json_contract'
SEEDS = [0,1,2]
RPMS = ['6000rpm','8000rpm','11000rpm']
ARMS = [
    {'id':'A0','indices':VIBRATION75,'rpm_strategy':'mixed','classifier':'linear','signed_log':False,'reuse_baseline':True},
    {'id':'A1','indices':VIBRATION75,'rpm_strategy':'separate','classifier':'linear','signed_log':False},
    {'id':'A2','indices':VIBRATION66,'rpm_strategy':'mixed','classifier':'linear','signed_log':False},
    {'id':'A3','indices':VIBRATION66,'rpm_strategy':'separate','classifier':'linear','signed_log':False},
    {'id':'A4','indices':VIBRATION66,'rpm_strategy':'separate','classifier':'linear','signed_log':True},
    {'id':'A5','indices':VIBRATION75,'rpm_strategy':'separate','classifier':'extra_trees','signed_log':False,'reference_arm':'A1'},
    {'id':'A6','indices':VIBRATION75,'rpm_strategy':'separate','classifier':'hist_gradient','signed_log':False,'reference_arm':'A1'},
    {'id':'A7','indices':VIBRATION75,'rpm_strategy':'separate','classifier':'shrinkage_lda','signed_log':False,'reference_arm':'A1'},
    {'id':'A8','indices':VIBRATION75,'rpm_strategy':'separate','classifier':'rbf_svm','signed_log':False,'reference_arm':'A1'},
]
SCORES = [
    {'id':'B1','reference':'class_mahalanobis','calibration':'global_quantile'},
    {'id':'B2','reference':'pooled_within_lw','calibration':'class_quantile'},
    {'id':'B3','reference':'pooled_within_lw','calibration':'global_quantile'},
    {'id':'B4','reference':'class_knn','calibration':'global_quantile'},
    {'id':'B5','reference':'class_mahalanobis','calibration':'conditional_conformal'},
    {'id':'B6','reference':'class_knn','calibration':'conditional_conformal'},
]


def classifier(name, seed, n_classes):
    if name=='linear': return LogisticRegression(**CLASSIFIER_CONFIG)
    if name=='extra_trees': return ExtraTreesClassifier(n_estimators=200,max_depth=12,min_samples_leaf=5,max_features='sqrt',class_weight='balanced',random_state=seed,n_jobs=1)
    if name=='hist_gradient': return HistGradientBoostingClassifier(learning_rate=.05,max_iter=200,max_leaf_nodes=15,min_samples_leaf=20,l2_regularization=1.,class_weight='balanced',early_stopping=False,random_state=seed)
    if name=='shrinkage_lda': return LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto',priors=[1/n_classes]*n_classes)
    if name=='rbf_svm': return SVC(C=1.,kernel='rbf',gamma='scale',class_weight='balanced',probability=False,random_state=seed)
    raise ValueError('unregistered classifier')


def build_registry(baseline, baseline_path):
    verify_seal(baseline,'baseline_checksum')
    old=baseline['baseline_index']
    index=old['paths']
    p=json.loads(Path(index['protocol']).read_text(encoding='utf-8'))
    verify_seal(p,'protocol_checksum')
    n=len(p['known_fault_labels'])+1
    params={name:{str(s):classifier(name,s,n).get_params() for s in SEEDS} for name in ['linear','extra_trees','hist_gradient','shrinkage_lda','rbf_svm']}
    paths=['experiments/fault_type_accuracy_registry.py','experiments/fault_type_openset.py','core/openset.py','core/mahalanobis.py','core/fault_type_feature_contract.py','core/fault_type_validator.py']
    return seal({'schema_version':1,'protocol_version':PROTOCOL,'scope':'EXPLORATORY_HISTORICAL_TEST_EXPOSED',
        'selection_policy':'none','selection_sample_ids':[],'validation_sample_ids':[],'shared_validation_calibration':False,
        'baseline_artifact':{'path':str(Path(baseline_path).resolve()),'sha256':_sha256_file(Path(baseline_path)),'baseline_checksum':baseline['baseline_checksum']},
        'baseline_index':old,'dataset_fingerprint':p['dataset_fingerprint'],'baseline_protocol_checksum':p['protocol_checksum'],
        'exposure_ledger_checksum':p['exposure_ledger_checksum'],'known_labels':[p['healthy_label'],*sorted(p['known_fault_labels'])],
        'unknown_labels':p['unknown_test_labels'],'folds':p['folds'],'seeds':SEEDS,'expected_rpms':RPMS,
        'arms':ARMS,'score_arms':SCORES,'classifier_resolved':params,'scaler_resolved':json.loads(json.dumps(RobustScaler().get_params())),'detectors':DETECTOR_CONFIG,
        'removed_features':[{'zero_based':i,'canonical_name':FEATURE_NAMES[i]} for i in REMOVED],
        'feature_mapping':{a['id']:[{'zero_based':i,'canonical_name':FEATURE_NAMES[i]} for i in a['indices']] for a in ARMS},
        'redundancy_tolerance':{'rtol':RELATION_RTOL,'atol':RELATION_ATOL},
        'signed_log':{'scale':'max(median_train(abs(x_j)),1e-12)','formula':'sign(x)*log1p(abs(x)/scale)','inverse':'sign(z)*expm1(abs(z))*scale','after':'train-only RobustScaler'},
        'rules':{'quantile':.95,'quantile_method':'linear','denominator_floor':'numpy float64 epsilon','distance_unit':'square root of quadratic form; knn mean5 Euclidean',
                 'pooled_covariance':'LedoitWolf(assume_centered=True) on train residual x-mu_train_label',
                 'B1_B4':'min raw distance / max(quantile95(min raw distances on known cal),eps); reject >1',
                 'B2':'min_c raw pooled distance / max(class own cal q95,eps); reject >1',
                 'B3':'pooled minimum raw / global cal q95; reject >1',
                 'B5_B6':'p_c=(1+count(cal_true_c raw_c >= raw_c(x)))/(n_c+1); reject max(p)<=.05; score=1-max(p)',
                 'conformal_alpha':.05,'conformal_ties':'>=','conformal_warning':'exchangeability across motors/windows unproved; no5% deployment guarantee',
                 'routing':'metadata RPM only; unsupported RPM rejected; no order tracking',
                 'missing':'NA/INCOMPLETE cell with reason; never borrow RPM/test/cal for fit','minimum_reference_per_class':5},
        'planned':{'new_A_logical_evaluations':144,'new_B_logical_evaluations':54,'total_new_logical_evaluations':198,
                   'classifier_fits':198,'factory_reference_fits':180,'pooled_reference_fits':27,
                   'baseline_A0_evaluations_reused':18,'seed_note':'algorithm seeds only; no new motor or acquisition'},
        'pairs':[['A1','A0'],['A2','A0'],['A3','A1'],['A3','A2'],['A4','A3'],['A5','A1'],['A6','A1'],['A7','A1'],['A8','A1'],['B1','A1/mahalanobis'],['B2','A1/mahalanobis'],['B3','B1'],['B3','B2'],['B4','A1/knn'],['B5','A1/mahalanobis'],['B6','A1/knn']],
        'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__},
        'sources':[{'path':q,'sha256':_sha256_file(Path(q))} for q in paths],
        'papers':{'ExtraTrees':'Geurts, Ernst, Wehenkel (2006), Machine Learning63:3–42; https://doi.org/10.1007/s10994-006-6226-1',
                  'SVM':'Cortes, Vapnik (1995), Machine Learning20:273–297; https://doi.org/10.1007/BF00994018',
                  'gradient_boosting':'Friedman (2001), Annals of Statistics29:1189–1232; https://doi.org/10.1214/aos/1013203451; HGB is sklearn histogram implementation, not exact paper reproduction',
                  'shrinkage':'Ledoit, Wolf (2004), Journal of Multivariate Analysis88:365–411; https://doi.org/10.1016/S0047-259X(03)00096-4',
                  'conformal':'Angelopoulos, Bates (2023), Foundations and Trends in Machine Learning; https://arxiv.org/html/2107.07511v6',
                  'tree_priority':'Grinsztajn, Oyallon, Varoquaux (NeurIPS2022 benchmark); no motor-data performance guarantee'},
        'fresh_final_test':False,'independent_validation_status':'INCOMPLETE','raw_acquisition':'UNKNOWN','global_winner_forbidden':True},'registry_checksum')


def check_registry(registry):
    verify_seal(registry,'registry_checksum')
    if (registry['protocol_version']!=PROTOCOL or registry['arms']!=ARMS or registry['score_arms']!=SCORES or
        registry['seeds']!=SEEDS or registry['expected_rpms']!=RPMS or registry['selection_policy']!='none' or
        registry['selection_sample_ids'] or registry['validation_sample_ids'] or registry['shared_validation_calibration']):
        raise ValueError('fixed study budget/selection changed')
    for s in registry['sources']:
        if _sha256_file(Path(s['path']))!=s['sha256']: raise ValueError('shared implementation SHA changed')
    artifact=registry['baseline_artifact']
    if _sha256_file(Path(artifact['path']))!=artifact['sha256']: raise ValueError('baseline artifact SHA changed')
    baseline=json.loads(Path(artifact['path']).read_text(encoding='utf-8'))
    expected=build_registry(baseline,artifact['path'])
    if expected!=registry: raise ValueError('registry differs from fixed formulas/runtime/source')
    return baseline


def run(pools, *, baseline_path):
    baseline=json.loads(Path(baseline_path).read_text(encoding='utf-8'))
    return build_registry(baseline,baseline_path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    args=p.parse_args();log,paths=setup_run('fault_type_accuracy_registry')
    r=run(None,baseline_path=args.baseline);check_registry(r)
    save_json(paths.output_dir/'registry.json',r)
    log.info('registry={} expected198 new evaluations; no fit. Commit/push first. output={}',r['registry_checksum'],paths.output_dir)


if __name__=='__main__': main()
