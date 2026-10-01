"""End-to-end synthetic198 CLI fixture. NEVER a motor research result."""
from __future__ import annotations
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from core.fault_type_sample_split import load_formal_catalog, generate_campaign_folds
from core.fault_type_manifest import build_split_manifest, write_split_manifest
from core.fault_type_final_guard import build_exposure_ledger, seal
from core.fault_type_fixed_calibration import fixed_manifests
from core.fault_type_features import FeatureStore
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_fixed_calibration import build_protocol, run as fixed_fit, evaluate as fixed_evaluate


def run(pools, *, output):
    labels=['8screws','1screws','2screws','3screws','3_14screws','4screws','4_146screws','5screws','6screws','7screws']
    root=output/'synthetic_features';rng=np.random.default_rng(20261001)
    for stage in ['1','2','3']:
        for rpm in ['6000rpm','8000rpm','11000rpm']:
            for j,label in enumerate(labels):
                X=rng.normal(size=(12,105))+j*.1+int(stage)*.02
                for off in [15,40,65]:
                    X[:,off]=np.abs(X[:,off]);X[:,off+3]=np.abs(X[:,off+3])
                    X[:,off+7]=X[:,off+9];X[:,off+12]=X[:,off]**2;X[:,off+13]=X[:,off+3]**2
                path=root/f'Step-{stage}/myfeature/T{stage}/{rpm}/{label}/{label}_Group_feature_data_clean.csv'
                path.parent.mkdir(parents=True,exist_ok=True);pd.DataFrame(X,columns=[f'x{i}' for i in range(105)]).to_csv(path,index=False)
    records,catalog=load_formal_catalog(root)
    role={'checksum':'r'*64,'split_id':'synthetic-N5','class_combination_id':'synthetic','class_combination_seed':42,
        'protocol':'A','healthy_label':labels[0],'known_fault_labels':labels[1:6],'unknown_validation_labels':[],'unknown_test_labels':labels[6:]}
    folds=generate_campaign_folds(records,healthy_label=role['healthy_label'],known_fault_labels=role['known_fault_labels'],unknown_test_labels=role['unknown_test_labels'])
    priors=[build_split_manifest(records,catalog,role,f,sample_split_seed=s,git_commit='synthetic') for f,s in zip(folds,[42,123,2026])]
    ledger=build_exposure_ledger(records,FeatureStore(root),test_ids={r['sample_id'] for r in records},evidence=[{'scope':'SYNTHETIC_ENGINEERING_ONLY'}])
    ledger_path=output/'ledger.json.gz';ledger_path.write_bytes(gzip.compress(json.dumps(ledger).encode(),mtime=0))
    protocol=build_protocol(priors,ledger);save_json(output/'protocol.json',protocol)
    manifests=fixed_manifests(priors,protocol)
    fixed_root=output/'baseline_fit';evaluation_root=output/'baseline_evaluation'
    locked=fixed_fit(FeatureStore(root),manifests=manifests,protocol=protocol,ledger=ledger,output=fixed_root,code_head='synthetic')
    fixed_evaluate(FeatureStore(root),manifests=manifests,protocol=protocol,ledger=ledger,locked=locked,output=evaluation_root,trusted_root=output)
    diagnosis_root=output/'diagnosis';diagnosis_root.mkdir();save_json(diagnosis_root/'diagnosis.json',seal({'scope':'SYNTHETIC_ENGINEERING_ONLY'},'diagnosis_checksum'))
    index={'paths':{'protocol':str((output/'protocol.json').resolve()),'locked_fit_root':str(fixed_root.resolve()),
        'evaluation_root':str(evaluation_root.resolve()),'diagnosis_root':str(diagnosis_root.resolve()),'exposure_ledger':str(ledger_path.resolve())}}
    index_path=output/'index.json';save_json(index_path,index)
    modules=[('fault_type_accuracy_baseline',['--index',str(index_path),'--data-root',str(root),'--code-head','synthetic']),
             ('fault_type_accuracy_registry',[]),('fault_type_accuracy_study',['fit']),('fault_type_accuracy_study',['evaluate']),('fault_type_accuracy_report',[])]
    outputs=[];commands=[]
    for i,(module,args) in enumerate(modules):
        if i==1:args+=['--baseline',outputs[0]+'/baseline_index.json']
        if i in [2,3]:args+=['--registry',outputs[1]+'/registry.json','--data-root',str(root),'--code-head','synthetic']
        if i==3:args+=['--locked',outputs[2]+'/locked_study.json']
        if i==4:args+=['--registry',outputs[1]+'/registry.json','--locked',outputs[2]+'/locked_study.json','--evaluation',outputs[3]+'/evaluation_report.json']
        parent=Path('output')/module;previous=set(parent.glob('*'));command=[sys.executable,'-m','experiments.'+module]+args
        r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8')
        (output/f'command_{i}.txt').write_text(r.stdout+r.stderr,encoding='utf-8');commands.append({'command':command,'exit_code':r.returncode})
        if r.returncode:raise RuntimeError(f'synthetic step{i} failed; retained command_{i}.txt')
        fresh=set(parent.glob('*'))-previous
        if len(fresh)!=1:raise ValueError('synthetic CLI output collision')
        outputs.append(str(fresh.pop().resolve()))
    result=json.loads((Path(outputs[-1])/'verified_results.json').read_text(encoding='utf-8'))
    if result['new_completed_evaluations']!=198:raise ValueError('smoke inventory differs')
    index={'scope':'SYNTHETIC_ENGINEERING_ONLY_NOT_RESEARCH','status':'PASS','new_evaluations':198,
        'commands':commands,'outputs':outputs,'fit_counts':result['fit_counts']}
    save_json(output/'smoke_index.json',index)
    return index


def main():
    argparse.ArgumentParser(description=__doc__).parse_args();log,paths=setup_run('fault_type_accuracy_smoke')
    r=run(None,output=paths.output_dir);log.info('synthetic{} evaluations PASS output={}',r['new_evaluations'],paths.output_dir)


if __name__=='__main__':main()
