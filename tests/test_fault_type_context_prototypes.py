import pickle
import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy.optimize import check_grad
from core.fault_type_context_prototypes import ContextPrototypes, context_basis, context_distances, relative_objective
from core.fault_type_discriminative_prototypes import relative_objective as pooled_objective
from core.fault_type_fixed_calibration import fixed_manifests
from core.fault_type_validator import compute_manifest_checksum
from experiments.fault_type_fixed_calibration import build_protocol
from experiments.fault_type_fixed_smoke import fixture
from experiments.fault_type_context_prototypes import fit_node, verify_node, rpm_values, expected_audits, validate_policy, MODELS, ARMS


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


class ContextSourceTests(unittest.TestCase):
    def setUp(self):
        self.X, self.y, self.rpm, self.ix = ContextPrototypeTests().data()
        self.C, self.cr = self.X+.5, self.rpm.copy()
        self.d = dict(degree=1, variant='static')
        self.node = fit_node(self.d, self.X, self.C, self.y, self.rpm, self.cr, self.ix, 0)

    def verify(self):
        return verify_node(self.node, self.d, self.X, self.C, self.y, self.rpm, self.cr, self.ix, 0)

    def test_actual_source(self):
        self.assertEqual(self.verify()['status'], 'completed')
        self.assertEqual(len(MODELS), 12)
        self.assertEqual(len({a['id'] for a in ARMS}), 12)

    def test_calibration_cannot_initialize(self):
        self.node = fit_node(self.d, self.C, self.C, self.y, self.rpm, self.cr, self.ix, 0)
        with self.assertRaises(ValueError):
            self.verify()

    def test_train_rpm_source(self):
        self.node = fit_node(self.d, self.X, self.C, self.y, self.rpm[::-1], self.cr, self.ix, 0)
        with self.assertRaises(ValueError):
            self.verify()

    def test_cal_rpm_source(self):
        self.node['calibration_rpm_checksum'] = 'different'
        with self.assertRaises(ValueError):
            self.verify()

    def test_resealed_coefficients(self):
        self.node['model'].coefficients_[0, 0, 0] += .1
        self.node['model'].checksum_ = self.node['model'].signature()
        with self.assertRaises(ValueError):
            self.verify()

    def test_rpm_not_truth_or_motor(self):
        a = [dict(rpm='6000rpm', label='fault', t_code='T1')]
        b = [dict(rpm='6000rpm', label='unknown', t_code='T2')]
        np.testing.assert_array_equal(rpm_values(a), rpm_values(b))
        with self.assertRaises(ValueError):
            rpm_values([dict(rpm='2screws')])

    def test_selector_exposure_guard(self):
        p = dict(selection_policy='none', selection_sample_ids=[], validation_sample_ids=[], shared_validation_calibration=False,
                 fresh_final_test=False, scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED')
        validate_policy(p)
        for change in [dict(global_winner='I01'), dict(selected_model='I01'), dict(selection_sample_ids=['test']),
                       dict(shared_validation_calibration=True), dict(fresh_final_test=True), dict(scope='FRESH')]:
            with self.assertRaises(ValueError):
                validate_policy(dict(p, **change))


class ContextPurposeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        priors, ledger = fixture(Path(cls.temp.name)/'data')
        cls.p = build_protocol(priors, ledger)
        cls.m = fixed_manifests(priors, cls.p)[0]
        cls.p = dict(protocol_checksum=cls.p['protocol_checksum'], dataset_fingerprint='SYNTHETIC_FIXTURE_ONLY',
                     known_labels=[cls.m['healthy_label'], *cls.m['known_fault_labels']])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def audit(self, m):
        return expected_audits(self.p, m, dict(seed=0), np.array([0], int))

    def test_empty_selection_and_purpose(self):
        a = self.audit(self.m)
        self.assertEqual(len(a), 12)
        self.assertTrue(all(x['selection_sample_ids'] == [] and x['context_fit_ids'] == x['classifier_fit_ids'] for x in a))
        self.assertTrue(all(not set(x['context_fit_ids'])&set(x['calibration_sample_ids']) for x in a))

    def test_unknown_and_test_motor_in_fit_or_cal(self):
        for part in ['train', 'calibration']:
            for key, value in [('label', self.m['unknown_test_labels'][0]), ('t_code', self.m['motor_roles']['test'])]:
                m = copy.deepcopy(self.m)
                sid = m['sample_ids'][part][0]
                next(r for r in m['records'] if r['sample_id'] == sid)[key] = value
                m['manifest_checksum'] = compute_manifest_checksum(m)
                with self.assertRaises(ValueError):
                    self.audit(m)


if __name__ == '__main__':
    unittest.main()
