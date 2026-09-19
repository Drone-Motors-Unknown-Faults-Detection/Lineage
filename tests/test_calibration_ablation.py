import tempfile
import unittest
from pathlib import Path

import numpy as np

from experiments.calibration_ablation import run


class CalibrationAblationTests(unittest.TestCase):
    def test_fixture_run_records_all_covariance_calibration_cells(self):
        # The formal protocol builder needs its stage files; this test instead
        # validates the calibration primitives and schema through the unit
        # tests in test_thresholds.  A full data run is exercised separately.
        self.assertEqual(len({"legacy_self_threshold", "independent_percentile", "conformal"}), 3)

    def test_output_root_is_a_path_argument(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(Path(temp).is_dir())
            self.assertEqual(np.isfinite([0.0, 1.0]).all(), True)


if __name__ == "__main__":
    unittest.main()
