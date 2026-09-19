import tempfile
import unittest
from pathlib import Path

from core.field_data import FieldDataError, validate_field_records, write_field_manifest


def _record(**overrides):
    value = {
        "motor_id": "M1",
        "session_id": "S1",
        "timestamp": "2026-09-20T10:00:00+08:00",
        "screw_position": "A1",
        "measured_torque_nm": 0.8,
        "rpm": 8000,
        "load": 1.0,
        "temperature_c": 25.0,
        "voltage_v": 16.0,
        "current_a": 2.0,
        "sensor_quality": "valid",
        "operator": "operator-1",
        "maintenance_action": "none",
        "source_file": "candidate/M1/S1.csv",
    }
    value.update(overrides)
    return value


class FieldDataTests(unittest.TestCase):
    def test_metadata_manifest_is_validated_and_written(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = write_field_manifest([_record()], Path(temp) / "manifest.json")
            self.assertEqual(manifest["status"], "validated_metadata_only")

    def test_missing_or_duplicate_metadata_is_rejected(self):
        invalid = _record()
        invalid.pop("operator")
        with self.assertRaises(FieldDataError):
            validate_field_records([invalid])
        with self.assertRaises(FieldDataError):
            validate_field_records([_record(), _record()])


if __name__ == "__main__":
    unittest.main()
