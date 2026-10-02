"""Recompute metric v2 from immutable, verified saved predictions; no fitting."""
from __future__ import annotations
import argparse
import gzip
import json
import time
from pathlib import Path
from core.fault_type_metrics_v2 import metrics_v2
from core.fault_type_final_guard import seal, verify_seal, digest
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_literature_study import verify_rows, validate_lock
from experiments.fault_type_literature_registry import check


def run(pools, *, index, output):
    verify_seal(index,'delivery_index_checksum')
    for a in index['artifacts'].values():
        if _sha256_file(Path(a['path'])) != a['sha256']:raise ValueError('baseline artifact SHA')
    read=lambda name:json.loads(Path(index['paths'][name]).read_text(encoding='utf-8'))
    protocol=read('protocol');manifests=check(protocol);lock=read('locked');validate_lock(lock,protocol,manifests)
    e=read('evaluation');verify_seal(e,'evaluation_checksum')
    if e['protocol_checksum']!=protocol['protocol_checksum'] or e['locked_checksum']!=lock['locked_checksum']:raise ValueError('evaluation binding')
    runs=[];count=0;unique=set();start=time.perf_counter()
    for r in e['runs']:
        a=r['prediction_artifact'];path=Path(a['path'])
        if _sha256_file(path)!=a['sha256']:raise ValueError('prediction SHA')
        rows=[json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
        m=next(m for m in manifests if m['fold_id']==r['fold_id'])
        verify_rows(rows,r,m,protocol,lock)
        result={k:r[k] for k in ['run_id','arm_id','score_id','fold_id','seed','motor_roles','samples','test_ids_checksum','prediction_artifact']}
        result['metrics']=metrics_v2(rows,protocol['known_labels'],protocol['unknown_labels'])
        result['rpm_metrics']=[{'rpm':rpm,'metrics':metrics_v2([x for x in rows if x['rpm']==rpm],protocol['known_labels'],protocol['unknown_labels'])} for rpm in protocol['rpms']]
        old=r['metrics']['healthy_safety']['false_positive_rate']
        if old != result['metrics']['healthy_safety_v2']['healthy_to_unknown_rate']:raise ValueError('old metric definition differs')
        runs.append(result);count+=len(rows);unique.update(x['sample_id'] for x in rows)
        if len(runs)%50==0:print('recomputed',len(runs),'of',len(e['runs']),flush=True)
    if count!=e['prediction_records'] or len(runs)!=e['completed_runs']:raise ValueError('inventory')
    result=seal({'version':'metric_definition_v2','baseline_index_checksum':index['delivery_index_checksum'],
        'protocol_checksum':protocol['protocol_checksum'],'runs':runs,'failed_runs':e['failed_runs'],
        'prediction_records':count,'unique_samples':len(unique),'models_refit':False,'models_reinferred':False,
        'seconds':time.perf_counter()-start,'scope':protocol['scope'],'healthy_research_limit':.10,
        'limit_note':'temporary research screen: <=10% total health alarm in EACH motor/RPM; not deployment promise; no threshold optimization',
        'source_checks':{a['path']:a['sha256'] for a in index['artifacts'].values()}},'metrics_checksum')
    save_json(output/'metrics_v2.json',result)
    (output/'metrics_v2.json.gz').write_bytes(gzip.compress(json.dumps(result,sort_keys=True,allow_nan=False).encode(),mtime=0))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,default=Path('reports/literature_expansion/result_index.json'))
    a=parser.parse_args();log,paths=setup_run('fault_type_metrics_v2')
    result=run(None,index=json.loads(a.index.read_text(encoding='utf-8')),output=paths.output_dir)
    log.info('v2 metrics={} runs={} records={}; no refit, output={}',result['metrics_checksum'],len(result['runs']),result['prediction_records'],paths.output_dir)


if __name__=='__main__':main()
