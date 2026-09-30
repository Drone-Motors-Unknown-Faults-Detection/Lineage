"""Metrics and aggregation for fault-configuration open-set experiments.

The functions in this module consume only frozen final-test predictions.  They
do not fit thresholds or models.  ``unknown`` is always the positive class for
ranking and binary rejection metrics, and larger Open Set scores must mean
"more unknown".
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Hashable, Mapping, Sequence
from typing import Any

import numpy as np
from scipy.stats import t as student_t
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


UNKNOWN_ROLES = frozenset({"unknown", "unknown_fault", "unknown_test", "unknown_validation"})
MAHALANOBIS_NAMES = frozenset({"mahalanobis", "mahalanobis_ledoit_wolf", "maha"})
KNN_NAMES = frozenset({"knn", "k-nn", "k_nn"})

FPR95_INTERPOLATION = "linear_between_adjacent_empirical_roc_points"
OPEN_SET_CLASSIFICATION_FORMULA = (
    "count(known samples with is_unknown=false and predicted_known_class=true_label) "
    "/ count(known samples)"
)

_AGGREGATED_METRICS = {
    "known_classification.accuracy": "higher_is_better",
    "known_classification.balanced_accuracy": "higher_is_better",
    "known_classification.macro_f1": "higher_is_better",
    "known_fault_classification.accuracy": "higher_is_better",
    "known_fault_classification.balanced_accuracy": "higher_is_better",
    "known_fault_classification.macro_f1": "higher_is_better",
    "unknown_rejection.auroc_unknown_positive": "higher_is_better",
    "unknown_rejection.aupr_unknown_positive": "higher_is_better",
    "unknown_rejection.fpr_at_95_tpr": "lower_is_better",
    "unknown_rejection.unknown_precision": "higher_is_better",
    "unknown_rejection.unknown_recall": "higher_is_better",
    "unknown_rejection.unknown_f1": "higher_is_better",
    "known_acceptance_rate": "higher_is_better",
    "open_set_classification_rate": "higher_is_better",
    "healthy_safety.false_positive_rate": "lower_is_better",
    "healthy_safety.acceptance_rate": "higher_is_better",
}


def _stable_labels(values: Sequence[Hashable]) -> list[Hashable]:
    return sorted(set(values), key=lambda value: (str(type(value)), str(value)))


def _json_label(value: Hashable | None) -> str | int | float | bool | None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _finite_score(value: object, *, sample_id: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"prediction {sample_id} has an invalid openset_score") from error
    if not math.isfinite(score):
        raise ValueError(f"prediction {sample_id} has a non-finite openset_score")
    return score


def _unknown_prediction(value: object, *, sample_id: str) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)) and int(value) in {0, 1}:
        return bool(value)
    raise ValueError(f"prediction {sample_id} has a non-binary is_unknown value")


def _normalise_predictions(
    predictions: Sequence[Mapping[str, Any]],
    *,
    unknown_labels: Sequence[Hashable] | None,
    require_unique_sample_ids: bool,
) -> list[dict[str, Any]]:
    if not predictions:
        raise ValueError("predictions must contain at least one final-test sample")
    declared_unknown = set(unknown_labels) if unknown_labels is not None else None
    rows: list[dict[str, Any]] = []
    sample_ids: set[str] = set()
    for index, item in enumerate(predictions):
        sample_id = str(item.get("sample_id") or "")
        if not sample_id:
            raise ValueError(f"prediction at index {index} has no sample_id")
        if require_unique_sample_ids and sample_id in sample_ids:
            raise ValueError(f"duplicate final-test sample_id: {sample_id}")
        sample_ids.add(sample_id)
        if "true_label" not in item or item.get("predicted_known_class") is None:
            raise ValueError(f"prediction {sample_id} lacks true_label or predicted_known_class")
        true_label = item["true_label"]
        role = str(item.get("true_role") or "")
        role_unknown = role in UNKNOWN_ROLES
        if declared_unknown is not None:
            label_unknown = true_label in declared_unknown
            if role and role_unknown != label_unknown:
                raise ValueError(
                    f"prediction {sample_id} has contradictory true_role={role!r} and unknown label membership"
                )
            is_true_unknown = label_unknown
        else:
            if not role:
                raise ValueError(f"prediction {sample_id} needs true_role when unknown_labels is omitted")
            is_true_unknown = role_unknown
        rows.append(
            {
                **dict(item),
                "sample_id": sample_id,
                "true_label": true_label,
                "true_role": role,
                "is_true_unknown": is_true_unknown,
                "openset_score": _finite_score(item.get("openset_score"), sample_id=sample_id),
                "is_unknown": _unknown_prediction(item.get("is_unknown"), sample_id=sample_id),
            }
        )
    return rows


def interpolated_fpr_at_tpr(
    unknown_labels: Sequence[bool | int],
    scores: Sequence[float],
    *,
    target_tpr: float = 0.95,
) -> dict[str, Any]:
    """Return FPR at a target TPR using linear interpolation on the ROC path.

    The empirical ROC curve is evaluated with ``drop_intermediate=False``.
    The first point reaching ``target_tpr`` and its immediately preceding
    point define the interpolation segment.  A single ground-truth class has
    no ROC curve and is reported as unavailable rather than coerced to zero.
    """

    labels = np.asarray(unknown_labels, dtype=int).reshape(-1)
    values = np.asarray(scores, dtype=float).reshape(-1)
    if len(labels) == 0 or len(labels) != len(values):
        raise ValueError("unknown_labels and scores must have equal non-zero length")
    if not np.isfinite(values).all():
        raise ValueError("scores must be finite")
    if not 0.0 < float(target_tpr) <= 1.0:
        raise ValueError("target_tpr must be in (0, 1]")
    if set(np.unique(labels)) - {0, 1}:
        raise ValueError("unknown_labels must be binary")
    if len(np.unique(labels)) < 2:
        return {
            "value": None,
            "status": "unavailable_single_ground_truth_class",
            "target_tpr": float(target_tpr),
            "interpolation": FPR95_INTERPOLATION,
        }

    fpr, tpr, _ = roc_curve(labels, values, pos_label=1, drop_intermediate=False)
    upper = int(np.searchsorted(tpr, float(target_tpr), side="left"))
    if upper >= len(tpr):
        return {
            "value": None,
            "status": "unavailable_target_tpr_not_reached",
            "target_tpr": float(target_tpr),
            "interpolation": FPR95_INTERPOLATION,
        }
    if upper == 0 or tpr[upper] == target_tpr:
        value = float(fpr[upper])
    else:
        lower = upper - 1
        tpr_span = float(tpr[upper] - tpr[lower])
        if tpr_span <= 0:
            value = float(fpr[upper])
        else:
            weight = float((target_tpr - tpr[lower]) / tpr_span)
            value = float(fpr[lower] + weight * (fpr[upper] - fpr[lower]))
    return {
        "value": value,
        "status": "computed",
        "target_tpr": float(target_tpr),
        "interpolation": FPR95_INTERPOLATION,
    }


def _classification_metrics(rows: Sequence[Mapping[str, Any]], labels: Sequence[Hashable]) -> dict[str, Any]:
    label_order = list(labels)
    if not rows:
        return {
            "status": "unavailable_no_samples",
            "n_samples": 0,
            "labels": [_json_label(label) for label in label_order],
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
            "per_class": [],
            "confusion_matrix": [],
            "confusion_matrix_axes": "rows=true_label, columns=predicted_known_class",
        }
    truth = np.asarray([item["true_label"] for item in rows], dtype=object)
    prediction = np.asarray([item["predicted_known_class"] for item in rows], dtype=object)
    precision, recall, f1, support = precision_recall_fscore_support(
        truth,
        prediction,
        labels=label_order,
        zero_division=0,
    )
    # A faulty sample can be predicted healthy: keep that column instead of
    # silently dropping it from the fault-only confusion matrix.
    matrix_labels = list(label_order) + [label for label in _stable_labels(list(prediction)) if label not in label_order]
    matrix = confusion_matrix(truth, prediction, labels=matrix_labels)
    return {
        "status": "computed",
        "n_samples": int(len(rows)),
        "labels": [_json_label(label) for label in label_order],
        "accuracy": float(accuracy_score(truth, prediction)),
        "balanced_accuracy": float(np.mean(recall[support > 0])),
        "macro_f1": float(f1_score(truth, prediction, labels=label_order, average="macro", zero_division=0)),
        "per_class": [
            {
                "label": _json_label(label),
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(label_order)
        ],
        "confusion_matrix": matrix.astype(int).tolist(),
        "confusion_matrix_labels": [_json_label(label) for label in matrix_labels],
        "confusion_matrix_axes": "rows=true_label, columns=predicted_known_class",
    }


def _score_distribution(scores: Sequence[float]) -> dict[str, float | int | None]:
    values = np.asarray(scores, dtype=float)
    if not len(values):
        return {
            "n": 0,
            "mean": None,
            "standard_deviation": None,
            "minimum": None,
            "q05": None,
            "q25": None,
            "median": None,
            "q75": None,
            "q95": None,
            "maximum": None,
        }
    return {
        "n": int(len(values)),
        "mean": float(np.mean(values)),
        "standard_deviation": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "minimum": float(np.min(values)),
        "q05": float(np.quantile(values, 0.05)),
        "q25": float(np.quantile(values, 0.25)),
        "median": float(np.median(values)),
        "q75": float(np.quantile(values, 0.75)),
        "q95": float(np.quantile(values, 0.95)),
        "maximum": float(np.max(values)),
    }


def _unknown_label_analysis(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[Hashable, list[Mapping[str, Any]]] = defaultdict(list)
    for item in rows:
        if item["is_true_unknown"]:
            grouped[item["true_label"]].append(item)
    output: list[dict[str, Any]] = []
    for label in _stable_labels(list(grouped)):
        items = grouped[label]
        attractions = [
            item.get("nearest_known_class")
            if item.get("nearest_known_class") is not None
            else item.get("predicted_known_class")
            for item in items
        ]
        counts = Counter(attractions)
        ordered_counts = sorted(counts.items(), key=lambda pair: (-pair[1], str(pair[0])))
        most_label, most_count = ordered_counts[0]
        output.append(
            {
                "unknown_label": _json_label(label),
                "n_samples": int(len(items)),
                "recall": float(np.mean([item["is_unknown"] for item in items])),
                "score_distribution": _score_distribution([item["openset_score"] for item in items]),
                "most_attracted_known_class": _json_label(most_label),
                "most_attracted_count": int(most_count),
                "most_attracted_share": float(most_count / len(items)),
                "attraction_counts": [
                    {"known_class": _json_label(name), "count": int(count)}
                    for name, count in ordered_counts
                ],
                "attraction_source": "nearest_known_class_else_predicted_known_class",
            }
        )
    return output


def evaluate_fault_type_predictions(
    predictions: Sequence[Mapping[str, Any]],
    *,
    healthy_label: Hashable,
    known_labels: Sequence[Hashable] | None = None,
    unknown_labels: Sequence[Hashable] | None = None,
    known_fault_count: int | None = None,
    require_unique_sample_ids: bool = True,
) -> dict[str, Any]:
    """Evaluate one frozen test split.

    ``predicted_known_class`` is evaluated for every known sample, including a
    sample rejected by the Open Set detector.  This keeps closed-set
    classification ability separate from the accept/reject decision.
    """

    rows = _normalise_predictions(
        predictions,
        unknown_labels=unknown_labels,
        require_unique_sample_ids=require_unique_sample_ids,
    )
    known_rows = [item for item in rows if not item["is_true_unknown"]]
    unknown_rows = [item for item in rows if item["is_true_unknown"]]
    if known_fault_count == 9 and unknown_rows:
        raise ValueError("N=9 is a closed-set baseline and cannot contain unknown-test samples")
    derived_known_labels = _stable_labels([item["true_label"] for item in known_rows])
    class_labels = list(known_labels) if known_labels is not None else derived_known_labels
    if set(derived_known_labels) - set(class_labels):
        raise ValueError("known_labels omits a true known final-test label")
    if healthy_label not in set(class_labels):
        raise ValueError("healthy_label must be included in known_labels")
    known_fault_labels = [label for label in class_labels if label != healthy_label]
    if known_fault_count is not None and known_fault_count != len(known_fault_labels):
        raise ValueError("known_fault_count does not match declared class labels")
    if any(r["predicted_known_class"] not in class_labels for r in rows):
        raise ValueError("classifier prediction is outside known class labels")
    known_fault_rows = [item for item in known_rows if item["true_label"] != healthy_label]

    truth_unknown = np.asarray([int(item["is_true_unknown"]) for item in rows], dtype=int)
    predicted_unknown = np.asarray([int(item["is_unknown"]) for item in rows], dtype=int)
    scores = np.asarray([item["openset_score"] for item in rows], dtype=float)
    no_unknown_positive = not unknown_rows
    if no_unknown_positive:
        ranking = {
            "value": None,
            "status": "unavailable_no_unknown_positives",
            "target_tpr": 0.95,
            "interpolation": FPR95_INTERPOLATION,
        }
        unknown_rejection = {
            "status": "unavailable_no_unknown_positives",
            "positive_class": "unknown",
            "score_direction": "higher_is_more_unknown",
            "n_known": int(len(known_rows)),
            "n_unknown": 0,
            "auroc_unknown_positive": None,
            "aupr_unknown_positive": None,
            "fpr_at_95_tpr": None,
            "fpr_at_95_tpr_status": ranking["status"],
            "fpr_at_95_tpr_interpolation": ranking["interpolation"],
            "unknown_precision": None,
            "unknown_recall": None,
            "unknown_f1": None,
        }
    else:
        ranking = interpolated_fpr_at_tpr(truth_unknown, scores)
        unknown_rejection = {
            "status": "computed",
            "positive_class": "unknown",
            "score_direction": "higher_is_more_unknown",
            "n_known": int(len(known_rows)),
            "n_unknown": int(len(unknown_rows)),
            "auroc_unknown_positive": float(roc_auc_score(truth_unknown, scores)),
            "aupr_unknown_positive": float(average_precision_score(truth_unknown, scores)),
            "fpr_at_95_tpr": ranking["value"],
            "fpr_at_95_tpr_status": ranking["status"],
            "fpr_at_95_tpr_interpolation": ranking["interpolation"],
            "unknown_precision": float(precision_score(truth_unknown, predicted_unknown, zero_division=0)),
            "unknown_recall": float(recall_score(truth_unknown, predicted_unknown, zero_division=0)),
            "unknown_f1": float(f1_score(truth_unknown, predicted_unknown, zero_division=0)),
        }

    accepted_known = [item for item in known_rows if not item["is_unknown"]]
    correctly_classified_and_accepted = [
        item for item in accepted_known if item["predicted_known_class"] == item["true_label"]
    ]
    healthy_rows = [item for item in known_rows if item["true_label"] == healthy_label]
    healthy_false_positives = sum(item["is_unknown"] for item in healthy_rows)
    return {
        "schema_version": 1,
        "status": "completed",
        "n_test_samples": int(len(rows)),
        "known_fault_count": int(known_fault_count) if known_fault_count is not None else len(known_fault_labels),
        "known_classification": _classification_metrics(known_rows, class_labels),
        "known_fault_classification": _classification_metrics(known_fault_rows, known_fault_labels),
        "unknown_rejection": unknown_rejection,
        "known_acceptance_rate": float(len(accepted_known) / len(known_rows)) if known_rows else None,
        "open_set_classification_rate": (
            float(len(correctly_classified_and_accepted) / len(known_rows)) if known_rows else None
        ),
        "open_set_classification_rate_formula": OPEN_SET_CLASSIFICATION_FORMULA,
        "healthy_safety": {
            "status": "computed" if healthy_rows else "unavailable_no_healthy_samples",
            "n_healthy": int(len(healthy_rows)),
            "false_positive_rate": (
                float(healthy_false_positives / len(healthy_rows)) if healthy_rows else None
            ),
            "acceptance_rate": (
                float(1.0 - healthy_false_positives / len(healthy_rows)) if healthy_rows else None
            ),
        },
        "per_unknown_label": _unknown_label_analysis(rows),
    }


def _nested_value(payload: Mapping[str, Any], path: str) -> float | None:
    value: Any = payload
    for part in path.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _mean_ci95(values: Sequence[float]) -> dict[str, Any]:
    finite = np.asarray([float(value) for value in values if math.isfinite(float(value))], dtype=float)
    if not len(finite):
        return {
            "status": "unavailable_no_computable_runs",
            "n": 0,
            "mean": None,
            "standard_deviation": None,
            "ci95_lower": None,
            "ci95_upper": None,
            "ci95_method": "student_t_two_sided_over_runs",
        }
    mean = float(np.mean(finite))
    if len(finite) == 1:
        return {
            "status": "insufficient_runs_for_interval",
            "n": 1,
            "mean": mean,
            "standard_deviation": None,
            "ci95_lower": None,
            "ci95_upper": None,
            "ci95_method": "student_t_two_sided_over_runs",
        }
    standard_deviation = float(np.std(finite, ddof=1))
    half_width = float(student_t.ppf(0.975, len(finite) - 1) * standard_deviation / math.sqrt(len(finite)))
    return {
        "status": "computed",
        "n": int(len(finite)),
        "mean": mean,
        "standard_deviation": standard_deviation,
        "ci95_lower": mean - half_width,
        "ci95_upper": mean + half_width,
        "ci95_method": "student_t_two_sided_over_runs",
    }


def _run_id(run: Mapping[str, Any], index: int) -> str:
    return str(run.get("run_id") or f"run-{index:04d}")


def _canonical_detector(value: object) -> str | None:
    name = str(value or "").lower()
    if name in MAHALANOBIS_NAMES:
        return "mahalanobis"
    if name in KNN_NAMES:
        return "knn"
    return None


def _prediction_sample_ids(run: Mapping[str, Any]) -> set[str] | None:
    predictions = run.get("predictions")
    if predictions is None:
        return None
    return {str(item.get("sample_id")) for item in predictions}


def paired_mahalanobis_knn(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Pair detector runs only when their immutable manifest checksums match."""

    grouped: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    ignored: list[dict[str, Any]] = []
    for index, run in enumerate(runs):
        run_id = _run_id(run, index)
        if run.get("status", "completed") != "completed":
            ignored.append({"run_id": run_id, "reason": "run_not_completed"})
            continue
        detector = _canonical_detector(run.get("openset_method") or run.get("method"))
        if detector is None:
            ignored.append({"run_id": run_id, "reason": "detector_not_mahalanobis_or_knn"})
            continue
        checksum = str(run.get("manifest_checksum") or "")
        if not checksum:
            ignored.append({"run_id": run_id, "reason": "missing_manifest_checksum"})
            continue
        if detector in grouped[checksum]:
            raise ValueError(f"duplicate {detector} run for manifest checksum {checksum}")
        grouped[checksum][detector] = run

    pairs: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for checksum in sorted(grouped):
        methods = grouped[checksum]
        if set(methods) != {"mahalanobis", "knn"}:
            unmatched.append({"manifest_checksum": checksum, "available_methods": sorted(methods)})
            continue
        mahalanobis_ids = _prediction_sample_ids(methods["mahalanobis"])
        knn_ids = _prediction_sample_ids(methods["knn"])
        if mahalanobis_ids is not None or knn_ids is not None:
            if mahalanobis_ids is None or knn_ids is None or mahalanobis_ids != knn_ids:
                raise ValueError(f"paired detector sample IDs differ for manifest checksum {checksum}")
        else:
            left = methods["mahalanobis"].get("test_sample_ids_sha256")
            right = methods["knn"].get("test_sample_ids_sha256")
            if not left or not right or left != right:
                raise ValueError(f"paired detector sample IDs digest missing or different for manifest checksum {checksum}")
        differences: dict[str, float] = {}
        for path in _AGGREGATED_METRICS:
            mahalanobis_value = _nested_value(methods["mahalanobis"].get("metrics", {}), path)
            knn_value = _nested_value(methods["knn"].get("metrics", {}), path)
            if mahalanobis_value is not None and knn_value is not None:
                differences[path] = knn_value - mahalanobis_value
        pairs.append(
            {
                "manifest_checksum": checksum,
                "mahalanobis_run_id": str(methods["mahalanobis"].get("run_id") or ""),
                "knn_run_id": str(methods["knn"].get("run_id") or ""),
                "difference_direction": "knn_minus_mahalanobis",
                "metric_differences": differences,
            }
        )
    aggregate = {
        path: {
            **_mean_ci95([pair["metric_differences"][path] for pair in pairs if path in pair["metric_differences"]]),
            "metric_direction": direction,
            "difference_direction": "knn_minus_mahalanobis",
        }
        for path, direction in _AGGREGATED_METRICS.items()
    }
    return {
        "status": "computed" if pairs else "unavailable_no_shared_manifest_checksum",
        "pairing_key": "manifest_checksum",
        "same_test_sample_ids_verified_when_predictions_present": True,
        "n_pairs": int(len(pairs)),
        "pairs": pairs,
        "aggregate": aggregate,
        "unmatched_manifests": unmatched,
        "ignored_runs": ignored,
    }


