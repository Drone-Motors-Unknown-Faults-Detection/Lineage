"""Read-only baseline inventory for continuing adaptive exploratory research."""
import argparse
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
import scipy
import sklearn
from core.fault_type_final_guard import verify_seal, seal
from core.formal_data import _sha256_file
from core.fault_type_features import FeatureStore
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_mechanism_registry import parents, read
from experiments.fault_type_fixed_calibration import verify_sources


def dependencies(output):
    """Version snapshot, not a recreated environment or editable-source lock."""
    freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True,
                            text=True, encoding='utf-8', errors='replace')
    listing = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'],
                             capture_output=True, text=True, encoding='utf-8', check=True)
    snapshot = {'freeze_exit_code': freeze.returncode, 'freeze_stdout': freeze.stdout,
                'freeze_stderr': freeze.stderr, 'installed_versions': json.loads(listing.stdout),
                'meaning': 'Read-only version inventory; not an installation lock or editable source reconstruction'}
    save_json(output / 'dependencies.json', snapshot)
    return {'path': str((output / 'dependencies.json').resolve()),
            'sha256': _sha256_file(output / 'dependencies.json'),
            'freeze_exit_code': freeze.returncode, 'fallback': 'pip list --format=json'}


def run(pools, *, output):
    indices = {}
    for name, file in [('literature', 'reports/literature_expansion/result_index.json'),
                       ('mechanisms', 'reports/mechanism_research_v2/result_index.json')]:
        d = read(file); verify_seal(d, 'delivery_index_checksum')
        for key, a in d['artifacts'].items():
            if _sha256_file(Path(a['path'])) != a['sha256']:
                raise ValueError(name + '/' + key + ' SHA mismatch')
        indices[name] = {'path': str(Path(file).resolve()), 'sha256': _sha256_file(Path(file)),
                         'artifact_hashes_verified': len(d['artifacts']), 'checksum': d['delivery_index_checksum']}
    p, ms, lock, audits = parents(read(indices['literature']['path']))
    data = verify_sources(pools.root, ms[0])
    result = seal({'version': 'continuous_inventory_v1', 'scope': 'ADAPTIVE_EXPLORATORY_ALL_OLD_TEST_EXPOSED',
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'branch': subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip(),
        'remote': subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip(),
        'dirty_tracked': subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], text=True).splitlines(),
        'indices': indices, 'parent_audits_verified': len(audits),
        'parent_models_sha': [{'path': a['path'], 'sha256': a['sha256'],
                              'verified': _sha256_file(Path(a['path'])) == a['sha256']} for a in lock['artifacts']],
        'formal_source_scan': data, 'dataset_fingerprint': p['dataset_fingerprint'],
        'environment': {'python': platform.python_version(), 'sklearn': sklearn.__version__,
                        'numpy': np.__version__, 'scipy': scipy.__version__, 'platform': platform.platform()},
        'available_tools': {x: bool(importlib.util.find_spec(x)) for x in
            ['torch', 'tensorflow', 'xgboost', 'lightgbm', 'catboost', 'metric_learn', 'pyod', 'pywt', 'optuna']},
        'disk': {drive: dict(zip(['total', 'used', 'free'], shutil.disk_usage(drive))) for drive in ['C:/', 'D:/']},
        'dependencies': dependencies(output),
        'no_refit_or_reinference': True, 'raw_independence': 'UNKNOWN', 'fresh_final_test': False}, 'inventory_checksum')
    if not all(a['verified'] for a in result['parent_models_sha']):
        raise ValueError('parent model SHA mismatch')
    save_json(output / 'inventory.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, default=Path('data/formal_local'))
    a = parser.parse_args(); log, paths = setup_run('fault_type_continuous_inventory')
    d = run(FeatureStore(a.data_root), output=paths.output_dir)
    log.info('inventory={} 41 artifact hashes; no fit/reinference', d['inventory_checksum'])


if __name__ == '__main__': main()
