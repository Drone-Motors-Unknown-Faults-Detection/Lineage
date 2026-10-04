"""exp21用途／遮蔽歷史／重封篡改測試，全部合成資料。"""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from experiments import fault_type_self_challenging as M
from core.fault_type_risk_extrapolation import RiskExtrapolationClassifier
from core.fault_type_literature import LiteratureRepresentation
from core.openset import create_openset_detector
from core.fault_type_final_guard import seal,digest
from core.fault_type_validator import compute_manifest_checksum
from core.fault_type_fixed_calibration import fixed_manifests
from experiments.fault_type_fixed_calibration import build_protocol
from experiments.fault_type_fixed_smoke import fixture
from experiments.fault_type_openset import DETECTOR_CONFIG
from tests.test_fault_type_axis_kernel import formal


class TestChallengeRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.X,cls.C=formal(n=36),formal(seed=123,n=36)
        cls.y=cls.cy=np.arange(36)%3
        cls.env=np.repeat(['6000rpm','8000rpm','11000rpm'],12)
        cls.p=dict(factory_parameters=DETECTOR_CONFIG)
        cls.original=dict(nodes=M.fit_nodes(cls.X,cls.C,cls.y,cls.env,0))
        if any(n['status']!='completed' for n in cls.original['nodes'].values()):
            raise AssertionError('synthetic fixed-horizon fit did not complete')
        base=LiteratureRepresentation('base75',0).fit(cls.X,cls.y)
        Z,C=base.transform(cls.X),base.transform(cls.C)
        cls.parent_original=dict(references={'base75/mixed':dict(transformer=base,detectors={
            method:create_openset_detector(method,**DETECTOR_CONFIG).fit(Z,cls.y,C,cls.cy)
            for method in ['mahalanobis','knn']})})

    def setUp(self):
        self.b=copy.deepcopy(self.original)
        self.parent=copy.deepcopy(self.parent_original)

    def proof(self,**change):
        args=dict(b=self.b,parent=self.parent,X=self.X,C=self.C,y=self.y,cy=self.cy,env=self.env,p=self.p,seed=0)
        args.update(change)
        return M.verify_actual_sources(**args)

    def test_full_known_source_replay(self):
        verified=self.proof()
        self.assertEqual(len(verified),8)
        self.assertTrue(all(x['test_numeric_reads']==0 for x in verified.values()))

    def test_changed_calibration_rejected(self):
        C=self.C.copy();C[0,15]+=.1
        with self.assertRaises(ValueError):self.proof(C=C)

    def test_resealed_msp_threshold_rejected(self):
        n=self.b['nodes']['base75_signed_gradient']
        n['rejector'].threshold+=.1;n['node_checksum']=M.node_signature(n)
        with self.assertRaises(ValueError):self.proof()

    def test_resealed_coefficients_rejected(self):
        n=self.b['nodes']['base75_signed_gradient'];m=n['model']
        m.coef_[0,0]+=.1;m.checksum_=m.signature();n['node_checksum']=M.node_signature(n)
        with self.assertRaises(ValueError):self.proof()

    def test_resealed_environment_source_rejected(self):
        n=self.b['nodes']['base75_signed_gradient'];m=n['model']
        m.source_['environments']='RESEALED';m.checksum_=m.signature();n['node_checksum']=M.node_signature(n)
        with self.assertRaises(ValueError):self.proof()

    def test_resealed_scaler_flags_rejected(self):
        n=self.b['nodes']['harmonic69_signed_gradient'];n['representation'].scaler.with_centering=False
        n['node_checksum']=M.node_signature(n)
        with self.assertRaises(ValueError):self.proof()

    def test_actual_changed_train_rpm_rejected(self):
        env=self.env.copy();env[[0,12]]=env[[12,0]]
        with self.assertRaises(ValueError):self.proof(env=env)

    def test_changed_factory_reference_rejected(self):
        self.parent['references']['base75/mixed']['detectors']['knn'].models_[0].neighbors._fit_X[0,0]+=.1
        with self.assertRaisesRegex(ValueError,'factory'):self.proof()

    def test_shared_classifier_and_fixed_factory_scores(self):
        values=M.infer(self.parent,self.b,self.p,self.C)
        self.assertEqual(len(values),24)
        for start in range(0,24,3):
            ids=[M.ARMS[i]['id'] for i in range(start,start+3)]
            for method in ids[1:]:np.testing.assert_array_equal(values[ids[0]][0],values[method][0])
            np.testing.assert_array_equal(values[ids[0]][1],values['M01'][1])
        np.testing.assert_array_equal(values['M02'][1],values['M23'][1])

    def test_msp_zero_threshold_and_strict_tie(self):
        n=self.b['nodes']['base75_unmasked'];m=n['model']
        m.coef_[:]=0;m.intercept_[:]=[1000.,0.,0.];m.checksum_=m.signature()
        Z=n['representation'].transform(self.C);n['rejector'].calibrate(Z)
        n['calibration_score_checksum']=M.array_checksum(n['rejector'].raw(Z));n['node_checksum']=M.node_signature(n)
        pred,score,q=M.infer(self.parent,self.b,self.p,self.C)['M03']
        self.assertEqual(q,0);np.testing.assert_array_equal(score,0)
        self.assertFalse((score>q).any())

    def test_failed_erm_does_not_attempt_challenge(self):
        with patch.object(RiskExtrapolationClassifier,'fit',side_effect=RuntimeError('SYNTHETIC_NONCONVERGENCE')) as fit:
            nodes=M.fit_nodes(self.X,self.C,self.y,self.env,0)
        self.assertEqual(fit.call_count,2)
        self.assertTrue(all(n['status']=='INCOMPLETE' for n in nodes.values()))
        self.assertEqual(sum(n['optimizer_attempted'] for n in nodes.values()),0)

    def test_fixed_unmasked_and_random_pair_controls(self):
        pairs=M.paired_methods(['C02','C17','C24','D01'])
        self.assertEqual(len(pairs),126)
        self.assertIn(('M06','M03'),pairs);self.assertIn(('M24','M15'),pairs)
        self.assertIn(('M24','M18'),pairs)
        self.assertFalse(any(old=='M24' for _,old in pairs))

    def test_policy_and_resealed_optimizer_rejected(self):
        p=dict(version='exp21_feature_self_challenging_v1',parameters=M.normalized(M.PARAMETERS),arms=M.ARMS,
            budget=M.BUDGET,reliability_contract=M.CONTRACT,selection_policy='none',selection_sample_ids=[],
            validation_sample_ids=[],shared_validation_calibration=False,fresh_final_test=False,
            scope='EXPLORATORY_HISTORICAL_TEST_EXPOSED')
        for change in [dict(global_winner='M18'),dict(selection_sample_ids=['outer']),
                       dict(shared_validation_calibration=True),dict(fresh_final_test=True)]:
            with self.assertRaises(ValueError):M.check(seal(dict(p,**change),'protocol_checksum'))
        p['parameters']['warm_optimizer']['maxiter']=10000
        with self.assertRaisesRegex(ValueError,'definitions'):M.check(seal(p,'protocol_checksum'))

    def test_resealed_mask_history_rejected(self):
        n=self.b['nodes']['base75_random'];m=n['model']
        m.history_[0]['muted_features']+=1
        m.optimizer_['history_checksum']=M.digest(m.history_);m.checksum_=m.signature()
        n['node_checksum']=M.node_signature(n)
        with self.assertRaises(ValueError):self.proof()

    def test_resealed_warm_start_rejected(self):
        n=self.b['nodes']['harmonic69_signed_gradient'];warm=n['warm_start']
        warm.coef_[0,0]+=.1;warm.checksum_=warm.signature()
        n['model'].warm_start_checksum_=warm.checksum_;n['model'].checksum_=n['model'].signature()
        n['node_checksum']=M.node_signature(n)
        with self.assertRaises(ValueError):self.proof()

    def test_inference_does_not_build_train_masks(self):
        from core.fault_type_self_challenging import challenge_mask
        with patch('core.fault_type_self_challenging.challenge_mask',side_effect=AssertionError('mask at inference')):
            values=M.infer(self.parent,self.b,self.p,self.C)
        self.assertEqual(len(values),24)


