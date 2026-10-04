"""exp19先行公式／來源回歸；合成資料不作研究成績。"""
import copy
import tempfile
import itertools
import unittest
from unittest.mock import patch
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cdist
from core.fault_type_axis_kernel import (SharedAxisRepresentation, AxisKernelClassifier,
    KernelCentroidRejection, kernel, kernel_diagonal, permute_axes, GAMMA, PERMUTATIONS)
from experiments import fault_type_axis_kernel as K
from experiments.fault_type_fixed_smoke import fixture
from experiments.fault_type_fixed_calibration import build_protocol
from core.fault_type_fixed_calibration import fixed_manifests
from core.fault_type_validator import compute_manifest_checksum
from core.fault_type_final_guard import seal
from core.fault_type_literature import LiteratureRepresentation
from core.openset import create_openset_detector
from experiments.fault_type_openset import DETECTOR_CONFIG


def formal(seed=42, n=18):
    r = np.random.default_rng(seed)
    X = r.normal(size=(n, 105))
    for offset in (15, 40, 65):
        X[:, offset+7] = X[:, offset+9]
        X[:, offset+12] = X[:, offset]**2
        X[:, offset+13] = X[:, offset+3]**2
    return X


def formal_permutation(X, permutation):
    Y = X.copy()
    Y[:, 15:90] = X[:, 15:90].reshape(-1, 3, 25)[:, permutation, :].reshape(-1, 75)
    return Y


