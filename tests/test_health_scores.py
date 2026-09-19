import unittest

import numpy as np

from health.index import CalibratedHealthIndex
from health.scores import DirectionFamiliarity, FixedHealthReference


class HealthScoreSeparationTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(11)
        self.healthy_train = rng.normal(0.0, 0.2, size=(80, 5))
        self.healthy_cal = rng.normal(0.0, 0.2, size=(30, 5))
        self.fault_train = rng.normal(2.0, 0.2, size=(40, 5))
        self.fault_cal = rng.normal(2.0, 0.2, size=(20, 5))
        self.probe = self.fault_cal[:3]

    def test_health_reference_is_unchanged_when_new_class_is_learned(self):
        before = CalibratedHealthIndex.fit(
            self.healthy_train,
            np.zeros(len(self.healthy_train), dtype=int),
            self.healthy_cal,
            np.zeros(len(self.healthy_cal), dtype=int),
        )
        after = CalibratedHealthIndex.fit(
            np.vstack([self.healthy_train, self.fault_train]),
            np.concatenate([np.zeros(len(self.healthy_train), dtype=int), np.ones(len(self.fault_train), dtype=int)]),
            np.vstack([self.healthy_cal, self.fault_cal]),
            np.concatenate([np.zeros(len(self.healthy_cal), dtype=int), np.ones(len(self.fault_cal), dtype=int)]),
        )
        before_results = before.predict(self.probe, condition="T1/8000rpm")
        after_results = after.predict(self.probe, condition="T1/8000rpm")
        np.testing.assert_allclose(
            [item.health_deviation_score for item in before_results],
            [item.health_deviation_score for item in after_results],
            rtol=1e-10,
            atol=1e-10,
        )
        self.assertTrue(all(item.health_reference_version == "healthy-reference-v1" for item in after_results))
        self.assertTrue(all(item.unknown_score is not None for item in before_results))
        self.assertLess(np.mean([item.unknown_score for item in after_results]), np.mean([item.unknown_score for item in before_results]))

    def test_direction_familiarity_is_separate_from_radius(self):
        reference = FixedHealthReference.fit(self.healthy_train, self.healthy_cal)
        model = DirectionFamiliarity.fit(
            np.vstack([self.healthy_train, self.fault_train]),
            np.concatenate([np.zeros(len(self.healthy_train), dtype=int), np.ones(len(self.fault_train), dtype=int)]),
            reference,
            label_names={1: "fault-A"},
        )
        familiarity, names = model.score(self.probe, reference)
        self.assertTrue(np.all((familiarity >= 0.0) & (familiarity <= 1.0)))
        self.assertEqual(set(names), {"fault-A"})


if __name__ == "__main__":
    unittest.main()
