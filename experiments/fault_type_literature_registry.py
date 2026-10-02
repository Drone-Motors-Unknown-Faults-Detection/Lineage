"""Finite literature/adaptation registry: 24 pipelines +22 score variants, 630 evals."""
from __future__ import annotations
import argparse
import json
import platform
from pathlib import Path
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,ExtraTreesClassifier,HistGradientBoostingClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from core.fault_type_literature import BlendedDiscriminant
from core.fault_type_final_guard import seal,verify_seal
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_accuracy_baseline import context
from experiments.fault_type_openset import CLASSIFIER_CONFIG,DETECTOR_CONFIG

VERSION='literature_expansion_v1_fixed_no_selection'
IMPLEMENTATIONS=['core/fault_type_literature.py','experiments/fault_type_literature_registry.py',
    'experiments/fault_type_literature_study.py','core/openset.py','core/mahalanobis.py',
    'core/fault_type_accuracy.py','core/fault_type_accuracy_pipeline.py','core/fault_type_accuracy_scores.py',
    'core/fault_type_features.py','core/fault_type_validator.py','core/fault_type_leakage.py',
    'experiments/fault_type_fixed_calibration.py']

ARMS=[
    ('C01','base75','lda',None),('C02','base75','linear',None),('C03','base75','extra',None),
    ('C04','base75','forest',None),('C05','base75','boost',None),('C06','base75','svm',None),
    ('C07','base75','knn',5),('C08','base75','knn',15),('C09','base75','nb',None),
    ('C10','base75','rda',[.5,.1]),('C11','base75','rda',[.5,.5]),('C12','base75','rda',[0.,.1]),
    ('C13','base75','lda',.1),('C14','base75','lda',.5),('C15','base75','lda',.9),
    ('C16','signed66','lda',None),('C17','harmonic69','lda',None),('C18','harmonic66','lda',None),
    ('C19','pca20','lda',None),('C20','nca10','knn',5),('C21','harmonic69','forest',None),
    ('C22','harmonic69','svm',None),('C23','base75','rda',[1.,.1]),('C24','base75','lda',None),
]
SCORES=[
    ('R01','pooled',None),('R02','relative',1.),('R03','relative',.5),('R04','relative',2.),
    ('R05','oas',None),('R06','diagonal',None),('R07','knn_factory',1),('R08','knn_factory',15),
    ('R09','iforest',None),('R10','lof',None),('R11','ocsvm',None),('R12','gmm',None),
    ('R13','centers',None),('R14','msp',None),('R15','entropy',None),('R16','margin',None),
    ('R17','predicted',None),('R18','relative',1.),('R19','energy',None),('R20','vim',None),
    ('R21','fusion',.25),('R22','fusion',.75),
]


def classifier(arm,seed,K):
    name=arm['classifier'];p=arm['parameter']
    if name=='lda':return LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto' if p is None else p,priors=[1/K]*K)
    if name=='linear':return LogisticRegression(**CLASSIFIER_CONFIG)
    if name=='extra':return ExtraTreesClassifier(n_estimators=200,max_depth=12,min_samples_leaf=5,max_features='sqrt',class_weight='balanced',random_state=seed,n_jobs=1)
    if name=='forest':return RandomForestClassifier(n_estimators=200,max_depth=12,min_samples_leaf=5,max_features='sqrt',class_weight='balanced',random_state=seed,n_jobs=1)
    if name=='boost':return HistGradientBoostingClassifier(learning_rate=.05,max_iter=200,max_leaf_nodes=15,min_samples_leaf=20,l2_regularization=1.,class_weight='balanced',early_stopping=False,random_state=seed)
    if name=='svm':return SVC(C=1.,kernel='rbf',gamma='scale',class_weight='balanced',probability=False,random_state=seed)
    if name=='knn':return KNeighborsClassifier(n_neighbors=p,weights='distance',metric='euclidean',algorithm='brute',n_jobs=1)
    if name=='nb':return GaussianNB(priors=[1/K]*K,var_smoothing=1e-9)
    if name=='rda':return BlendedDiscriminant(pooling=p[0],shrinkage=p[1])
    raise ValueError('unknown classifier')


