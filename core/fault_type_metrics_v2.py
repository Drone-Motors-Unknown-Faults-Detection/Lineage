"""Full final-decision health safety; additive research schema, old seals untouched.

Higher scores reject as unknown, strictly score > threshold. Unknown is ROC/AP
positive. No truth enters decision(); ties accept, signed scores are not divided.
"""
from __future__ import annotations
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
from experiments.fault_type_metrics import interpolated_fpr_at_tpr

VERSION = 'metric_definition_v2'


def decision(prediction, score, threshold):
    if not np.isfinite(score) or not np.isfinite(threshold):
        raise ValueError('finite score and threshold required')
    return 'unknown' if score > threshold else prediction


def ratio(count, total):
    return float(count / total) if total else None


def classification(truth, prediction, labels, recall_labels=None):
    """Retain healthy/unknown prediction columns in fault-only matrices."""
    labels = list(labels); recall_labels = labels if recall_labels is None else list(recall_labels)
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for t, p in zip(truth, prediction):
        matrix[labels.index(t), labels.index(p)] += 1
    support = matrix.sum(1); predicted = matrix.sum(0); diagonal = matrix.diagonal()
    per = []
    for name in recall_labels:
        i = labels.index(name); tp = int(diagonal[i])
        per.append({'label': name, 'support': int(support[i]),
                    'precision': ratio(tp, int(predicted[i])) if predicted[i] else 0.,
                    'recall': ratio(tp, int(support[i])),
                    'f1': ratio(2*tp, int(support[i]+predicted[i])) if support[i]+predicted[i] else 0.})
    valid = [x for x in per if x['support']]
    return {'n_samples': len(truth), 'accuracy': ratio(int(diagonal.sum()), len(truth)),
            'balanced_accuracy': float(np.mean([x['recall'] for x in valid])) if valid else None,
            'macro_f1': float(np.mean([x['f1'] for x in per])) if truth else None,
            'per_class': per, 'confusion_matrix': matrix.tolist(), 'labels': labels,
            'axes': 'rows=true, columns=prediction; all support retained'}


def metrics_v2(rows, known, unknown, healthy_limit=.10):
    known, unknown = list(known), list(unknown)
    if not known or len(set(known+unknown)) != len(known+unknown) or 'unknown' in known+unknown:
        raise ValueError('disjoint explicit class mapping required')
    if not 0 <= healthy_limit <= 1: raise ValueError('invalid safety limit')
    if len({r['sample_id'] for r in rows}) != len(rows): raise ValueError('duplicate sample ID')
    for r in rows:
        if r['true_label'] not in known+unknown or r['predicted_known_class'] not in known:
            raise ValueError('undeclared class/index')
        final = decision(r['predicted_known_class'], r['openset_score'], r['threshold'])
        if r['is_unknown'] is not (final == 'unknown'): raise ValueError('reject routing differs')
        if r.get('final_decision', final) != final: raise ValueError('final decision differs')
    healthy = known[0]
    kk = [r for r in rows if r['true_label'] in known]
    ff = [r for r in kk if r['true_label'] != healthy]
    hh = [r for r in rows if r['true_label'] == healthy]
    uu = [r for r in rows if r['true_label'] in unknown]
    accepted = [r for r in rows if not r['is_unknown']]
    final = [decision(r['predicted_known_class'], r['openset_score'], r['threshold']) for r in rows]
    truth = ['unknown' if r['true_label'] in unknown else r['true_label'] for r in rows]
    hu = sum(r['is_unknown'] for r in hh)
    hf = sum(not r['is_unknown'] and r['predicted_known_class'] != healthy for r in hh)
    correct = sum(not r['is_unknown'] and r['true_label'] == r['predicted_known_class'] for r in kk)
    reject = sum(r['is_unknown'] for r in uu); allreject = sum(r['is_unknown'] for r in rows)
    flags = [int(r['true_label'] in unknown) for r in rows]; scores = [r['openset_score'] for r in rows]
    rankable = bool(kk and uu)
    recall = ratio(reject, len(uu)); precision = ratio(reject, allreject) if allreject else (0. if uu else None)
    safety = ratio(hu+hf, len(hh))
    return {'version': VERSION, 'n_test_samples': len(rows),
        'known_classification': classification([r['true_label'] for r in kk], [r['predicted_known_class'] for r in kk], known),
        'known_fault_classification': classification([r['true_label'] for r in ff], [r['predicted_known_class'] for r in ff], known, known[1:]),
        'final_open_set_classification': classification(truth, final, known+['unknown']),
        'known_correct_after_rejection': ratio(correct, len(kk)),
        'known_rejection_rate': ratio(sum(r['is_unknown'] for r in kk), len(kk)),
        'unknown_prevalence': ratio(len(uu), len(rows)),
        'unknown_rejection': {'n_unknown': len(uu), 'unknown_recall': recall, 'unknown_precision': precision,
            'unknown_f1': 2*precision*recall/(precision+recall) if precision is not None and recall is not None and precision+recall else (0. if uu else None),
            'auroc_unknown_positive': float(roc_auc_score(flags, scores)) if rankable else None,
            'aupr_unknown_positive': float(average_precision_score(flags, scores)) if uu else None,
            'fpr_at_95_tpr': interpolated_fpr_at_tpr(flags, scores)['value'] if rankable else None},
        'healthy_safety_v2': {'n_healthy': len(hh), 'healthy_to_unknown_count': hu, 'healthy_to_known_fault_count': hf,
            'healthy_to_unknown_rate': ratio(hu, len(hh)), 'healthy_to_known_fault_rate': ratio(hf, len(hh)),
            'healthy_total_alarm_rate': safety, 'research_limit': healthy_limit,
            'fixed_point_constraint_satisfied': safety <= healthy_limit if safety is not None else None,
            'unknown_recall_at_fixed_point_under_constraint': recall if safety is not None and safety <= healthy_limit else None,
            'abstain_or_quality_alerts': 0},
        'selective': {'coverage': ratio(len(accepted), len(rows)), 'accepted_samples': len(accepted),
            'accuracy_all_accepted': ratio(correct, len(accepted))},
        'conflicts': {'correct_known_rejected': sum(r['is_unknown'] and r['true_label']==r['predicted_known_class'] for r in kk),
            'wrong_known_accepted': sum(not r['is_unknown'] and r['true_label']!=r['predicted_known_class'] for r in kk),
            'unknown_to_healthy': sum(not r['is_unknown'] and r['predicted_known_class']==healthy for r in uu)}}
