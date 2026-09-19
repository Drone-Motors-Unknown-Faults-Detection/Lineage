import unittest

import numpy as np

from health.thresholds import (
    AlarmPolicy,
    ConditionAwareCalibrator,
    ConformalCalibrator,
    apply_alarm_policy,
    independent_percentile,
)


class ThresholdTests(unittest.TestCase):
    def test_independent_percentile_is_fit_only_on_calibration(self):
        result = independent_percentile([1.0, 2.0, 3.0, 4.0], quantile=0.95)
        self.assertAlmostEqual(result.threshold, 3.85)
        self.assertEqual(result.n_calibration, 4)

    def test_conformal_p_values_are_bounded_and_ties_are_reproducible(self):
        calibrator = ConformalCalibrator.fit([1.0, 2.0, 3.0], alpha=0.05)
        first = calibrator.p_values([3.0, 10.0])
        second = calibrator.p_values([3.0, 10.0])
        np.testing.assert_array_equal(first, second)
        self.assertTrue(np.all((first >= 0.0) & (first <= 1.0)))
        self.assertEqual(first[0], 0.5)

    def test_condition_fallback_exact_coarse_global(self):
        calibrator = ConditionAwareCalibrator.fit(
            {"T1|8000rpm": np.arange(20.0), "T2": np.arange(3.0) + 100.0},
            min_samples=10,
        )
        threshold, scope = calibrator.transform([5.0, 5.0, 5.0], ["T1|8000rpm|hot", "T1|6000rpm", "T2|hot"])
        self.assertEqual(scope, ("T1|8000rpm", "global", "global"))
        self.assertGreater(threshold[2], threshold[0])

    def test_event_policies_suppress_single_spike(self):
        scores = np.array([0.2, 1.4, 0.2, 1.4, 1.4, 1.4, 0.2])
        single = apply_alarm_policy(scores, 1.0, AlarmPolicy(kind="single"))
        consecutive = apply_alarm_policy(scores, 1.0, AlarmPolicy(kind="consecutive", consecutive=2))
        ratio = apply_alarm_policy(scores, 1.0, AlarmPolicy(kind="k_of_n", window=3, required=2))
        np.testing.assert_array_equal(single, [False, True, False, True, True, True, False])
        np.testing.assert_array_equal(consecutive, [False, False, False, False, True, True, False])
        np.testing.assert_array_equal(ratio, [False, False, False, True, True, True, True])

    def test_hysteresis_requires_exit_line(self):
        scores = [0.9, 1.2, 1.05, 0.95, 0.85]
        alarms = apply_alarm_policy(scores, 1.0, AlarmPolicy(kind="hysteresis", enter_threshold=1.1, exit_threshold=0.9))
        np.testing.assert_array_equal(alarms, [False, True, True, True, False])


if __name__ == "__main__":
    unittest.main()