def build(index):
    p,_,manifests,ledger=context(index)
    arms=[{'id':a,'representation':r,'classifier':c,'parameter':v,'rpm_strategy':'separate' if a=='C24' else 'mixed'} for a,r,c,v in ARMS]
    scores=[{'id':a,'kind':k,'parameter':v,'parent_arm':'C17' if a=='R18' else 'C01'} for a,k,v in SCORES]
    # None parameters are omitted from scalar formulas, not implicitly defaulted.
    for s in scores:
        if s['parameter'] is None:s.pop('parameter')
    K=len(p['known_fault_labels'])+1
    params={a['id']:{str(seed):classifier(a,seed,K).get_params() for seed in [0,1,2]} for a in arms}
    return seal({'version':VERSION,'scope':index.get('scope','EXPLORATORY_HISTORICAL_TEST_EXPOSED'),'prior_index':index,
        'dataset_fingerprint':p['dataset_fingerprint'],'exposure_ledger_checksum':ledger['ledger_checksum'],
        'manifest_checksums':[m['manifest_checksum'] for m in manifests],
        'known_labels':[p['healthy_label'],*sorted(p['known_fault_labels'])],'unknown_labels':p['unknown_test_labels'],
        'folds':p['folds'],'seeds':[0,1,2],'rpms':p['expected_rpms'],'arms':arms,'scores':scores,
        'classifier_parameters':params,'factory_parameters':DETECTOR_CONFIG,
        'selection_policy':'none','selection_sample_ids':[],'validation_sample_ids':[],'shared_validation_calibration':False,
        'budget':{'pipelines':24,'additional_scores':22,'folds':3,'seeds':3,'logical_evaluations':630,
                  'unique_test_rows':28910,'seed_mean_is_not_new_motors':True},
        'calibration':{'quantile':.95,'method':'linear','direction':'higher score = unknown','reject_comparison':'>',
                       'signed_scores':'raw > scalar q95; never divide by negative q95','missing_predicted_class':'INCOMPLETE; no fallback'},
        'representation_rules':{'all':'RobustScaler train-only quantile_range[25,75]',
            'signed66':'train median abs scale floor1e-12; signed log1p',
            'harmonic':'30 historical band maxima / per-axis sum abs; floor=max(train median(sum)*1e-6,1e-12); not energy',
            'harmonic69':'retain66 stats/ratios +3 log1p(sum/floor) amplitude coordinates',
            'harmonic66':'same but remove amplitude coordinates (normalization ablation)',
            'pca20':'full SVD train-only20 components, no whitening',
            'nca10':'train-only NCA10, train-class stratified cap60 rows/class, seed0/1/2, max_iter50; audit actual subset; budget stop reported'},
        'novelty_rules':{'RMD':'min class pooled-LW squared distance - weight*train background LW squared distance; adaptation of Ren2021',
            'OAS':'pooled within-class residual covariance; sklearn OAS implementation, not manual exact paper',
            'centers':'2 train KMeans centers/class n_init10; pooled-LW precision, global known-cal q95',
            'gmm':'2 diagonal EM components/class; reg1e-4,n_init1,max_iter200; min negative class log-density',
            'predicted':'cal predicted-label groups, q95 distance to predicted reference; reject missing group; no cal truth routing',
            'energy':'negative logsumexp of actual fitted LDA affine decision logits T1; tabular adaptation not energy training',
            'vim':'LDA W,b origin=-pinv(W)b; train second moment about origin; principal rank20; alpha=train mean maxlogit/train mean residual; reject nonpositive alpha',
            'fusion':'known-cal robust-standardized [factoryMaha score,1-MSP]; fixed distance weights .25,.75; final global known-cal q95'},
        'limitations':{'fresh_final_test':False,'physical_independence':'UNKNOWN','final_validation':'INCOMPLETE',
            'adaptations':'predeclared after reading exposed historical results; exploratory, no global deployed winner',
            'cold_start':'not tested here; healthy+known faults only','all_methods':'finite suitable families; raw/deep/transductive methods not claimed tested'},
        'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__},
        'implementations':[{'path':s,'sha256':_sha256_file(Path(s))} for s in IMPLEMENTATIONS],
        'bibliography_artifact':{'path':'reports/literature_expansion/sources.md','sha256':_sha256_file(Path('reports/literature_expansion/sources.md'))}},'protocol_checksum')


def check(protocol):
    verify_seal(protocol,'protocol_checksum')
    if protocol!=build(protocol['prior_index']):raise ValueError('fixed protocol/runtime/source changed')
    return context(protocol['prior_index'])[2]


def run(pools,*,index):return build(index)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--index',type=Path,default=Path('reports/fixed_motor_calibration/result_index.json'))
    args=p.parse_args();log,paths=setup_run('fault_type_literature_registry')
    r=run(None,index=json.loads(args.index.read_text(encoding='utf-8')));check(r)
    save_json(paths.output_dir/'protocol.json',r);log.info('protocol={} no fit,630 planned; commit before fit',r['protocol_checksum'])


if __name__=='__main__':main()