class TestChallengePurpose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        priors,ledger=fixture(Path(cls.temp.name)/'data')
        cls.m=fixed_manifests(priors,build_protocol(priors,ledger))[0]
        cls.p=dict(protocol_checksum='SYNTHETIC',dataset_fingerprint='SYNTHETIC_FIXTURE_ONLY',
                   known_labels=[cls.m['healthy_label'],*cls.m['known_fault_labels']])
        cls.pa=dict(seed=0,sha256='SYNTHETIC')

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_only_train_rpm_loss_and_empty_selection(self):
        audits=M.expected_audits(self.p,self.m,self.pa)
        self.assertEqual(len(audits),24)
        for a in audits:
            for key in ['scaler_fit_ids','representation_fit_ids','classifier_fit_ids','reference_fit_ids']:
                self.assertEqual(a[key],self.m['sample_ids']['train'])
            self.assertEqual(a['calibration_sample_ids'],self.m['sample_ids']['calibration'])
            self.assertEqual(a['selection_sample_ids'],[])
            loss=[x for ids in a['loss_environment_ids'].values() for x in ids]
            self.assertEqual(set(loss),set(self.m['sample_ids']['train']))
            self.assertFalse(set(loss)&set(self.m['sample_ids']['calibration']))

    def test_unknown_or_test_motor_in_development_rejected(self):
        for part in ['train','calibration']:
            for key,value in [('label',self.m['unknown_test_labels'][0]),('t_code',self.m['motor_roles']['test'])]:
                m=copy.deepcopy(self.m);sid=m['sample_ids'][part][0]
                next(r for r in m['records'] if r['sample_id']==sid)[key]=value
                m['manifest_checksum']=compute_manifest_checksum(m)
                with self.assertRaises(ValueError):M.expected_audits(self.p,m,self.pa)

    def test_missing_training_rpm_class_is_incomplete(self):
        rows=[r for r in self.m['records'] if r['sample_id'] in set(self.m['sample_ids']['train'])]
        rows=[r for r in rows if not (r['rpm']=='6000rpm' and r['label']==self.p['known_labels'][0])]
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):M.check_rpm_coverage(rows,self.p['known_labels'])


if __name__=='__main__':unittest.main()
