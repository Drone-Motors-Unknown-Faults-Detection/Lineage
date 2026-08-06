import unittest

import numpy as np

from scripts.openset_mahalanobis import MahalanobisOpenSetDetector


class MahalanobisOpenSetDetectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(42)
        class0 = rng.normal(-2.0, 0.3, size=(100, 6))
        class1 = rng.normal(2.0, 0.3, size=(100, 6))
        cls.X_train = np.vstack([class0[:70], class1[:70]])
        cls.y_train = np.repeat([0, 1], 70)
        cls.X_cal = np.vstack([class0[70:], class1[70:]])
        cls.y_cal = np.repeat([0, 1], 30)
        cls.X_unknown = rng.normal(10.0, 0.3, size=(20, 6))

    def test_all_methods_reject_far_unknown_samples(self):
        for method in ("legacy", "ledoit_wolf", "oas", "mcd"):
            with self.subTest(method=method):
                detector = MahalanobisOpenSetDetector(method=method).fit(
                    self.X_train, self.y_train, self.X_cal, self.y_cal
                )
                self.assertGreater(np.mean(detector.score_samples(self.X_unknown) > 1.0), 0.95)

    def test_class_conditional_methods_return_known_labels(self):
        for method in ("ledoit_wolf", "oas", "mcd"):
            with self.subTest(method=method):
                detector = MahalanobisOpenSetDetector(method=method).fit(
                    self.X_train, self.y_train, self.X_cal, self.y_cal
                )
                predictions = detector.predict_known_class(self.X_cal)
                self.assertGreater(np.mean(predictions == self.y_cal), 0.85)

    def test_unknown_data_cannot_set_threshold(self):
        detector = MahalanobisOpenSetDetector(method="oas")
        with self.assertRaises(TypeError):
            detector.fit(self.X_train, self.y_train, self.X_cal, self.y_cal, self.X_unknown)


if __name__ == "__main__":
    unittest.main()
