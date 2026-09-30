import unittest
import numpy as np
from core.fault_type_source_audit import recover_row_mapping


class MappingTests(unittest.TestCase):
    def test_unique_filtered_rows(self):
        raw = np.arange(12.).reshape(4, 3)
        result = recover_row_mapping(raw[[0, 3]], raw)
        self.assertEqual(result["unique_matches"], 2)
        self.assertEqual(result["mapping"][1]["processed_window_ordinal"], 3)
        self.assertIsNone(result["raw_source_intervals"])

    def test_duplicate_ambiguous_not_fabricated(self):
        result = recover_row_mapping([[1, 2]], [[1, 2], [1, 2]])
        self.assertEqual(result["unique_matches"], 0)
        self.assertEqual(len(result["ambiguous_rows"]), 1)

    def test_changed_row_not_mapped(self):
        result = recover_row_mapping([[1, 3]], [[1, 2]])
        self.assertEqual(result["unmatched_rows"], [0])
