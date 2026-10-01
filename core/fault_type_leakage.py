"""Read-only independence diagnostics; matches are not hardware provenance.

Uses the existing validator and numeric exposure digest. No new class split,
deduplication, thresholds, model fitting, or independence-standard relaxation.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import numpy as np
from core.fault_type_final_guard import digest, numeric_row_digest


def numeric_duplicates(records, values):
    values = np.asarray(values, dtype=float)
    if values.shape != (len(records), 105) or not np.isfinite(values).all():
        raise ValueError("finite catalog-aligned105 features required")
    exact, semantic = defaultdict(list), defaultdict(list)
    for record, row in zip(records, values):
        # IEEE signed zeros compare numerically equal; canonicalize only for
        # this exact-numeric diagnostic, never change saved features/ledger.
        canonical = np.asarray(row, dtype="<f8").copy()
        canonical[canonical == 0] = 0.0
        exact[hashlib.sha256(canonical.tobytes()).hexdigest()].append(record)
        semantic[numeric_row_digest(row)].append(record)

    def summarize(groups):
        repeated = {key: members for key, members in groups.items() if len(members) > 1}
        return {
            "unique_digests": len(groups), "duplicate_groups": len(repeated),
            "rows_in_duplicate_groups": sum(len(v) for v in repeated.values()),
            "cross_motor_groups": sum(len({r.get("t_code") for r in v}) > 1 for v in repeated.values()),
            "cross_label_groups": sum(len({r["label"] for r in v}) > 1 for v in repeated.values()),
            "examples": [{"digest": k, "sample_ids": sorted(r["sample_id"] for r in v),
                "labels": sorted({r["label"] for r in v}), "sources": sorted({r["source_file"] for r in v})}
                for k, v in sorted(repeated.items())[:20]],
        }
    return {"exact_numeric": summarize(exact), "semantic_12g": summarize(semantic),
            "limitation": "Equal105-vectors flag possible copies, not proof of the same physical acquisition; no near-copy/transform exclusion guarantee."}, semantic


def selection_dependency(manifests, *, selection_by_fold=None, global_choice=True):
    """Audit the selector's actual dependency, not ordinary CV train reuse.

    For a single global choice made from all folds' validation scores, every
    outer test must be disjoint from the UNION of those selection inputs.
    This is separate from correct within-fold train-only estimator fitting.
    """
    if selection_by_fold is None:
        selection_by_fold = {m["fold_id"]: set(m["sample_ids"]["validation"]) for m in manifests}
    selected = {key: set(ids) for key, ids in selection_by_fold.items()}
    union = set().union(*selected.values()) if selected else set()
    rows = []
    for m in manifests:
        test = set(m["sample_ids"]["test"])
        own = selected[m["fold_id"]]
        effective = union if global_choice else own
        shared = test & effective
        rows.append({"fold_id": m["fold_id"], "test_count": len(test),
            "own_fold_selection_overlap": len(test & own),
            "effective_selection_test_overlap": len(shared),
            "overlap_ids_checksum": digest(sorted(shared)),
            "overlap_examples": sorted(shared)[:5]})
    return {"selector": "global_choice_from_all_fold_validation" if global_choice else "fold_local_choice",
        "selection_ids": len(union), "selection_ids_checksum": digest(sorted(union)),
        "folds": rows,
        "status": "NOT_INDEPENDENT_FOR_GLOBAL_SELECTION" if any(r["effective_selection_test_overlap"] for r in rows)
                  else "NO_RECORDED_SELECTION_TEST_ID_OVERLAP",
        "limitation": "No-ID-overlap is not proof of session, raw-window or acquisition independence."}


def audit_fit_ids(audits, manifests):
    by_fold = {m["fold_id"]: m for m in manifests}
    checks = []
    for audit in audits:
        m = by_fold[audit["fold_id"]]
        parts = {key: set(value) for key, value in m["sample_ids"].items()}
        by_id = {r["sample_id"]: r for r in m["records"]}
        known = {m["healthy_label"], *m["known_fault_labels"]}
        problems = []
        for key, part in (("train_only_transform_fit_ids", "train"), ("classifier_fit_ids", "train"),
                          ("reference_ids", "train"), ("selection_ids", "validation"),
                          ("calibration_ids", "calibration")):
            ids = list(audit.get(key, []))
            if len(ids) != len(set(ids)) or set(ids) != parts[part]:
                problems.append(f"{key}: input IDs do not exactly match {part}")
            if any(by_id.get(sid, {}).get("label") not in known for sid in ids):
                problems.append(f"{key}: unknown/unbound label")
            if set(ids) & parts["test"]:
                problems.append(f"{key}: within-fold test input")
        checks.append({"fold_id": m["fold_id"], "representation": audit["representation"],
                       "status": "FAIL" if problems else "PASS", "problems": problems})
    expected = {(m["fold_id"], name) for m in manifests for name in
                ("baseline105", "vibration75", "current15", "delta_t15", "vibration_current90", "train_pca20")}
    identities = [(a["fold_id"], a["representation"]) for a in audits]
    complete = len(identities) == len(set(identities)) and set(identities) == expected
    return {"status": "PASS" if complete and all(c["status"] == "PASS" for c in checks) else "FAIL",
            "complete_18_fit_inventory": complete, "checks": checks,
            "evidence_level": "saved_execution_ID_audit_and_current_code_flow; not independent instrumentation of historical execution"}


def paired_saved_metrics(verified):
    summaries = {r["representation"]: r for r in verified["representations"]}
    baseline, selected = summaries["baseline105"], summaries[verified["selected_before_test"]]
    metrics = []
    for key in ("accuracy", "balanced_accuracy", "macro_f1"):
        before = baseline["known"][key]["equal_fold_mean"]
        after = selected["known"][key]["equal_fold_mean"]
        metrics.append({"metric": key, "baseline105": before, "selected": after, "difference": after-before})
    detectors = []
    for method in ("mahalanobis", "knn"):
        left = next(d for d in baseline["detectors"] if d["method"] == method)
        right = next(d for d in selected["detectors"] if d["method"] == method)
        detectors.append({"method": method, "metrics": [{"metric": key,
            "baseline105": left["unknown"][key]["equal_fold_mean"],
            "selected": right["unknown"][key]["equal_fold_mean"],
            "difference": right["unknown"][key]["equal_fold_mean"]-left["unknown"][key]["equal_fold_mean"]}
            for key in ("auroc_unknown_positive", "unknown_recall", "unknown_f1", "fpr_at_95_tpr")],
            "healthy_fpr_baseline": left["healthy_fpr_equal_fold_mean"],
            "healthy_fpr_selected": right["healthy_fpr_equal_fold_mean"]})
    return {"same_condition_pairing_verified": True, "selected": verified["selected_before_test"],
        "known_metrics": metrics, "detectors": detectors,
        "guard_only_fix_performance_change": 0.0,
        "scope": "EXPLORATORY; saved predictions recomputed, no model refit/reselection or new test exposure",
        "limitation": "Cross-fold global selection depends on known rows of outer test; selected-vs-baseline difference is descriptive, not unbiased final improvement."}