class TestAxisKernel(unittest.TestCase):
    def setUp(self):
        self.X = formal()
        self.Z = SharedAxisRepresentation().fit(self.X).transform(self.X)
        self.y = np.arange(len(self.X)) % 3

    def test_scaler_commutes_with_permutation(self):
        s = SharedAxisRepresentation().fit(self.X)
        for p in PERMUTATIONS:
            np.testing.assert_array_equal(s.transform(formal_permutation(self.X, p)), permute_axes(self.Z, p))

    def test_scaler_fit_shared_distribution(self):
        from core.fault_type_accuracy import VIBRATION66
        s = SharedAxisRepresentation().fit(self.X)
        np.testing.assert_array_equal(s.scaler_.center_, np.median(self.X[:, VIBRATION66].reshape(-1, 22), axis=0))

    def test_scaler_tamper(self):
        s = SharedAxisRepresentation().fit(self.X)
        s.scaler_.scale_[0] *= 2
        with self.assertRaises(ValueError):
            s.transform(self.X)

    def test_redundancy_gate_train_only(self):
        X = self.X.copy()
        X[0, 22] += 1
        with self.assertRaises(ValueError):
            SharedAxisRepresentation().fit(X)

    def test_empty_transform_not_fit(self):
        s = SharedAxisRepresentation().fit(self.X)
        self.assertEqual(s.transform(np.empty((0, 105))).shape, (0, 66))
        with self.assertRaises(ValueError):
            s.fit(np.empty((0, 105)))

    def test_zero_alpha_matches_rbf(self):
        np.testing.assert_allclose(kernel(self.Z, self.Z, 0), np.exp(-GAMMA*cdist(self.Z, self.Z, 'sqeuclidean')), rtol=0, atol=0)

    def test_six_equals_thirty_six(self):
        A, B = self.Z[:3], self.Z[4:8]
        full = sum(kernel(permute_axes(A, p), permute_axes(B, q), 0) for p, q in itertools.product(PERMUTATIONS, repeat=2))/36
        np.testing.assert_allclose(kernel(A, B, 1), full, rtol=1e-13, atol=1e-14)

    def test_full_invariance_both_arguments(self):
        for p in PERMUTATIONS:
            np.testing.assert_allclose(kernel(permute_axes(self.Z, p), self.Z, 1), kernel(self.Z, self.Z, 1), atol=1e-14)
            np.testing.assert_allclose(kernel(self.Z, permute_axes(self.Z, p), 1), kernel(self.Z, self.Z, 1), atol=1e-14)

    def test_convex_mixture_and_psd(self):
        for alpha in (0, .5, 1):
            K = kernel(self.Z, self.Z, alpha)
            np.testing.assert_allclose(K, K.T, atol=1e-14)
            self.assertGreaterEqual(np.linalg.eigvalsh(K).min(), -1e-10)
        np.testing.assert_allclose(kernel(self.Z, self.Z, .5), (kernel(self.Z, self.Z, 0)+kernel(self.Z, self.Z, 1))/2)

    def test_diagonal_not_forced_to_one(self):
        for alpha in (0, .5, 1):
            np.testing.assert_allclose(kernel_diagonal(self.Z, alpha), np.diag(kernel(self.Z, self.Z, alpha)), atol=1e-14)
        self.assertTrue(np.any(kernel_diagonal(self.Z, 1) < .99))

    def test_block_invariance(self):
        np.testing.assert_array_equal(kernel(self.Z, self.Z, .5, 1), kernel(self.Z, self.Z, .5, 128))

    def test_empty_kernel_shape(self):
        self.assertEqual(kernel(self.Z[:0], self.Z, 1).shape, (0, len(self.Z)))
        self.assertEqual(kernel(self.Z, self.Z[:0], 1).shape, (len(self.Z), 0))

    def test_invalid_matrix_parameters(self):
        for bad in [np.ones((2, 65)), np.full((2, 66), np.nan), np.full((2, 66), np.inf)]:
            with self.assertRaises(ValueError):
                kernel(bad, self.Z, 1)
        for alpha, block in [(2, 128), (.2, 128), (float('nan'), 128), (1, 0)]:
            with self.assertRaises(ValueError):
                kernel(self.Z, self.Z, alpha, block)
        with self.assertRaises(ValueError):
            permute_axes(self.Z, (0, 0, 1))

    def test_overflow_rejected(self):
        X = np.full((2, 66), 1e308)
        with self.assertRaises(ValueError):
            kernel(X, -X, 1)
        X[:, :22] *= -1
        with self.assertRaises(ValueError):
            kernel_diagonal(X, 1)

    def test_classifier_and_centroid_hand_formula(self):
        m = AxisKernelClassifier(.5, 0).fit(self.Z, self.y)
        pred, D = m.infer(self.Z[:4])
        K = kernel(self.Z[:4], self.Z, .5)
        T = kernel(self.Z, self.Z, .5)
        expected = np.column_stack([kernel_diagonal(self.Z[:4], .5)-2*K[:, self.y == c].mean(1)+T[np.ix_(self.y == c, self.y == c)].mean() for c in range(3)])
        np.testing.assert_allclose(D, expected)
        np.testing.assert_array_equal(pred, m.classifier_.predict(K))
        self.assertEqual(m.infer(self.Z[:0])[1].shape, (0, 3))

    def test_same_config_seed_deterministic(self):
        a = AxisKernelClassifier(1, 0).fit(self.Z, self.y)
        b = AxisKernelClassifier(1, 0).fit(self.Z, self.y)
        self.assertEqual(a.checksum_, b.checksum_)
        np.testing.assert_array_equal(a.predict(self.Z), b.predict(self.Z))

    def test_actual_source_reconstruction(self):
        m = AxisKernelClassifier(.5, 0).fit(self.Z, self.y)
        self.assertEqual(m.verify_known_source(self.Z, self.y)['test_numeric_reads'], 0)
        Z = self.Z.copy()
        Z[0, 0] += .1
        with self.assertRaises(ValueError):
            m.verify_known_source(Z, self.y)

    def test_resealed_weights_rejected_by_actual_fit(self):
        m = AxisKernelClassifier(.5, 0).fit(self.Z, self.y)
        m.classifier_.intercept_[0] += .1
        m.checksum_ = m.signature()
        with self.assertRaisesRegex(ValueError, 'reconstruction'):
            m.verify_known_source(self.Z, self.y)

    def test_private_state_tamper(self):
        m = AxisKernelClassifier(.5, 0).fit(self.Z, self.y)
        m.classifier_._intercept_[0] += .1
        with self.assertRaises(ValueError):
            m.predict(self.Z)

    def test_invalid_classifier_labels(self):
        for y in [self.y[:-1], np.ones(len(self.Z), int), self.y.astype(float)]:
            with self.assertRaises(ValueError):
                AxisKernelClassifier(.5, 0).fit(self.Z, y)

    def test_nonconvergence_refused(self):
        def failed_fit(c, X, y):
            c.fit_status_ = 1
            return c
        with patch('core.fault_type_axis_kernel.SVC.fit', failed_fit):
            with self.assertRaisesRegex(RuntimeError, 'INCOMPLETE'):
                AxisKernelClassifier(.5, 0).fit(self.Z, self.y)

    def test_centroid_q_linear_zero_and_tie(self):
        D = np.array([[0., 2.], [1., 2.], [2., 3.]])
        m = KernelCentroidRejection().calibrate(D)
        self.assertEqual(m.quantile_, 1.9)
        np.testing.assert_array_equal(m.score_samples(D), [0, 1, 2])
        z = KernelCentroidRejection().calibrate(np.zeros((3, 2)))
        self.assertEqual(z.quantile_, 0)
        self.assertFalse((z.score_samples(np.zeros((1, 2))) > z.quantile_)[0])

    def test_centroid_invalid_and_empty(self):
        for D in [np.empty((0, 2)), np.ones((2, 1)), np.array([[0., -1.]]), np.full((2, 2), np.nan)]:
            with self.assertRaises(ValueError):
                KernelCentroidRejection().calibrate(D)
        m = KernelCentroidRejection().calibrate(np.ones((2, 2)))
        self.assertEqual(len(m.score_samples(np.empty((0, 2)))), 0)
        m.quantile_ += .1
        with self.assertRaises(ValueError):
            m.score_samples(np.ones((2, 2)))


