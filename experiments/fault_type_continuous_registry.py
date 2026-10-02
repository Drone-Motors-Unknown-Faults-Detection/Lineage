"""Seal first continuous batch: eight matched arms, 72 exposed-data runs."""
import argparse
import platform
import subprocess
from pathlib import Path
import sklearn
from core.fault_type_final_guard import seal,verify_seal
from core.fault_type_reliability import CONTRACT,check_contract
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_mechanism_registry import parents,read

ARMS=[{'id':'Q01','kind':'neighbors','metric':False,'subset_classifier':True,'detector':'C02/M'},
      {'id':'Q02','kind':'neighbors','metric':True,'subset_classifier':True,'detector':'C02/M'},
      {'id':'Q03','kind':'neighbors','metric':False,'subset_classifier':False,'detector':'C02/M'},
      {'id':'Q04','kind':'neighbors','metric':True,'subset_classifier':False,'detector':'C02/M'},
      {'id':'Q05','kind':'gain','dimension':63,'detector':'self/M'},
      {'id':'Q06','kind':'gain','dimension':66,'detector':'self/M'},
      {'id':'Q07','kind':'gain','dimension':69,'detector':'self/M'},
      {'id':'Q08','kind':'gain','dimension':66,'detector':'C02/M'}]
FILES=['core/fault_type_continuous.py','core/fault_type_reliability.py','experiments/fault_type_continuous_registry.py',
       'experiments/fault_type_continuous_study.py','experiments/fault_type_continuous_report.py',
       'reports/continuous_research/source_ledger.md','reports/continuous_research/hypothesis_adaptation_cards.md']
PARAMS={'neighbors':{'n_neighbors':5,'weights':'distance','algorithm':'brute','p':2,'n_jobs':1},
        'lda':{'solver':'lsqr','shrinkage':'auto','priors':'uniform'},
        'metric':{'target_k':3,'subset_per_class_rpm':20,'pull':.5,'push':.5,'ridge':.01,
                  'maxiter':150,'maxfun':500,'maxls':50,'ftol':1e-9,'gtol':1e-6,'max_seconds':120},
        'scaler':{'type':'RobustScaler','quantile_range':[25,75]},'floor':{'relative':1e-6,'absolute':1e-12}}


def build(index):
    pp,ms,lock,_=parents(index)
    return seal({'version':'continuous_Q_v1','scope':'ADAPTIVE_EXPLORATORY_ALL_OLD_TEST_EXPOSED',
        'parent_index':index,'parent_protocol_checksum':pp['protocol_checksum'],'parent_locked_checksum':lock['locked_checksum'],
        'dataset_fingerprint':pp['dataset_fingerprint'],'manifest_checksums':[m['manifest_checksum'] for m in ms],
        'known_labels':pp['known_labels'],'unknown_labels':pp['unknown_labels'],'rpms':pp['rpms'],'seeds':[0,1,2],
        'folds':[{'fold_id':m['fold_id'],'motor_roles':m['motor_roles']} for m in ms],
        'factory_parameters':pp['factory_parameters'],'exposure_ledger_checksum':pp['exposure_ledger_checksum'],
        'selection_policy':'none','selection_sample_ids':[],'validation_sample_ids':[], 'shared_validation_calibration':False,
        'all_old_28910_samples_exposed':True,'fresh_final_test':False,'arms':ARMS,'parameters':PARAMS,
        'reliability_contract':CONTRACT,'budget':{'planned_runs':72,'max_fit_seconds':1800,'max_evaluate_seconds':1800,
            'max_verify_seconds':1800,'reserve_C_bytes':1000000000,'artifact_estimate_bytes':200000000},
        'score':{'higher_is_unknown':True,'threshold':1.,'comparison':'>','q':.95,'quantile':'linear'},
        'limitations':{'raw_independence':'UNKNOWN','inner_independent_groups':'UNKNOWN; no model selection',
            'minimum_two_independent_test_groups_per_class':'INCOMPLETE','subset_robustness':'NOT_YET_RUN'},
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__},
        'implementations':[{'path':f,'sha256':_sha256_file(Path(f))} for f in FILES]},'protocol_checksum')


def check(p):
    verify_seal(p,'protocol_checksum');check_contract(p['reliability_contract'])
    if p['version']!='continuous_Q_v1' or p['arms']!=ARMS or p['parameters']!=PARAMS or p['seeds']!=[0,1,2]:raise ValueError('fixed batch changed')
    if p['selection_policy']!='none' or p['selection_sample_ids'] or p['validation_sample_ids'] or p['shared_validation_calibration'] or p['fresh_final_test'] or not p['all_old_28910_samples_exposed']:raise ValueError('selection/exposure changed')
    if p['environment']!={'python':platform.python_version(),'sklearn':sklearn.__version__}:raise ValueError('science runtime changed')
    if [a['path'] for a in p['implementations']]!=FILES:raise ValueError('implementation inventory')
    for a in p['implementations']:
        if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('implementation SHA changed')
    pp,ms,lock,audits=parents(p['parent_index'])
    for k in ['dataset_fingerprint','known_labels','unknown_labels','rpms','factory_parameters','exposure_ledger_checksum']:
        if p[k]!=pp[k]:raise ValueError('parent source/class binding')
    if p['parent_protocol_checksum']!=pp['protocol_checksum'] or p['parent_locked_checksum']!=lock['locked_checksum'] or p['manifest_checksums']!=[m['manifest_checksum'] for m in ms] or p['folds']!=[{'fold_id':m['fold_id'],'motor_roles':m['motor_roles']} for m in ms]:raise ValueError('parent split binding')
    if p['budget']['planned_runs']!=len(ARMS)*len(ms)*len(p['seeds']) or p['score']!={'higher_is_unknown':True,'threshold':1.,'comparison':'>','q':.95,'quantile':'linear'}:raise ValueError('fixed score/budget')
    return pp,ms,lock,audits


def run(pools,*,index):return build(index)
def main():
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('--index',type=Path,default=Path('reports/literature_expansion/result_index.json'))
    a=q.parse_args();log,paths=setup_run('fault_type_continuous_registry');p=run(None,index=read(a.index));check(p)
    save_json(paths.output_dir/'protocol.json',p);log.info('protocol={} 72 planned; commit BEFORE fit',p['protocol_checksum'])
if __name__=='__main__':main()
