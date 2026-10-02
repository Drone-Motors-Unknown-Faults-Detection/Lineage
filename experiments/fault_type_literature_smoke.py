"""Reuse immutable existing synthetic fixture; 630 engineering evaluations only."""
from __future__ import annotations
import argparse
import json
import platform
from pathlib import Path
from core.fault_type_features import FeatureStore
from core.logger import setup_run
from core.fault_type_provenance import save_json
from experiments.fault_type_literature_registry import build
from experiments.fault_type_literature_study import run as study


def run(pools,*,fixture,output):
    index=json.loads((fixture/'index.json').read_text(encoding='utf-8'))
    index['scope']='SYNTHETIC_ENGINEERING_ONLY_NOT_RESEARCH'
    protocol=build(index);save_json(output/'protocol.json',protocol)
    if protocol['dataset_fingerprint']=='c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d':raise ValueError('not synthetic data')
    pools=FeatureStore(fixture/'synthetic_features');folders={}
    for name in ['fit','evaluate','verify']:
        folders[name]=output/name;folders[name].mkdir()
    lock=study(pools,action='fit',protocol=protocol,output=folders['fit'],code_head='synthetic-engineering')
    evaluation=study(pools,action='evaluate',protocol=protocol,output=folders['evaluate'],code_head='synthetic-engineering',locked=lock)
    result=study(pools,action='verify',protocol=protocol,output=folders['verify'],code_head='synthetic-engineering',locked=lock,evaluation=evaluation)
    status={'scope':protocol['scope'],'python':platform.python_version(),'status':'PASS','completed':result['completed_runs'],
        'failed':len(result['failed_runs']),'planned':630,'prediction_records':result['prediction_records'],'protocol_checksum':protocol['protocol_checksum'],
        'failed_cases':result['failed_runs'],'output':str(output.resolve())}
    if status['completed']+status['failed']!=630:raise ValueError('synthetic inventory')
    save_json(output/'smoke_index.json',status);return status


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,default=Path('output/fault_type_accuracy_smoke/2026-10-02-00-30-45'))
    a=p.parse_args();log,paths=setup_run('fault_type_literature_smoke_py'+platform.python_version().replace('.','_'))
    result=run(None,fixture=a.fixture,output=paths.output_dir);log.info('{} synthetic completed{} failed{}',result['status'],result['completed'],result['failed'])


if __name__=='__main__':main()
