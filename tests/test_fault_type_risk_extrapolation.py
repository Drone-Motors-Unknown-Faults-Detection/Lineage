"""REx改編的合成公式與actual source測試，不是正式研究成績。"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from scipy.special import logsumexp
from core.fault_type_risk_extrapolation import (objective, risk_design, RiskExtrapolationClassifier,
                                               RIDGE, OPTIMIZER)


class TestRiskFormula(unittest.TestCase):
    def setUp(self):
        self.X = np.random.default_rng(42).normal(size=(36, 4))
        self.y = np.tile(np.arange(3), 12)
        self.env = np.repeat([6000, 8000, 11000], 12)
        self.theta = np.random.default_rng(123).normal(size=15)*.1

    def test_hand_equal_class_environment_risks(self):
        value, _, risks = objective(self.theta, self.X, self.y, self.env, 1.)
        A = self.theta.reshape(5, 3)
        logits = np.column_stack([self.X, np.ones(36)]) @ A
        ce = logsumexp(logits, axis=1)-logits[np.arange(36), self.y]
        expected = np.array([np.mean([ce[(self.env == e)&(self.y == c)].mean() for c in range(3)]) for e in np.unique(self.env)])
        np.testing.assert_allclose(risks, expected, rtol=1e-14)
        self.assertAlmostEqual(value, expected.mean()+np.var(expected)+RIDGE/2*np.sum(A[:-1]**2))

    def test_analytic_gradient_all_fixed_betas(self):
        for beta in [0., 1., 10.]:
            _, grad, _ = objective(self.theta, self.X, self.y, self.env, beta)
            numeric = []
            for j in range(len(self.theta)):
                plus, minus = self.theta.copy(), self.theta.copy()
                plus[j] += 1e-5; minus[j] -= 1e-5
                numeric.append((objective(plus, self.X, self.y, self.env, beta)[0]-objective(minus, self.X, self.y, self.env, beta)[0])/2e-5)
            np.testing.assert_allclose(grad, numeric, rtol=1e-6, atol=1e-9)

    def test_zero_beta_erm_and_no_bias_ridge(self):
        value, grad, risks = objective(np.zeros(15), self.X, self.y, self.env, 0.)
        self.assertAlmostEqual(value, np.log(3))
        np.testing.assert_allclose(risks, np.log(3))
        np.testing.assert_allclose(grad[-3:], 0., atol=1e-15)

    def test_duplicate_complete_cell_does_not_change_weight(self):
        mask = (self.env == 8000)&(self.y == 1)
        a = objective(self.theta, self.X, self.y, self.env, 10.)
        b = objective(self.theta, np.concatenate([self.X, self.X[mask]]),
                      np.concatenate([self.y, self.y[mask]]), np.concatenate([self.env, self.env[mask]]), 10.)
        for old, new in zip(a, b):
            np.testing.assert_allclose(old, new, rtol=1e-12, atol=1e-14)

    def test_three_environment_population_not_sample_variance(self):
        a, _, risks = objective(self.theta, self.X, self.y, self.env, 1.)
        b, _, _ = objective(self.theta, self.X, self.y, self.env, 0.)
        self.assertAlmostEqual(a-b, np.var(risks, ddof=0))
        self.assertNotAlmostEqual(a-b, np.var(risks, ddof=1), places=8)

    def test_missing_class_or_environment_incomplete(self):
        for mask in [self.env != 6000, ~((self.env == 6000)&(self.y == 2))]:
            with self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
                risk_design(self.X[mask], self.y[mask], self.env[mask])

    def test_invalid_inputs_and_nonfinite(self):
        for X, y, env in [(self.X[:0], self.y[:0], self.env[:0]),
                (self.X, self.y.astype(float), self.env), (self.X, self.y+1, self.env),
                (self.X, self.y, self.env[:-1]), (self.X*np.nan, self.y, self.env)]:
            with self.assertRaises(ValueError):
                risk_design(X, y, env)
        with self.assertRaises(ValueError):
            objective(self.theta, self.X, self.y, self.env, .5)
        with self.assertRaises(ValueError):
            objective(self.theta, self.X, self.y, self.env, 0., ridge=0)

    def test_overflow_refused(self):
        with self.assertRaises(ValueError):
            objective(np.ones(15)*1e200, self.X*1e200, self.y, self.env, 10.)


class TestRiskClassifier(unittest.TestCase):
    setUp = TestRiskFormula.setUp
    def test_warm_start_requires_same_known_source(self):
        erm = RiskExtrapolationClassifier(0., 0).fit(self.X, self.y, self.env)
        for base in [None, RiskExtrapolationClassifier(0., 1).fit(self.X, self.y, self.env)]:
            with self.assertRaises(ValueError):
                RiskExtrapolationClassifier(1., 0).fit(self.X, self.y, self.env, base)
        X = self.X.copy(); X[0, 0] += .1
        with self.assertRaises(ValueError):
            RiskExtrapolationClassifier(1., 0).fit(X, self.y, self.env, erm)
        with self.assertRaises(ValueError):
            RiskExtrapolationClassifier(0., 0).fit(self.X, self.y, self.env, erm)

    def test_determinism_and_actual_source(self):
        erm = RiskExtrapolationClassifier(0., 0).fit(self.X, self.y, self.env)
        for beta in [0., 1., 10.]:
            m = erm if beta == 0 else RiskExtrapolationClassifier(beta, 0).fit(self.X, self.y, self.env, erm)
            proof = m.verify_known_source(self.X, self.y, self.env, None if beta == 0 else erm)
            self.assertEqual(proof['test_numeric_reads'], 0)
            self.assertEqual(m.optimizer_['options'], OPTIMIZER)
            np.testing.assert_allclose(m.predict_proba(self.X).sum(1), 1.)
            np.testing.assert_array_equal(m.predict(self.X), m.predict_proba(self.X).argmax(1))
            self.assertEqual(len(m.predict(np.empty((0, 4)))), 0)

    def test_coefficient_tampering_and_resealing(self):
        m = RiskExtrapolationClassifier().fit(self.X, self.y, self.env)
        m.coef_[0, 0] += .1
        with self.assertRaises(ValueError):
            m.predict(self.X)
        m.checksum_ = m.signature()
        with self.assertRaisesRegex(ValueError, 'source mismatch'):
            m.verify_known_source(self.X, self.y, self.env)

    def test_optimizer_failure_is_incomplete(self):
        result = SimpleNamespace(success=False, message='SYNTHETIC_NONCONVERGENCE', x=np.zeros(15))
        with patch('core.fault_type_risk_extrapolation.minimize', return_value=result):
            with self.assertRaisesRegex(RuntimeError, 'INCOMPLETE'):
                RiskExtrapolationClassifier().fit(self.X, self.y, self.env)

    def test_query_truth_and_environment_not_required(self):
        m = RiskExtrapolationClassifier().fit(self.X, self.y, self.env)
        before = m.predict(self.X)
        self.y[:] = 2; self.env[:] = 11000
        np.testing.assert_array_equal(before, m.predict(self.X))
        with self.assertRaises(ValueError):
            m.predict(self.X[:, :3])


if __name__ == '__main__':
    unittest.main()
