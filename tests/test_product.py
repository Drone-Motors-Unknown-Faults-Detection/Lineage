import unittest

from health.product import ExperimentReport, HumanAnnotation, ProductSchemaError, RollbackGuard
from health.stream import CsvReplayAdapter, StreamPacket


class ProductTests(unittest.TestCase):
    def test_rollback_guard_blocks_forgetting(self):
        decision = RollbackGuard(max_forgetting=0.05).evaluate(
            {"old_class_macro_f1": 0.9, "healthy_false_positive_rate": 0.01},
            {"old_class_macro_f1": 0.8, "healthy_false_positive_rate": 0.01},
            rollback_pointer="v1",
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.rollback_pointer, "v1")

    def test_failed_report_requires_error(self):
        with self.assertRaises(ProductSchemaError):
            ExperimentReport("r", "s", 42, "c", {}, {}, "failed", "raw_105d")

    def test_csv_and_live_packet_shape_are_shared(self):
        adapter = CsvReplayAdapter([StreamPacket(1.0, "M1", "S1", (1.0, 2.0), "fixture")])
        packet = next(iter(adapter))
        self.assertEqual(packet.motor_id, "M1")
        self.assertEqual(adapter.stats.emitted, 1)

    def test_annotation_action_is_explicit(self):
        annotation = HumanAnnotation("e1", "confirm", "operator", "2026-09-20T10:00:00Z")
        self.assertEqual(annotation.action, "confirm")


if __name__ == "__main__":
    unittest.main()
