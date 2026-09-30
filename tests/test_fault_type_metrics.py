import copy
import unittest

from experiments.fault_type_metrics import (
    FPR95_INTERPOLATION,
    aggregate_fault_type_runs,
    evaluate_fault_type_predictions,
    interpolated_fpr_at_tpr,
    paired_mahalanobis_knn,
)


def _predictions():
    return [
        {"sample_id": "h1", "true_label": "healthy", "true_role": "healthy", "predicted_known_class": "healthy", "openset_score": 0.10, "is_unknown": False, "nearest_known_class": "healthy"},
        {"sample_id": "h2", "true_label": "healthy", "true_role": "healthy", "predicted_known_class": "fault-a", "openset_score": 0.90, "is_unknown": True, "nearest_known_class": "fault-a"},
        {"sample_id": "a1", "true_label": "fault-a", "true_role": "known_fault", "predicted_known_class": "fault-a", "openset_score": 0.20, "is_unknown": False, "nearest_known_class": "fault-a"},
        {"sample_id": "a2", "true_label": "fault-a", "true_role": "known_fault", "predicted_known_class": "healthy", "openset_score": 0.30, "is_unknown": False, "nearest_known_class": "healthy"},
        {"sample_id": "b1", "true_label": "fault-b", "true_role": "unknown_test", "predicted_known_class": "fault-a", "openset_score": 0.40, "is_unknown": False, "nearest_known_class": "fault-a"},
        {"sample_id": "b2", "true_label": "fault-b", "true_role": "unknown_test", "predicted_known_class": "healthy", "openset_score": 0.80, "is_unknown": True, "nearest_known_class": "healthy"},
        {"sample_id": "c1", "true_label": "fault-c", "true_role": "unknown_test", "predicted_known_class": "fault-a", "openset_score": 0.95, "is_unknown": True, "nearest_known_class": "fault-a"},
        {"sample_id": "c2", "true_label": "fault-c", "true_role": "unknown_test", "predicted_known_class": "fault-a", "openset_score": 0.99, "is_unknown": True, "nearest_known_class": "fault-a"},
    ]


def _metrics(predictions=None):
    return evaluate_fault_type_predictions(
        predictions or _predictions(),
        healthy_label="healthy",
        known_labels=["healthy", "fault-a"],
        unknown_labels=["fault-b", "fault-c"],
        known_fault_count=1,
    )


