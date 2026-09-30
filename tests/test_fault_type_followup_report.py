import copy
import unittest
from experiments.fault_type_followup_report import paired_differences


class PairedTests(unittest.TestCase):
    def fixture(self):
        return [{"classifier": "linear_baseline", "seed": seed, "method": method,
            "manifest_checksum": str(seed), "test_ids_checksum": "same",
            "metrics": {"unknown_rejection": {"auroc_unknown_positive": .6 if method == "knn" else .5,
                "unknown_recall": .1}, "healthy_safety": {"false_positive_rate": .05}}}
            for seed in (42, 123, 2026) for method in ("mahalanobis", "knn")]

    def test_native_metric_keys_and_pair_direction(self):
        pairs = paired_differences(self.fixture())
        self.assertEqual(len(pairs), 3)
        self.assertAlmostEqual(pairs[0]["unknown_auroc_delta"], .1)

    def test_pair_mismatch_rejected(self):
        rows = self.fixture(); rows[0]["test_ids_checksum"] = "changed"
        with self.assertRaises(ValueError): paired_differences(rows)
