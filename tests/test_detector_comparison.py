import unittest

import numpy as np

from experiments.detector_comparison import _fpr_at_95_tpr


class DetectorComparisonTests(unittest.TestCase):
    def test_fpr_metric_is_evaluation_only_and_bounded(self):
        value = _fpr_at_95_tpr(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]))
        self.assertIsNotNone(value)
        self.assertTrue(0.0 <= value <= 1.0)


if __name__ == "__main__":
    unittest.main()
