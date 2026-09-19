import unittest

import numpy as np

from health.sensor_quality import assess_sensor_window


class SensorQualityTests(unittest.TestCase):
    def test_clean_window_is_valid(self):
        report = assess_sensor_window(np.ones((20, 2)) + np.arange(40).reshape(20, 2) * 0.01)
        self.assertEqual(report.action, "diagnose_motor")
        self.assertEqual(report.status, "valid")

    def test_missing_flatline_and_gap_are_sensor_warning(self):
        values = np.ones((20, 3))
        values[2, 0] = np.nan
        report = assess_sensor_window(values, timestamps=[0.0, 1.0] + list(np.arange(2, 20) + 5.0), expected_interval=1.0)
        self.assertEqual(report.action, "sensor_warning")
        self.assertIn("missing_or_nonfinite", report.issues)
        self.assertIn("timestamp_gap", report.issues)


if __name__ == "__main__":
    unittest.main()
