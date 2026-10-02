"""Seal nine complete mechanisms BEFORE fitting/evaluation (81 cells)."""
from __future__ import annotations
import argparse
import json
import platform
import subprocess
from pathlib import Path
import sklearn
from core.fault_type_final_guard import seal,verify_seal
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_literature_registry import check as parent_check
from experiments.fault_type_literature_study import validate_lock

IMPLEMENTATIONS=['core/fault_type_mechanisms.py','core/fault_type_metrics_v2.py',
    'experiments/fault_type_mechanism_registry.py','experiments/fault_type_mechanism_study.py']
ARMS=[{'id':'D01','classifier':'C17','detector':'C02/M','kind':'decoupled'},
      {'id':'D02','classifier':'C17','detector':'C02/K','kind':'decoupled'},
      {'id':'D03','classifier':'C24','detector':'C02/M','kind':'decoupled'},
      *[{'id':'P0'+str(i+1),'classifier':'RPMPartialPooling','beta':b,'detector':'C02/M','kind':'partial_pool'} for i,b in enumerate([0.,.5,1.])],
      {'id':'G01','classifier':'C17','detector':'block geometry','background_weight':0.,'kind':'block'},
      {'id':'G02','classifier':'C17','detector':'block geometry','background_weight':1.,'kind':'block'},
      {'id':'G03','classifier':'block nearest','detector':'block geometry','background_weight':0.,'kind':'block'}]


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def parents(index):
    verify_seal(index,'delivery_index_checksum')
    for name in ['protocol','locked','summary_compact']:
        a=index['artifacts'][name]
        if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('parent artifact SHA')
    p=read(index['paths']['protocol']);ms=parent_check(p);lock=read(index['paths']['locked']);audits=validate_lock(lock,p,ms)
    return p,ms,lock,audits


def build(index):
    p,ms,lock,_=parents(index)
    return seal({'version':'mechanisms_v2_fixed_no_selection','scope':'EXPLORATORY_HISTORICAL_TEST_EXPOSED',
        'parent_index':index,'parent_protocol_checksum':p['protocol_checksum'],'parent_locked_checksum':lock['locked_checksum'],
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'dataset_fingerprint':p['dataset_fingerprint'],'manifest_checksums':[m['manifest_checksum'] for m in ms],
        'known_labels':p['known_labels'],'unknown_labels':p['unknown_labels'],'rpms':p['rpms'],'seeds':[0,1,2],
        'folds':[{'fold_id':m['fold_id'],'motor_roles':m['motor_roles']} for m in ms],
        'exposure_ledger_checksum':p['exposure_ledger_checksum'],'all_old_28910_samples_exposed':True,
        'arms':ARMS,'selection_policy':'none','selection_sample_ids':[],'validation_sample_ids':[],
        'shared_validation_calibration':False,'calibration':{'q':.95,'quantile_method':'linear','factory_threshold':1.,'comparison':'>','higher_is_unknown':True,'signed':'no division/abs/sign reversal'},
        'factory_parameters':p['factory_parameters'],'parent_classifier_parameters':p['classifier_parameters'],
        'rules':{'P':'one global base75 parent train scaler; perRPM means/within pooled LW cov convex beta0,.5,1; equal class prior; no target fit',
            'G':'harmonic69 parent train scaler; stats36/shape30/amp3 separate within residual LW; 1/3 mean per-dimension squared distances; min-class; bg coefficient0/1',
            'covariance_eigen_floor':'max(trace/d,1e-12)*1e-10 numerical floor only; not a fitted hyperparameter',
            'missing_rpm_class':'INCOMPLETE, no fallback or role substitution',
            'seed':'no motor role changes; deterministic duplicates disclosed',
            'decision_inputs':'formal numeric features plus declared RPM only; no true labels/path/T-code as features'},
        'budget':{'mechanisms':3,'new_complete_arms':9,'folds':3,'seeds':3,'new_evaluations':81,'maximum':108,'rounds':1},
        'gate':{'healthy_total_limit':.10,'each_motor_rpm':True,'meaning':'temporary research screen, not deployment guarantee',
            'ordering':['complete health alarm constraint','worst class recall / worst unknown recall','trade-off table; no deployed global winner'],
            'stop':'no second round if remaining option is test-driven coefficient shopping'},
        'limitations':{'fresh_final_test':False,'final_guard':'INCOMPLETE; >=2 test groups unchanged','acquisition_independence':'UNKNOWN','development_groups':'UNKNOWN; no row-random inner selection'},
        'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__},
        'implementations':[{'path':s,'sha256':_sha256_file(Path(s))} for s in IMPLEMENTATIONS],
        'research_documents':[{'path':s,'sha256':_sha256_file(Path(s))} for s in ['reports/mechanism_research_v2/source_ledger.md','reports/mechanism_research_v2/hypothesis_cards.md','reports/mechanism_research_v2/adaptation_cards.md']]},'protocol_checksum')


def check(p):
    verify_seal(p,'protocol_checksum')
    if p['arms']!=ARMS or p['seeds']!=[0,1,2] or p['selection_policy']!='none' or p['selection_sample_ids'] or p['validation_sample_ids'] or p['shared_validation_calibration']:raise ValueError('fixed arm/selection rules changed')
    if p['environment']!={'python':platform.python_version(),'sklearn':sklearn.__version__}:raise ValueError('science runtime changed')
    for a in p['implementations']+p['research_documents']:
        if _sha256_file(Path(a['path']))!=a['sha256']:raise ValueError('protocol implementation/document changed')
    pp,ms,lock,audits=parents(p['parent_index'])
    if p['parent_protocol_checksum']!=pp['protocol_checksum'] or p['parent_locked_checksum']!=lock['locked_checksum'] or p['dataset_fingerprint']!=pp['dataset_fingerprint'] or p['manifest_checksums']!=[m['manifest_checksum'] for m in ms]:raise ValueError('parent/data/split binding')
    if any(p[k]!=pp[k] for k in ['known_labels','unknown_labels','rpms','factory_parameters','exposure_ledger_checksum']) or p['folds']!=[{'fold_id':m['fold_id'],'motor_roles':m['motor_roles']} for m in ms] or p['budget']['new_evaluations']!=81 or p['gate']['healthy_total_limit']!=.10:raise ValueError('fixed class/roles/calibration/budget binding')
    return pp,ms,lock,audits


def run(pools,*,index):return build(index)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--index',type=Path,default=Path('reports/literature_expansion/result_index.json'))
    a=p.parse_args();log,paths=setup_run('fault_type_mechanism_registry');r=run(None,index=read(a.index));check(r)
    save_json(paths.output_dir/'protocol.json',r);log.info('protocol={} 81 cells; commit BEFORE fit/evaluate',r['protocol_checksum'])


if __name__=='__main__':main()
