"""Read-only score distributions; posthoc diagnosis, never fitting or selection.

Uses the sealed study's existing infer function and trusted model loader.
No threshold scan, new model, unknown fitting, or changed protocol is permitted.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from core.fault_type_final_guard import seal, verify_seal
from core.fault_type_features import FeatureStore
from core.fault_type_provenance import save_json
from core.logger import setup_run
from core.fault_type_accuracy_pipeline import records_for
from experiments.fault_type_literature_registry import check
from experiments.fault_type_literature_study import validate_lock, load_bundle, infer, artifact
from experiments.fault_type_fixed_calibration import verify_sources


def distribution(scores, threshold):
    x = np.asarray(scores, float)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all() or not np.isfinite(threshold):
        raise ValueError('finite nonempty scores and threshold required')
    q = [.05, .25, .5, .75, .95]
    return {'samples':len(x), 'minimum':float(x.min()), 'maximum':float(x.max()),
            'quantiles':dict(zip(map(str,q),map(float,np.quantile(x,q)))),
            'threshold':float(threshold), 'median_minus_threshold':float(np.median(x)-threshold),
            'reject_rate':float(np.mean(x > threshold)),
            'note':'raw signed scores; no division by zero or negative threshold'}


def summarize(records, scores, threshold, known):
    if len(records) != len(scores):
        raise ValueError('record/score count differs')
    labels = sorted({r['label'] for r in records})
    groups = []
    for rpm in ['all', *sorted({r['rpm'] for r in records})]:
        for label in ['all', *labels]:
            ix = [i for i,r in enumerate(records)
                  if (rpm == 'all' or r['rpm'] == rpm) and (label == 'all' or r['label'] == label)]
            if ix:
                groups.append({'rpm':rpm, 'label':label,
                    'class_role':'mixed' if label == 'all' else 'healthy' if label == known[0]
                        else 'known_fault' if label in known else 'unknown_fault',
                    **distribution(np.asarray(scores)[ix], threshold)})
    return groups


def run(pools, *, protocol, locked, verified, output, inputs):
    manifests = check(protocol)
    audits = validate_lock(locked, protocol, manifests)
    verify_seal(verified, 'report_checksum')
    if (verified['protocol_checksum'] != protocol['protocol_checksum'] or
            verified['locked_checksum'] != locked['locked_checksum']):
        raise ValueError('diagnosis binding differs')
    before = verify_sources(pools.root, manifests[0])
    # Bounded diagnostic view only. Full protocol is validated above; no refit.
    # These IDs are hypotheses/comparators, NOT a test-selected deployment winner.
    view = dict(protocol,
        arms=[a for a in protocol['arms'] if a['id'] in ['C01','C02','C17']],
        scores=[s for s in protocol['scores'] if s['id'] in
                ['R01','R02','R03','R04','R18','R19','R20']])
    results = []
    with threadpool_limits(limits=1):
        for a in locked['artifacts']:
            b = load_bundle(a, locked, protocol, manifests, audits)
            m = next(m for m in manifests if m['fold_id'] == a['fold_id'])
            for part in ['train','calibration','test']:
                records = records_for(m, part)
                for (arm,score_id),(_,scores,threshold) in infer(b, view, records, pools).items():
                    results.append({'method_id':arm+'/'+score_id, 'fold_id':a['fold_id'],
                        'seed':a['seed'], 'part':part, 'motor':m['motor_roles'][part],
                        'model_sha256':a['sha256'],
                        'groups':summarize(records, scores, threshold, protocol['known_labels'])})
    after = verify_sources(pools.root, manifests[0])
    if after != before:
        raise ValueError('sources changed during diagnosis')
    result = seal({'scope':'POSTHOC_READ_ONLY_DIAGNOSIS_NOT_NEW_EVALUATIONS',
        'data_scope':protocol['scope'], 'version':'literature_diagnosis_v1_read_only',
        'implementation':artifact(Path(__file__)),
        'diagnostic_arm_ids':[a['id'] for a in view['arms']],
        'diagnostic_score_ids':[s['id'] for s in view['scores']],
        'inputs':inputs, 'protocol_checksum':protocol['protocol_checksum'],
        'locked_checksum':locked['locked_checksum'], 'verified_checksum':verified['report_checksum'],
        'source_before':before, 'source_after':after, 'distributions':results,
        'selection_policy':'none', 'thresholds_modified':False, 'models_refit':False,
        'limitations':['raw session/window/mount/unit/load evidence UNKNOWN',
                      'test historically exposed; diagnostic truth grouping is not model input',
                      'no false alarms/hour, delay, RUL or quantified aging truth']}, 'diagnosis_checksum')
    save_json(output/'diagnosis.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['protocol','locked','verified']:
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--data-root', type=Path, required=True)
    args = p.parse_args()
    log, paths = setup_run('fault_type_literature_diagnosis')
    inputs = {name:artifact(getattr(args,name)) for name in ['protocol','locked','verified']}
    read = lambda name:json.loads(getattr(args,name).read_text(encoding='utf-8'))
    result = run(FeatureStore(args.data_root), protocol=read('protocol'), locked=read('locked'),
                 verified=read('verified'), output=paths.output_dir, inputs=inputs)
    log.info('read-only diagnosis {} distribution sets; output={}',
             len(result['distributions']), paths.output_dir)


if __name__ == '__main__':
    main()
