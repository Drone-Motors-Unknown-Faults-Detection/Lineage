import unittest

import numpy as np

from experiments.field_scenarios import _purity, _sensor_scenarios, _transient_persistent


class FieldScenarioTests(unittest.TestCase):
    def test_cluster_purity_is_bounded(self):
        purity = _purity(np.array([0, 0, 1, 1]), np.array(["a", "a", "b", "b"]))
        self.assertEqual(purity, 1.0)

    def test_sensor_scenarios_and_transient_policy_are_reported(self):
        sensors = _sensor_scenarios()
        self.assertEqual(sensors["clean"]["action"], "diagnose_motor")
        self.assertEqual(sensors["missing_points"]["action"], "sensor_warning")
        self.assertIn("timestamp_gap", sensors["timestamp_gap"]["issues"])
        self.assertIn("missing_or_nonfinite", sensors["dropout"]["issues"])
        events = _transient_persistent()
        self.assertGreater(events["single_spike"]["false_alarm_events"], 0)
        self.assertEqual(events["single_spike_consecutive"]["false_alarm_events"], 0)
        self.assertEqual(events["persistent_event"]["event_unknown_recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
