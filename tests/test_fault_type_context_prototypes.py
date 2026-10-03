import pickle
import unittest
import numpy as np
from scipy.optimize import check_grad
from core.fault_type_context_prototypes import ContextPrototypes, context_basis, context_distances, relative_objective
from core.fault_type_discriminative_prototypes import relative_objective as pooled_objective


class ContextPrototypeTests(unittest.TestCase):
    def data(self):
        rng = np.random.default_rng(17)
        r = np.tile(np.repeat([6000, 8000, 11000], 10), 2)
        y = np.repeat([0, 1], 30)
        c = (r-8000)/3000
        X = y[:, None]*2-1+c[:, None]*np.array([3., -.5, 2.])[None, :]+rng.normal(0, .05, (60, 3))
        return X, y, r, np.arange(60)

    def test_basis_hand(self):
        np.testing.assert_array_equal(context_basis([6000, 8000, 11000], 1), [[1, -2/3], [1, 0], [1, 1]])
        np.testing.assert_array_equal(context_basis([8000], 2), [[1, 0, 0]])

    def test_invalid_rpm(self):
        for bad in [[7000], [np.nan], [6000.1], [[6000]], ['T1'], ['2screws']]:
            with self.assertRaises(ValueError):
                context_basis(bad, 1)

    def test_context_hand_distance(self):
        theta = np.array([[[1., 2.], [2., 0.]], [[3., 0.], [0., 1.]]])
        d, w = context_distances([[0., 0.]], theta, context_basis([11000], 1))
        np.testing.assert_array_equal(w, [[[3., 2.], [3., 1.]]])
        np.testing.assert_array_equal(d, [[13., 10.]])

    def test_gradient_with_auxiliary(self):
        X, y, r, _ = self.data()
        for degree in [1, 2]:
            theta = ContextPrototypes(degree).fit(X, y, r, np.arange(60)).initial_+.07
            phi = context_basis(r, degree)
            for aux in [0., .01]:
                args = X, y, np.array([0, 1]), phi, aux
                error = check_grad(lambda w: relative_objective(w.reshape(theta.shape), *args)[0],
                                   lambda w: relative_objective(w.reshape(theta.shape), *args)[1].ravel(), theta.ravel())
                self.assertLess(error, 2e-6)

    def test_degree_zero_pooled_loss(self):
        X, y, r, ix = self.data()
        model = ContextPrototypes(0).fit(X, y, r, ix)
        mean = np.stack([X[y == c].mean(axis=0) for c in [0, 1]])
        np.testing.assert_allclose(model.initial_[:, 0], mean, atol=1e-14)
        value, gradient = relative_objective(model.initial_, X, y, model.labels_, context_basis(r, 0))
        control, g = pooled_objective(mean, X, y, model.labels_, mean)
        self.assertAlmostEqual(value, control, places=13)
        np.testing.assert_allclose(gradient[:, 0], g, atol=1e-13)

    def test_quadratic_matches_rpm_means(self):
        X, y, r, ix = self.data()
        model = ContextPrototypes(2).fit(X, y, r, ix)
        for rpm in [6000, 8000, 11000]:
            means = np.stack([X[(y == c)&(r == rpm)].mean(axis=0) for c in [0, 1]])
            w = np.einsum('nq,cqd->ncd', context_basis([rpm], 2), model.initial_)[0]
            np.testing.assert_allclose(w, means, atol=1e-13)

    def test_context_signal_and_routing(self):
        X, y, r, ix = self.data()
        model = ContextPrototypes().fit(X, y, r, ix)
        np.testing.assert_array_equal(model.predict(X, r), y)
        self.assertTrue(np.any(model.predict(X, np.repeat(8000, len(r))) != y))

    def test_missing_rpm_support(self):
        X, y, r, ix = self.data()
        mask = (y != 0)|(r != 6000)
        with self.assertRaises(ValueError):
            ContextPrototypes().fit(X[mask], y[mask], r[mask], np.arange(mask.sum()))

    def test_replay_pickle_and_optimizer(self):
        X, y, r, ix = self.data()
        for variant in ['glvq', 'auxiliary']:
            a = ContextPrototypes(1, variant, 1).fit(X, y, r, ix)
            b = ContextPrototypes(1, variant, 1).fit(X, y, r, ix)
            self.assertTrue(a.optimizer_['success'])
            self.assertEqual(a.signature(), b.signature())
            self.assertLessEqual(a.optimizer_['final_loss'], a.optimizer_['initial_loss']+1e-12)
            np.testing.assert_array_equal(a.predict(X, r), pickle.loads(pickle.dumps(a)).predict(X, r))

    def test_nonconvergence(self):
        X, y, r, ix = self.data()
        a = ContextPrototypes(1, 'glvq').fit(X, y, r, ix, options={'maxiter': 0})
        self.assertFalse(a.optimizer_['success'])
        with self.assertRaises(ValueError):
            a.predict(X, r)

    def test_tamper_and_empty(self):
        X, y, r, ix = self.data()
        a = ContextPrototypes().fit(X, y, r, ix)
        self.assertEqual(len(a.predict(np.empty((0, 3)), [])), 0)
        a.coefficients_[0, 0, 0] += .1
        with self.assertRaises(ValueError):
            a.predict(X, r)


if __name__ == '__main__':
    unittest.main()