class FaultTypeMetricTests(unittest.TestCase):
    def test_reports_classification_rejection_safety_and_unknown_attraction(self):
        result = _metrics()

        self.assertEqual(result["known_classification"]["confusion_matrix"], [[1, 1], [1, 1]])
        self.assertEqual(result["known_classification"]["accuracy"], 0.5)
        self.assertEqual(result["known_classification"]["balanced_accuracy"], 0.5)
        self.assertEqual(result["known_classification"]["macro_f1"], 0.5)
        self.assertEqual(result["known_acceptance_rate"], 0.75)
        self.assertEqual(result["open_set_classification_rate"], 0.5)
        self.assertIn("count(known samples", result["open_set_classification_rate_formula"])
        self.assertEqual(result["healthy_safety"]["false_positive_rate"], 0.5)
        self.assertEqual(result["healthy_safety"]["acceptance_rate"], 0.5)
        self.assertEqual(result["unknown_rejection"]["unknown_precision"], 0.75)
        self.assertEqual(result["unknown_rejection"]["unknown_recall"], 0.75)
        self.assertEqual(result["unknown_rejection"]["unknown_f1"], 0.75)
        self.assertEqual(result["unknown_rejection"]["fpr_at_95_tpr_interpolation"], FPR95_INTERPOLATION)

        per_unknown = {row["unknown_label"]: row for row in result["per_unknown_label"]}
        self.assertEqual(per_unknown["fault-b"]["recall"], 0.5)
        self.assertEqual(per_unknown["fault-c"]["recall"], 1.0)
        self.assertEqual(per_unknown["fault-c"]["most_attracted_known_class"], "fault-a")
        self.assertEqual(per_unknown["fault-c"]["score_distribution"]["n"], 2)

    def test_nine_known_faults_suppresses_metrics_that_need_unknown_positives(self):
        rows = [
            {"sample_id": "h", "true_label": "healthy", "true_role": "healthy", "predicted_known_class": "healthy", "openset_score": 0.1, "is_unknown": False},
            {"sample_id": "f", "true_label": "fault-1", "true_role": "known_fault", "predicted_known_class": "fault-1", "openset_score": 0.2, "is_unknown": False},
        ]
        rows.extend({"sample_id": f"f-{i}", "true_label": f"fault-{i}", "true_role": "known_fault", "predicted_known_class": f"fault-{i}", "openset_score": .2, "is_unknown": False} for i in range(2, 10))
        result = evaluate_fault_type_predictions(
            rows,
            healthy_label="healthy",
            known_labels=["healthy", *[f"fault-{i}" for i in range(1, 10)]],
            known_fault_count=9,
        )

        rejection = result["unknown_rejection"]
        self.assertEqual(rejection["status"], "unavailable_no_unknown_positives")
        for name in ("auroc_unknown_positive", "aupr_unknown_positive", "fpr_at_95_tpr", "unknown_precision", "unknown_recall", "unknown_f1"):
            self.assertIsNone(rejection[name])
        self.assertEqual(result["known_classification"]["accuracy"], 1.0)

    def test_fpr95_records_interpolation_and_rejects_single_class(self):
        computed = interpolated_fpr_at_tpr(
            [0, 0, 1, 1, 1, 1],
            [0.9, 0.1, 0.8, 0.7, 0.6, 0.05],
        )
        self.assertEqual(computed["status"], "computed")
        self.assertEqual(computed["interpolation"], FPR95_INTERPOLATION)
        # The final positive scores 0.05, below both negatives (0.9, 0.1).
        # Between TPR=.75 and 1.0 FPR is already 1.0, not .5.
        self.assertAlmostEqual(computed["value"], 1.0)

        unavailable = interpolated_fpr_at_tpr([0, 0], [0.1, 0.2])
        self.assertIsNone(unavailable["value"])
        self.assertEqual(unavailable["status"], "unavailable_single_ground_truth_class")

    def test_aggregate_has_macro_pooled_ci_failed_runs_and_same_manifest_pairs(self):
        predictions_a = _predictions()
        predictions_b = copy.deepcopy(predictions_a)
        predictions_b[0]["predicted_known_class"] = "fault-a"
        metrics_a = _metrics(predictions_a)
        metrics_b = _metrics(predictions_b)
        runs = [
            {"run_id": "m-a", "status": "completed", "manifest_checksum": "same", "openset_method": "mahalanobis", "healthy_label": "healthy", "metrics": metrics_a, "predictions": predictions_a},
            {"run_id": "k-a", "status": "completed", "manifest_checksum": "same", "openset_method": "knn", "healthy_label": "healthy", "metrics": metrics_b, "predictions": predictions_b},
            {"run_id": "m-unpaired", "status": "completed", "manifest_checksum": "other", "openset_method": "mahalanobis", "healthy_label": "healthy", "metrics": metrics_a, "predictions": predictions_a},
            {"run_id": "failed", "status": "failed", "reason": "fixture failure", "manifest_checksum": "failed-checksum", "openset_method": "knn"},
        ]

        result = aggregate_fault_type_runs(runs)
        accuracy = result["macro_over_splits"]["metrics"]["known_classification.accuracy"]
        self.assertEqual(accuracy["n"], 3)
        self.assertEqual(accuracy["status"], "computed")
        self.assertIsNotNone(accuracy["ci95_lower"])
        self.assertEqual(result["pooled_sample"]["metrics"]["n_test_samples"], 24)
        self.assertEqual(result["failed_runs"], [{"run_id": "failed", "status": "failed", "reason": "fixture failure"}])
        paired = result["paired_detector_comparison"]
        self.assertEqual(paired["n_pairs"], 1)
        self.assertEqual(paired["pairs"][0]["manifest_checksum"], "same")
        self.assertEqual(paired["unmatched_manifests"], [{"manifest_checksum": "other", "available_methods": ["mahalanobis"]}])

    def test_pairing_refuses_different_sample_sets_even_with_same_checksum(self):
        predictions = _predictions()
        other = copy.deepcopy(predictions)
        other[-1]["sample_id"] = "different"
        runs = [
            {"run_id": "m", "manifest_checksum": "checksum", "openset_method": "mahalanobis", "metrics": _metrics(predictions), "predictions": predictions},
            {"run_id": "k", "manifest_checksum": "checksum", "openset_method": "knn", "metrics": _metrics(other), "predictions": other},
        ]
        with self.assertRaisesRegex(ValueError, "sample IDs differ"):
            paired_mahalanobis_knn(runs)

    def test_fault_only_confusion_does_not_drop_healthy_predictions(self):
        result = _metrics()["known_fault_classification"]
        self.assertEqual(sum(map(sum, result["confusion_matrix"])), result["n_samples"])
        self.assertIn("healthy", result["confusion_matrix_labels"])

    def test_protocols_cannot_be_mixed_and_count_cannot_be_faked(self):
        with self.assertRaisesRegex(ValueError, "must never"):
            aggregate_fault_type_runs([{"protocol": "A"}, {"protocol": "B"}])
        with self.assertRaisesRegex(ValueError, "does not match"):
            evaluate_fault_type_predictions(_predictions()[:4], healthy_label="healthy", known_fault_count=9)


if __name__ == "__main__":
    unittest.main()
