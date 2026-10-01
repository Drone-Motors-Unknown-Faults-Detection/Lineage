"""Bounded exploratory-study helpers; original CSV and defaults stay untouched."""
from __future__ import annotations

import numpy as np
from experiments.fault_type_fixed_calibration import metrics_for

VIBRATION75 = list(range(15, 90))
REMOVED = [offset + i for offset in (15, 40, 65) for i in (7, 12, 13)]
VIBRATION66 = [i for i in VIBRATION75 if i not in REMOVED]
RELATION_RTOL, RELATION_ATOL = 1e-8, 1e-10


def verify_redundancy(X):
    X = np.asarray(X, float)
    if X.ndim != 2 or X.shape[1] != 105 or not len(X) or not np.isfinite(X).all():
        raise ValueError('finite nonempty formal105 train required')
    checks = []
    for axis, offset in zip(('X', 'Y', 'Z'), (15, 40, 65)):
        for name, lhs, rhs in [('clearance=impulse', X[:, offset+7], X[:, offset+9]),
                               ('msa=rms_squared', X[:, offset+12], X[:, offset]**2),
                               ('variance=std_squared', X[:, offset+13], X[:, offset+3]**2)]:
            valid = bool(np.allclose(lhs, rhs, rtol=RELATION_RTOL, atol=RELATION_ATOL))
            checks.append({'axis': axis, 'relation': name, 'maximum_absolute_error': float(np.max(np.abs(lhs-rhs))), 'valid': valid})
    if not all(c['valid'] for c in checks):
        raise ValueError('train feature contract mismatch: '+str(checks))
    return {'checks': checks, 'rtol': RELATION_RTOL, 'atol': RELATION_ATOL,
            'removed_zero_based': REMOVED, 'retained_zero_based': VIBRATION66,
            'input_scope': 'train only; no correlation-based feature selection'}


def study_metrics(rows, known, unknown):
    result = metrics_for(rows, known, unknown)
    accepted = [r for r in rows if not r['is_unknown']]
    correct = sum(r['true_label'] in known and r['true_label'] == r['predicted_known_class'] for r in accepted)
    accepted_known = [r for r in accepted if r['true_label'] in known]
    n_known = sum(r['true_label'] in known for r in rows)
    healthy = [r for r in rows if r['true_label'] == known[0]]
    result['selective'] = {'accepted_samples': len(accepted), 'total_samples': len(rows),
        'coverage': len(accepted)/len(rows), 'accuracy_all_accepted': correct/len(accepted) if accepted else None,
        'known_coverage': len(accepted_known)/n_known if n_known else None,
        'accuracy_known_accepted': correct/len(accepted_known) if accepted_known else None,
        'definition': 'accepted unknown samples count incorrect; accuracy never replaces coverage'}
    result['healthy_contribution'] = {'healthy_samples': len(healthy), 'known_samples': n_known,
        'healthy_correct': sum(r['predicted_known_class'] == known[0] for r in healthy),
        'healthy_correct_fraction_of_all_known': sum(r['predicted_known_class'] == known[0] for r in healthy)/n_known if n_known else None}
    return result
