"""實驗18拒絕公式與校準來源；合成工程測試不作研究成績。"""
import pickle
import unittest
import numpy as np
from core.fault_type_context_rejection import ContextRejection, components, EPSILON


class ContextRejectionTests(unittest.TestCase):
    def test_hand_components(self):
        np.testing.assert_allclose(components([[1, 3, 8], [2, 2, 9], [0, 0, 4]]),
            [[1, 1-2/(4+EPSILON)], [2, 1], [0, 1]], rtol=0, atol=1e-15)

    def test_unknown_truth_not_an_input(self):
        d = [[1, 2], [3, 9]]
        m = ContextRejection('distance').calibrate(d)
        np.testing.assert_array_equal(m.score_samples(d), m.score_samples(np.array(d)))

    def test_quantile_linear(self):
        m = ContextRejection('distance').calibrate([[0, 1], [2, 3]])
        self.assertEqual(m.quantiles_[0], 1.9)
        self.assertGreater(m.score_samples([[2, 3]])[0], 0)

    def test_zero_quantile_and_tie(self):
        m = ContextRejection('distance').calibrate([[0, 0], [0, 0]])
        np.testing.assert_array_equal(m.score_samples([[0, 0], [1, 2]]), [0, 1/EPSILON])
        self.assertFalse(m.score_samples([[0, 0]])[0] > 0)

    def test_or_exact_boolean_union(self):
        cal = [[.1, 4], [.2, 3], [1, 5]]
        query = [[0, 4], [9, 10], [.5, .5], [.2, 1]]
        models = {k: ContextRejection(k).calibrate(cal) for k in ['distance', 'ambiguity', 'or']}
        a, b, c = [models[k].score_samples(query) for k in models]
        np.testing.assert_array_equal(c > 0, (a > 0) | (b > 0))
        np.testing.assert_array_equal(c, np.maximum(a, b))

    def test_distances_invalid(self):
        for x in [[[1]], [[-1, 3]], [[np.nan, 1]], [[np.inf, 1]], [1, 2]]:
            with self.assertRaises(ValueError):
                components(x)

    def test_no_empty_calibration(self):
        with self.assertRaises(ValueError):
            ContextRejection('distance').calibrate(np.empty((0, 2)))

    def test_overflow_rejected(self):
        with self.assertRaises(ValueError):
            components([[1e308, 1e308]])

    def test_empty_queries(self):
        for mode in ['distance', 'ambiguity', 'or']:
            m = ContextRejection(mode).calibrate([[1, 3]])
            self.assertEqual(m.score_samples(np.empty((0, 2))).shape, (0,))

    def test_fixed_mode_only(self):
        with self.assertRaises(ValueError):
            ContextRejection('choose_best')

    def test_state_tamper(self):
        m = ContextRejection('ambiguity').calibrate([[1, 3]])
        m.quantiles_[0] += 1
        with self.assertRaises(ValueError):
            m.score_samples([[1, 3]])

    def test_calibration_replay_and_pickle(self):
        m = ContextRejection('or').calibrate([[0, 2], [2, 3], [9, 15]])
        n = ContextRejection('or').calibrate([[0, 2], [2, 3], [9, 15]])
        self.assertEqual(m.checksum_, n.checksum_)
        np.testing.assert_array_equal(m.score_samples([[2, 9]]), pickle.loads(pickle.dumps(n)).score_samples([[2, 9]]))

    def test_far_and_ambiguous_are_distinct(self):
        m = ContextRejection('distance').calibrate([[1, 9]])
        n = ContextRejection('ambiguity').calibrate([[1, 9]])
        self.assertGreater(m.score_samples([[100, 900]])[0], 0)
        self.assertLessEqual(n.score_samples([[100, 900]])[0], 0)
        self.assertLess(m.score_samples([[.2, .2]])[0], 0)
        self.assertGreater(n.score_samples([[.2, .2]])[0], 0)


if __name__ == '__main__':
    unittest.main()
