import unittest
from core.fault_type_provenance import documented_motor, evidence


class EvidenceTests(unittest.TestCase):
    def test_documented_identity_not_serial(self):
        result = documented_motor("T2", "2", {"commit": "pinned"})
        self.assertEqual(result["documented_motor_id"]["value"], "T2")
        self.assertEqual(result["age_description"]["value"], "old")
        self.assertIsNone(result["serial_number"]["value"])

    def test_mapping_conflict_rejected(self):
        with self.assertRaises(ValueError):
            documented_motor("T2", "1", {"commit": "pinned"})

    def test_no_fabricated_unknown_or_unsourced_claim(self):
        with self.assertRaises(ValueError):
            evidence("session1", "unknown", [])
        with self.assertRaises(ValueError):
            evidence("session1", "artifact", [])
