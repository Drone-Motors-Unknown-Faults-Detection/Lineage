"""Verify saved baseline and train-only feature relations; never refit baseline."""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import platform
import sklearn
from core.fault_type_accuracy import study_metrics, verify_redundancy
from core.fault_type_final_guard import seal, verify_seal, digest
from core.fault_type_features import FeatureStore
from core.fault_type_manifest import read_split_manifest
from core.fault_type_provenance import save_json
from core.formal_data import _sha256_file
from core.logger import setup_run
from experiments.fault_type_fixed_calibration import check_protocol, verify_sources
from experiments.fault_type_fixed_report import verify_report


def context(index):
    paths = index['paths']
    protocol = json.loads(Path(paths['protocol']).read_text(encoding='utf-8'))
    locked_path = Path(paths['locked_fit_root'])/'locked_methods.json'
    locked = json.loads(locked_path.read_text(encoding='utf-8'))
    verify_seal(locked, 'locked_checksum')
    manifests = []
    for a in locked['manifest_artifacts']:
        if _sha256_file(Path(a['path'])) != a['sha256']:
            raise ValueError('baseline manifest SHA mismatch')
        manifests.append(read_split_manifest(Path(a['path'])))
    ledger = json.loads(gzip.decompress(Path(paths['exposure_ledger']).read_bytes()))
    check_protocol(protocol, manifests, ledger)
    for a in locked['training_artifacts']+[locked['fit_audit_artifact']]:
        if _sha256_file(Path(a['path'])) != a['sha256']:
            raise ValueError('baseline model/audit SHA mismatch')
    return protocol, locked, manifests, ledger


def run(pools, *, index, code_head):
    protocol, locked, manifests, ledger = context(index)
    before = verify_sources(pools.root, manifests[0])
    evaluation_path = Path(index['paths']['evaluation_root'])/'evaluation_report.json'
    report = json.loads(evaluation_path.read_text(encoding='utf-8'))
    verified, predictions = verify_report(report, manifests=manifests, protocol=protocol, locked=locked)
    runs = []
    for r in report['runs']:
        rows = predictions[r['run_id']]
        runs.append({k: r[k] for k in ['run_id', 'fold_id', 'seed', 'representation', 'method', 'motor_roles', 'prediction_artifact']} |
            {'metrics': study_metrics(rows, locked['known_labels'], locked['unknown_labels']),
             'rpm_metrics': [{'rpm': rpm, 'metrics': study_metrics([x for x in rows if x['rpm'] == rpm], locked['known_labels'], locked['unknown_labels'])} for rpm in protocol['expected_rpms']]})
    train_checks, counts = [], []
    for m in manifests:
        by = {r['sample_id']: r for r in m['records']}
        train = [by[s] for s in m['sample_ids']['train']]
        X = pools.load(train)
        train_checks.append({'fold_id': m['fold_id'], 'train_ids_checksum': digest(m['sample_ids']['train']), 'relations': verify_redundancy(X)})
        for part in ['train', 'calibration', 'test']:
            c = Counter((by[s]['rpm'], by[s]['label']) for s in m['sample_ids'][part])
            counts.append({'fold_id': m['fold_id'], 'partition': part, 'motor': m['motor_roles'][part],
                'ids_checksum': digest(m['sample_ids'][part]), 'cells': [{'rpm': rpm, 'label': label, 'samples': n} for (rpm,label), n in sorted(c.items())]})
    diagnosis_path = Path(index['paths']['diagnosis_root'])/'diagnosis.json'
    diagnosis = json.loads(diagnosis_path.read_text(encoding='utf-8'))
    verify_seal(diagnosis, 'diagnosis_checksum')
    after = verify_sources(pools.root, manifests[0])
    if before != after: raise ValueError('source changed')
    return seal({'schema_version': 1, 'scope': 'EXPLORATORY_HISTORICAL_TEST_EXPOSED', 'code_head': code_head,
        'environment': {'python': platform.python_version(), 'sklearn': sklearn.__version__},
        'baseline_index': index, 'verified_predictions': {k: verified[k] for k in ['completed_evaluations','prediction_records','unique_test_sample_ids']},
        'source_before': before, 'source_after': after, 'new_baseline_fits': 0,
        'baseline_runs': runs, 'train_feature_checks': train_checks, 'partition_counts': counts,
        'diagnosis_artifact': {'path': str(diagnosis_path.resolve()), 'sha256': _sha256_file(diagnosis_path)},
        'baseline_evaluation_artifact': {'path': str(evaluation_path.resolve()), 'sha256': _sha256_file(evaluation_path)},
        'problems': {'engineering_bug': 'no covered score/label/SHA error found', 'ranking': 'T1 overall weak; RPM-dependent reversal',
                     'calibration_transfer': 'wide class acceptance documented; no threshold cap',
                     'physical_semantics': 'UNKNOWN acquisition/synchronization/installation; not repaired by higher scores'},
        'fresh_final_test': False, 'independent_validation_status': 'INCOMPLETE'}, 'baseline_checksum')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index', type=Path, default=Path('reports/fixed_motor_calibration/result_index.json'))
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--code-head', required=True)
    args = p.parse_args(); log, paths = setup_run('fault_type_accuracy_baseline')
    result = run(FeatureStore(args.data_root), index=json.loads(args.index.read_text(encoding='utf-8')), code_head=args.code_head)
    save_json(paths.output_dir/'baseline_index.json', result)
    log.info('baseline verified, no new fit; output={}', paths.output_dir)


if __name__ == '__main__': main()
