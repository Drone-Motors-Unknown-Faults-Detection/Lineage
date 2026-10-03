"""實驗18拒絕公式與校準來源；合成工程測試不作研究成績。"""
import pickle
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from core.fault_type_context_rejection import ContextRejection, components, EPSILON
from core.fault_type_context_prototypes import ContextPrototypes
from experiments import fault_type_context_rejection as J
from experiments import fault_type_context_prototypes as I
from experiments.fault_type_fixed_smoke import fixture
from experiments.fault_type_fixed_calibration import build_protocol
from core.fault_type_fixed_calibration import fixed_manifests
from core.fault_type_validator import compute_manifest_checksum
from core.fault_type_final_guard import seal


class IdentityTransform:
    def transform(self, X):
        return np.asarray(X)


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


class RejectionSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(0)
        cls.rpm = np.tile(np.repeat([6000, 8000, 11000], 8), 2)
        y = np.repeat([0, 1], 24)
        X = y[:, None]*2+((cls.rpm-8000)/3000)[:, None]*[3, -.5, 2]+rng.normal(0, .02, (48, 3))
        cls.spaces = {g: (X, X+.05) for g in ['identity', 'metric']}
        cls.b = dict(weights=[1., 1., 1.], nodes={d['id']: dict(status='completed',
            model=ContextPrototypes(d['degree'], d['variant'], 0).fit(X, y, cls.rpm, np.arange(48))) for d in I.MODELS})
        cls.nodes = J.calibrate_nodes(cls.b, cls.spaces, cls.rpm, cls.rpm)

    def setUp(self):
        self.nodes = copy.deepcopy(self.__class__.nodes)

    def verify(self, spaces=None, b=None):
        return J.verify_nodes(self.nodes, b or self.b, spaces or self.spaces, self.rpm, self.rpm)

    def test_actual_calibration_replay(self):
        self.assertEqual(len(self.verify()), 36)

    def test_changed_calibration_rejected(self):
        spaces = {g: (z, c+.3) for g, (z, c) in self.spaces.items()}
        with self.assertRaises(ValueError):
            self.verify(spaces)

    def test_changed_train_rejected(self):
        spaces = {g: (z+.3, c) for g, (z, c) in self.spaces.items()}
        with self.assertRaises(ValueError):
            self.verify(spaces)

    def test_resealed_threshold_rejected(self):
        model = next(iter(self.nodes.values()))['model']
        model.quantiles_[0] += .1
        model.checksum_ = model.signature()
        with self.assertRaises(ValueError):
            self.verify()

    def test_parent_resealed_prototype_rejected(self):
        b = copy.deepcopy(self.b)
        model = next(iter(b['nodes'].values()))['model']
        model.coefficients_[0, 0, 0] += .2
        model.checksum_ = model.signature()
        with self.assertRaises(ValueError):
            self.verify(b=b)

    def test_node_inventory(self):
        self.nodes.pop(next(iter(self.nodes)))
        with self.assertRaises(ValueError):
            self.verify()

    def test_inference_uses_no_truth(self):
        parent = dict(references={'harmonic69/mixed': dict(transformer=IdentityTransform())})
        X = self.spaces['identity'][0]
        first = J.infer(parent, dict(nodes=self.nodes), self.b, X, self.rpm)
        second = J.infer(parent, dict(nodes=self.nodes), self.b, X.copy(), self.rpm.copy())
        self.assertEqual(len(first), 36)
        for arm in J.ARMS:
            for field in [0, 1]:
                np.testing.assert_array_equal(first[arm['id']][field], second[arm['id']][field])
            self.assertEqual(first[arm['id']][2], 0.)

    def test_classifier_same_for_all_three_scores(self):
        parent = dict(references={'harmonic69/mixed': dict(transformer=IdentityTransform())})
        x = self.spaces['identity'][0]
        values = J.infer(parent, dict(nodes=self.nodes), self.b, x, self.rpm)
        for i in range(0, 36, 3):
            keys = [J.ARMS[j]['id'] for j in range(i, i+3)]
            np.testing.assert_array_equal(values[keys[0]][0], values[keys[1]][0])
            np.testing.assert_array_equal(values[keys[0]][0], values[keys[2]][0])
            np.testing.assert_array_equal(values[keys[2]][1] > 0, (values[keys[0]][1] > 0)|(values[keys[1]][1] > 0))

    def test_empty_matrix_is_refused_after_source_gate(self):
        context = (None, None, None, (None, None, None, [{}]))
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(J, 'check', return_value=context), patch.object(J, 'validate_parent_source'), \
                    patch.object(J, 'verify_sources', return_value='SYNTHETIC'), patch.object(J, 'budget'):
                with self.assertRaisesRegex(ValueError, 'inventory mismatch'):
                    J.evaluate(type('Pools', (), dict(root=Path(folder)))(), {}, dict(artifacts=[]), {}, Path(folder))

    def test_global_selector_and_false_fresh_are_rejected(self):
        p = dict(selection_policy='none', selection_sample_ids=[], validation_sample_ids=[], shared_validation_calibration=False,
                 fresh_final_test=False, scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED')
        for change in [dict(global_winner='J01'), dict(selection_sample_ids=['test']), dict(shared_validation_calibration=True),
                       dict(fresh_final_test=True)]:
            with self.assertRaisesRegex(ValueError, 'selection/exposure policy'):
                J.check(seal(dict(p, **change), 'protocol_checksum'))

    def test_resealed_parameters_cannot_change_method(self):
        p = dict(selection_policy='none', selection_sample_ids=[], validation_sample_ids=[], shared_validation_calibration=False,
                 fresh_final_test=False, scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED', version='exp18_context_rejection_v1',
                 parameters=dict(J.PARAMETERS, quantile=.9), arms=J.ARMS, budget=J.BUDGET, reliability_contract=J.CONTRACT)
        with self.assertRaisesRegex(ValueError, 'definitions changed'):
            J.check(seal(p, 'protocol_checksum'))

    def test_saved_raw_components_cannot_change(self):
        extra = dict(raw=np.array([[1., .2]]), quantiles=[2., .8], state_checksum='SYNTHETIC', mode='or')
        row = dict(context_distance=1., context_ambiguity=.2, calibration_quantiles=[2., .8], rejector_state_checksum='SYNTHETIC', score_mode='or')
        J.check_components([row], extra)
        for change in [dict(context_distance=2.), dict(calibration_quantiles=[3., .8]), dict(score_mode='distance'), dict(rejector_state_checksum='changed')]:
            with self.assertRaises(ValueError):
                J.check_components([dict(row, **change)], extra)


class RejectionPurposeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        priors, ledger = fixture(Path(cls.temp.name)/'data')
        cls.p = build_protocol(priors, ledger)
        cls.m = fixed_manifests(priors, cls.p)[0]
        cls.p = dict(protocol_checksum=cls.p['protocol_checksum'], dataset_fingerprint='SYNTHETIC_FIXTURE_ONLY',
                     known_labels=[cls.m['healthy_label'], *cls.m['known_fault_labels']])
        cls.b = dict(audits=I.expected_audits(cls.p, cls.m, dict(seed=0), np.array([0], int)))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_exact_known_cal_ids_no_selection(self):
        audit = J.expected_audits(self.p, self.m, self.b)
        self.assertEqual(len(audit), 36)
        for a in audit:
            self.assertEqual(a['detector_calibration_ids'], self.m['sample_ids']['calibration'])
            self.assertFalse(a['new_classifier_fit'])
            self.assertEqual(a['selection_sample_ids'], [])

    def test_unknown_and_test_motor_in_development(self):
        for part in ['train', 'calibration']:
            for key, value in [('label', self.m['unknown_test_labels'][0]), ('t_code', self.m['motor_roles']['test'])]:
                m = copy.deepcopy(self.m)
                sid = m['sample_ids'][part][0]
                next(r for r in m['records'] if r['sample_id'] == sid)[key] = value
                m['manifest_checksum'] = compute_manifest_checksum(m)
                with self.assertRaises(ValueError):
                    J.expected_audits(self.p, m, self.b)

    def test_calibration_in_parent_fit_is_rejected(self):
        b = copy.deepcopy(self.b)
        b['audits'][0]['classifier_fit_ids'].append(self.m['sample_ids']['calibration'][0])
        with self.assertRaises(ValueError):
            J.expected_audits(self.p, self.m, b)


if __name__ == '__main__':
    unittest.main()