def aggregate_fault_type_runs(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate all declared runs using equal-run macro and pooled-sample views."""

    if not runs:
        raise ValueError("runs must contain at least one declared run")
    protocols = {r.get("protocol") for r in runs if r.get("status", "completed") == "completed" and r.get("protocol") is not None}
    if len(protocols) > 1:
        raise ValueError("Protocol A and B must never be aggregated together")
    completed: list[Mapping[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for index, run in enumerate(runs):
        run_id = _run_id(run, index)
        if run.get("status", "completed") != "completed":
            failed.append(
                {
                    "run_id": run_id,
                    "status": str(run.get("status")),
                    "reason": str(run.get("reason") or "unspecified"),
                }
            )
            continue
        if not isinstance(run.get("metrics"), Mapping):
            raise ValueError(f"completed run {run_id} has no metrics")
        if not isinstance(run.get("predictions"), Sequence) or not run.get("predictions"):
            raise ValueError(f"completed run {run_id} has no per-sample predictions")
        completed.append(run)
    if not completed:
        raise ValueError("no completed runs are available for aggregation")

    macro = {
        path: {
            **_mean_ci95(
                [value for run in completed if (value := _nested_value(run["metrics"], path)) is not None]
            ),
            "metric_direction": direction,
        }
        for path, direction in _AGGREGATED_METRICS.items()
    }
    healthy_labels = {run.get("healthy_label") for run in completed}
    if None in healthy_labels or len(healthy_labels) != 1:
        raise ValueError("all completed runs must declare the same healthy_label")
    pooled_predictions: list[dict[str, Any]] = []
    for index, run in enumerate(completed):
        run_id = _run_id(run, index)
        for item in run["predictions"]:
            pooled_predictions.append({**dict(item), "sample_id": f"{run_id}::{item.get('sample_id')}"})
    pooled = evaluate_fault_type_predictions(
        pooled_predictions,
        healthy_label=next(iter(healthy_labels)),
        require_unique_sample_ids=True,
    )

    unknown_by_label: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for run in completed:
        for row in run["metrics"].get("per_unknown_label", []):
            unknown_by_label[str(row["unknown_label"])].append(row)
    per_unknown_macro = []
    for label in sorted(unknown_by_label):
        items = unknown_by_label[label]
        per_unknown_macro.append(
            {
                "unknown_label": label,
                "runs_present": len(items),
                "recall": _mean_ci95([float(item["recall"]) for item in items]),
                "mean_score": _mean_ci95(
                    [float(item["score_distribution"]["mean"]) for item in items]
                ),
                "most_attracted_share": _mean_ci95(
                    [float(item["most_attracted_share"]) for item in items]
                ),
            }
        )
    return {
        "schema_version": 1,
        "status": "completed",
        "declared_runs": int(len(runs)),
        "completed_runs": int(len(completed)),
        "failed_runs": failed,
        "uncertainty_scope": "descriptive across overlapping class combinations and campaign folds; not independent physical motors",
        "macro_over_splits": {
            "weighting": "each completed run has equal weight",
            "metrics": macro,
            "per_unknown_label": per_unknown_macro,
        },
        "pooled_sample": {
            "weighting": "each final-test prediction has equal weight; larger splits contribute more; reused source samples across combinations are repeated, not independent observations",
            "metrics": pooled,
        },
        "paired_detector_comparison": paired_mahalanobis_knn(runs),
    }


# Short aliases for callers that already provide fault-type prediction rows.
evaluate_predictions = evaluate_fault_type_predictions
aggregate_runs = aggregate_fault_type_runs
paired_detector_comparison = paired_mahalanobis_knn