class TestAxisRunner(unittest.TestCase):
    def setUp(self):
        self.X,self.C = formal(n=18),formal(seed=123,n=18)
        self.y,self.cy = np.arange(18)%3,np.arange(18)%3
        self.p=dict(factory_parameters=DETECTOR_CONFIG)
        rep=SharedAxisRepresentation().fit(self.X)
        self.b=dict(representation=rep,nodes=K.fit_nodes(rep.transform(self.X),rep.transform(self.C),self.y,0))
        base=LiteratureRepresentation('base75',0).fit(self.X,self.y)
        Z,C=base.transform(self.X),base.transform(self.C)
        self.parent=dict(references={'base75/mixed':dict(transformer=base,detectors={method:
            create_openset_detector(method,**DETECTOR_CONFIG).fit(Z,self.y,C,self.cy) for method in ['mahalanobis','knn']})})

    def test_source_rebuilds_scaler_svc_centroid_and_factory(self):
        verified=K.verify_actual_sources(self.b,self.parent,self.X,self.C,self.y,self.cy,self.p,0)
        self.assertEqual(len(verified),3)
        self.assertTrue(all(a['test_numeric_reads']==0 for a in verified.values()))

    def test_changed_calibration_rejected(self):
        C=self.C.copy();C[0,15]+=.1
        with self.assertRaises(ValueError):
            K.verify_actual_sources(self.b,self.parent,self.X,C,self.y,self.cy,self.p,0)

    def test_resealed_threshold_rejected(self):
        n=self.b['nodes']['alpha1']['rejector'];n.quantile_+=.1;n.checksum_=n.signature()
        with self.assertRaises(ValueError):
            K.verify_actual_sources(self.b,self.parent,self.X,self.C,self.y,self.cy,self.p,0)

    def test_changed_factory_reference_rejected(self):
        self.parent['references']['base75/mixed']['detectors']['knn'].models_[0].neighbors._fit_X[0,0]+=.1
        with self.assertRaisesRegex(ValueError,'factory'):
            K.verify_actual_sources(self.b,self.parent,self.X,self.C,self.y,self.cy,self.p,0)

    def test_classifier_shared_across_three_rejectors(self):
        values=K.infer(self.parent,self.b,self.p,self.C)
        self.assertEqual(len(values),9)
        for start in range(0,9,3):
            ids=[K.ARMS[i]['id'] for i in range(start,start+3)]
            np.testing.assert_array_equal(values[ids[0]][0],values[ids[1]][0])
            np.testing.assert_array_equal(values[ids[0]][0],values[ids[2]][0])
        np.testing.assert_array_equal(values['K01'][1],values['K04'][1])
        np.testing.assert_array_equal(values['K02'][1],values['K08'][1])

    def test_failed_fits_stay_incomplete(self):
        with patch.object(AxisKernelClassifier,'fit',side_effect=RuntimeError('SYNTHETIC_NONCONVERGENCE')):
            nodes=K.fit_nodes(self.b['representation'].transform(self.X),self.b['representation'].transform(self.C),self.y,0)
        self.assertTrue(all(n['status']=='INCOMPLETE' and n['model'] is None for n in nodes.values()))

    def test_comparisons_have_fixed_alpha_controls(self):
        pairs=K.paired_methods(['C02','C17','C24','D01'])
        self.assertEqual(len(pairs),42)
        self.assertIn(('K04','K01'),pairs)
        self.assertIn(('K09','K03'),pairs)
        self.assertFalse(any(old=='K09' for _,old in pairs))

    def test_policy_and_resealed_parameters_rejected(self):
        p=dict(version='exp19_axis_invariant_kernel_v1',parameters=K.normalized(K.PARAMETERS),arms=K.ARMS,
            budget=K.BUDGET,reliability_contract=K.CONTRACT,selection_policy='none',selection_sample_ids=[],
            validation_sample_ids=[],shared_validation_calibration=False,fresh_final_test=False,
            scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED')
        for change in [dict(global_winner='K09'),dict(selection_sample_ids=['outer']),dict(shared_validation_calibration=True),dict(fresh_final_test=True)]:
            with self.assertRaises(ValueError):
                K.check(seal(dict(p,**change),'protocol_checksum'))
        p['parameters']['gamma']=2/66
        with self.assertRaisesRegex(ValueError,'definitions'):
            K.check(seal(p,'protocol_checksum'))


class TestAxisPurpose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        priors,ledger=fixture(Path(cls.temp.name)/'data')
        protocol=build_protocol(priors,ledger)
        cls.m=fixed_manifests(priors,protocol)[0]
        cls.p=dict(protocol_checksum='SYNTHETIC',dataset_fingerprint='SYNTHETIC_FIXTURE_ONLY',
            known_labels=[cls.m['healthy_label'],*cls.m['known_fault_labels']])
        cls.pa=dict(seed=0,sha256='SYNTHETIC')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_train_cal_and_empty_selection_audits(self):
        audits=K.expected_audits(self.p,self.m,self.pa)
        self.assertEqual(len(audits),9)
        for a in audits:
            for field in ['scaler_fit_ids','representation_fit_ids','classifier_fit_ids','reference_fit_ids','support_reference_ids']:
                self.assertEqual(a[field],self.m['sample_ids']['train'])
            self.assertEqual(a['calibration_sample_ids'],self.m['sample_ids']['calibration'])
            self.assertEqual(a['selection_sample_ids'],[])

    def test_unknown_and_test_motor_in_development_rejected(self):
        for part in ['train','calibration']:
            for key,value in [('label',self.m['unknown_test_labels'][0]),('t_code',self.m['motor_roles']['test'])]:
                m=copy.deepcopy(self.m);sid=m['sample_ids'][part][0]
                next(r for r in m['records'] if r['sample_id']==sid)[key]=value
                m['manifest_checksum']=compute_manifest_checksum(m)
                with self.assertRaises(ValueError):
                    K.expected_audits(self.p,m,self.pa)


if __name__ == '__main__':
    unittest.main()
