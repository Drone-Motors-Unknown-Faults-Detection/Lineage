import pickle
import unittest
import numpy as np
from scipy.optimize import check_grad
from core.fault_type_smooth_l1 import (ALPHA, smooth_absolute, distances_and_gradients,
                                      relative_objective, SmoothL1Prototypes)
from core.fault_type_metric_classifiers import PrototypeClassifier


class SmoothL1Tests(unittest.TestCase):
    def data(self):
        rng = np.random.default_rng(17)
        X = np.r_[rng.normal(-1, .25, (15, 4)), rng.normal(1, .25, (15, 4))]
        return X, np.repeat([0, 1], 15), np.arange(30)

    def test_original_zero_values(self):
        q, dq = smooth_absolute(np.zeros(2), 'quasi')
        s, ds = smooth_absolute(np.zeros(2), 'soft')
        np.testing.assert_array_equal(q, 2*np.log(2)/ALPHA)
        np.testing.assert_array_equal(s, 0)
        np.testing.assert_array_equal(dq, 0)
        np.testing.assert_array_equal(ds, 0)

    def test_function_gradient(self):
        z = np.array([-.3, -.07, 0., .03, .5])
        for kind in ['quasi', 'soft']:
            e = check_grad(lambda x: smooth_absolute(x, kind)[0].sum(),
                           lambda x: smooth_absolute(x, kind)[1], z)
            self.assertLess(e, 2e-6)

    def test_extreme_stability(self):
        z = np.array([-1e6, 1e6, 0.])
        for kind in ['quasi', 'soft']:
            value, gradient = smooth_absolute(z, kind)
            self.assertTrue(np.isfinite(value).all())
            self.assertTrue(np.isfinite(gradient).all())
            np.testing.assert_allclose(gradient[:2], [-1, 1])

    def test_distance_hand_calculation(self):
        X = np.array([[1., 2.]])
        W = np.array([[0., 0.]])
        for kind in ['quasi', 'soft']:
            distance, gradient = distances_and_gradients(X, W, kind)
            value, dz = smooth_absolute(X[0], kind)
            self.assertEqual(distance[0, 0], value.sum())
            np.testing.assert_array_equal(gradient[0, 0], -dz)

    def test_relative_gradient(self):
        X, y, _ = self.data()
        W = np.array([[-.8, -.7, -1.3, -.9], [.7, 1.1, .8, 1.3]])
        for kind in ['quasi', 'soft']:
            for anchor in [0., .01]:
                args = (X, y, np.array([0, 1]), W+.2, kind, anchor)
                e = check_grad(lambda w: relative_objective(w.reshape(W.shape), *args)[0],
                               lambda w: relative_objective(w.reshape(W.shape), *args)[1].ravel(), W.ravel())
                self.assertLess(e, 1e-6)

    def test_static_matched_mean(self):
        X, y, ix = self.data()
        for kind in ['quasi', 'soft']:
            model = SmoothL1Prototypes(kind).fit(X, y, ix)
            original = PrototypeClassifier(1, 42).fit(X, y)
            np.testing.assert_array_equal(model.prototypes_, original.prototypes_)
            np.testing.assert_array_equal(model.predict(X), y)

    def test_optimizer_and_anchor(self):
        X, y, ix = self.data()
        for kind in ['quasi', 'soft']:
            for variant in ['glvq', 'anchored']:
                model = SmoothL1Prototypes(kind, variant).fit(X, y, ix)
                self.assertTrue(model.optimizer_['success'])
                self.assertLessEqual(model.optimizer_['final_loss'], model.optimizer_['initial_loss']+1e-12)

    def test_replay_and_pickle(self):
        X, y, ix = self.data()
        for kind in ['quasi', 'soft']:
            model = SmoothL1Prototypes(kind, 'anchored', 1).fit(X, y, ix)
            second = SmoothL1Prototypes(kind, 'anchored', 1).fit(X, y, ix)
            self.assertEqual(model.signature(), second.signature())
            np.testing.assert_array_equal(model.predict(X), pickle.loads(pickle.dumps(model)).predict(X))

    def test_zero_tie(self):
        X = np.zeros((2, 3))
        for kind in ['quasi', 'soft']:
            model = SmoothL1Prototypes(kind).fit(X, np.array([0, 1]), np.arange(2))
            np.testing.assert_array_equal(model.predict(X), 0)
            self.assertEqual(model.optimizer_['initial_loss'], .5)

    def test_nonconvergence_refused(self):
        X, y, ix = self.data()
        model = SmoothL1Prototypes('soft', 'glvq').fit(X, y, ix, options={'maxiter': 0})
        self.assertFalse(model.optimizer_['success'])
        with self.assertRaises(ValueError):
            model.predict(X)

    def test_tampering_refused(self):
        X, y, ix = self.data()
        model = SmoothL1Prototypes().fit(X, y, ix)
        model.prototypes_[0, 0] += .1
        with self.assertRaises(ValueError):
            model.predict(X)

    def test_invalid_and_empty_inputs(self):
        X, y, ix = self.data()
        for bad in [np.array([], int), np.array([0, 0, 16]), np.array([-1, 16]), np.array([0., 16.])]:
            with self.assertRaises(ValueError):
                SmoothL1Prototypes().fit(X, y, bad)
        model = SmoothL1Prototypes().fit(X, y, ix)
        self.assertEqual(len(model.predict(np.empty((0, 4)))), 0)
        with self.assertRaises(ValueError):
            model.predict([[np.nan]*4])


if __name__ == '__main__':
    unittest.main()
