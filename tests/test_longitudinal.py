import unittest

from health.longitudinal import LongitudinalDataError, LongitudinalObservation, validate_trajectories


def _row(**overrides):
    payload = {
        "motor_id": "T1",
        "session_id": "S1",
        "timestamp": "2026-09-20T10:00:00+08:00",
        "cumulative_operating_hours": 1.0,
        "rpm": 8000,
        "load": 1.0,
        "temperature_c": 25,
        "voltage_v": 16,
        "current_a": 2,
        "health_deviation_score": 0.1,
        "unknown_score": 0.0,
        "direction_familiarity": 0.0,
        "inspection_result": "healthy",
        "maintenance_event": "none",
        "part_replacement": "none",
    }
    payload.update(overrides)
    return LongitudinalObservation(**payload)


class LongitudinalTests(unittest.TestCase):
    def test_t1_t2_t3_are_separate_trajectories(self):
        result = validate_trajectories([_row(motor_id="T1"), _row(motor_id="T2"), _row(motor_id="T3")])
        self.assertEqual(result["motor_count"], 3)
        self.assertIn("never concatenated", result["stitched_motor_policy"])

    def test_rul_requires_failure_endpoint(self):
        with self.assertRaises(LongitudinalDataError):
            _row(estimated_rul=10.0)


if __name__ == "__main__":
    unittest.main()
