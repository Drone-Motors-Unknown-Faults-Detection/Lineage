"""Fixed research screening gates, NOT independent deployment guarantees."""
import numpy as np

CONTRACT = {
    'version': 'continuous_reliability_v1',
    'scope': 'ADAPTIVE_EXPLORATORY; A/B cannot imply independent C',
    'primary': 'motor macro known-fault F1 and fault accuracy; all seeds',
    'fault_f1_gain_over_C17': .02, 'fault_accuracy_gain_over_C24': .02,
    'motor_fault_f1_drop_tolerance': .01, 'minimum_motor_class_recall': .10,
    'healthy_total_alarm_max_each_motor_rpm': .10,
    'unknown_recall_drop_tolerance_each_motor_rpm_vs_C02': .02,
    'minimum_motor_unknown_recall': .10,
    'known_correct_after_rejection_drop_vs_D01': .01,
    'coverage_drop_each_motor_rpm_vs_D01': .10,
    'minimum_known_subsets_for_B': 3,
    'threshold_search': False, 'minimum_independent_test_groups_per_class': 2,
    'rationale': '2pp material gain; 1pp motor F1/postreject guard; prior temporary 10% full health cap; '
        '10% class/unknown floor avoids accepting existing zero-recall collapse. Research values, not deployment requirements.'}


def check_contract(contract):
    if contract != CONTRACT: raise ValueError('versioned reliability contract changed')


def assess(candidate, controls, contract=CONTRACT, *, subsets_verified=1):
    """All seed/group values required; no missing cell can silently pass."""
    check_contract(contract); reasons = []; incomplete = []
    expected = {(motor, rpm, seed) for motor in ['T1', 'T2', 'T3']
                for rpm in ['6000rpm', '8000rpm', '11000rpm'] for seed in [0, 1, 2]}
    def cells(runs):
        out = {}
        if len(runs) != 9: incomplete.append('expected nine motor/seed runs')
        for run in runs:
            for g in run['rpm_metrics']:
                key = (run['motor_roles']['test'], g['rpm'], run['seed'])
                if key in out: raise ValueError('duplicate motor/RPM/seed')
                out[key] = g['metrics']
        if set(out) != expected: incomplete.append('missing/unexpected motor/RPM/seed coverage')
        return out
    c = cells(candidate); base = {k: cells(v) for k, v in controls.items()}
    if not {'C02', 'C17', 'C24', 'D01'} <= set(base): raise ValueError('required controls missing')
    overall_expected = {(motor, seed) for motor in ['T1', 'T2', 'T3'] for seed in [0, 1, 2]}
    for name, runs in [('candidate', candidate), *controls.items()]:
        keys = [(r['motor_roles']['test'], r['seed']) for r in runs]
        if len(keys) != len(set(keys)): raise ValueError('duplicate motor/seed run')
        if set(keys) != overall_expected: incomplete.append(name+' overall coverage')
        for r in runs:
            m = r['metrics']; f = m['known_fault_classification']
            values = [f['macro_f1'], f['accuracy'], m['known_correct_after_rejection'],
                      m['unknown_rejection']['unknown_recall'], *[x['recall'] for x in f['per_class']]]
            if any(v is None or not np.isfinite(v) for v in values) or not f['per_class'] or any(x['support'] <= 0 for x in f['per_class']):
                incomplete.append(name+' missing overall support/finite metric')
    if incomplete:
        return {'contract_version':contract['version'], 'main_screen':'INCOMPLETE', 'reasons':[],
                'incomplete':incomplete, 'evidence_B':False, 'evidence_C':False,
                'fresh_final_test':False, 'subsets_verified':subsets_verified,
                'independent_final_guard':'INCOMPLETE; requirement unchanged', 'production_replacement':False}
    for key, m in c.items():
        if key not in expected or any(key not in d for d in base.values()): continue
        health = m['healthy_safety_v2']['healthy_total_alarm_rate']; ur = m['unknown_rejection']['unknown_recall']
        coverage = m['selective']['coverage']; known = m['known_fault_classification']['per_class']
        values = [health, ur, coverage, *[x['recall'] for x in known],
                  base['C02'][key]['unknown_rejection']['unknown_recall'], base['D01'][key]['selective']['coverage']]
        if any(v is None or not np.isfinite(v) for v in values) or any(x['support'] == 0 for x in known):
            incomplete.append('missing class/health/unknown support '+str(key)); continue
        if health > contract['healthy_total_alarm_max_each_motor_rpm']: reasons.append('health '+str(key))
        if ur < base['C02'][key]['unknown_rejection']['unknown_recall'] - contract['unknown_recall_drop_tolerance_each_motor_rpm_vs_C02']:
            reasons.append('unknown noninferiority '+str(key))
        if coverage < base['D01'][key]['selective']['coverage'] - contract['coverage_drop_each_motor_rpm_vs_D01']:
            reasons.append('coverage '+str(key))
    for seed in [0, 1, 2]:
        rr = [r for r in candidate if r['seed'] == seed]
        if len(rr) != 3: continue
        mean = lambda runs, branch, field: float(np.mean([r['metrics'][branch][field] for r in runs if r['seed'] == seed]))
        if mean(rr, 'known_fault_classification', 'macro_f1') < mean(controls['C17'], 'known_fault_classification', 'macro_f1') + contract['fault_f1_gain_over_C17']:
            reasons.append('primary F1 seed'+str(seed))
        if mean(rr, 'known_fault_classification', 'accuracy') < mean(controls['C24'], 'known_fault_classification', 'accuracy') + contract['fault_accuracy_gain_over_C24']:
            reasons.append('primary accuracy seed'+str(seed))
        if np.mean([r['metrics']['known_correct_after_rejection'] for r in rr]) < np.mean([r['metrics']['known_correct_after_rejection'] for r in controls['D01'] if r['seed']==seed]) - contract['known_correct_after_rejection_drop_vs_D01']:
            reasons.append('postrejection seed'+str(seed))
        for r in rr:
            motor = r['motor_roles']['test']; m = r['metrics']
            b = next(x for x in controls['C17'] if x['seed']==seed and x['motor_roles']['test']==motor)['metrics']
            if m['known_fault_classification']['macro_f1'] < b['known_fault_classification']['macro_f1'] - contract['motor_fault_f1_drop_tolerance']:
                reasons.append('motor F1 '+motor+' seed'+str(seed))
            if min(x['recall'] for x in m['known_fault_classification']['per_class']) < contract['minimum_motor_class_recall']:
                reasons.append('class collapse '+motor+' seed'+str(seed))
            if m['unknown_rejection']['unknown_recall'] < contract['minimum_motor_unknown_recall']:
                reasons.append('motor unknown floor '+motor+' seed'+str(seed))
    screen = not reasons and not incomplete
    return {'contract_version': contract['version'], 'main_screen': 'INCOMPLETE' if incomplete else 'PASS' if screen else 'FAILED',
            'reasons': reasons, 'incomplete': incomplete, 'evidence_B': bool(screen and subsets_verified >= contract['minimum_known_subsets_for_B']),
            'evidence_C': False, 'fresh_final_test': False, 'subsets_verified': subsets_verified,
            'independent_final_guard': 'INCOMPLETE; requirement unchanged', 'production_replacement': False}
