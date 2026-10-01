import copy
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from core.fault_type_features import FeatureStore
from core.fault_type_fixed_calibration import fixed_manifests,audit_fixed_fit,fixed_dependency
from core.fault_type_final_guard import seal,digest
from core.fault_type_validator import compute_manifest_checksum,validate_split_manifest
from core.openset import create_openset_detector
from experiments.fault_type_fixed_calibration import build_protocol,check_protocol,run,evaluate,raw_class_scores,metrics_for,load_bound_model
from experiments.fault_type_fixed_smoke import fixture
from experiments.fault_type_fixed_report import verify_report,load_predictions,verify_rows


def reseal(m):
    m['manifest_checksum']=compute_manifest_checksum(m)
    return m


class FixedCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        cls.priors,cls.ledger=fixture(cls.root/'data')
        cls.protocol=build_protocol(cls.priors,cls.ledger)
        cls.manifests=fixed_manifests(cls.priors,cls.protocol)
        cls.pool=FeatureStore(cls.root/'data')
        cls.locked=run(cls.pool,manifests=cls.manifests,protocol=cls.protocol,ledger=cls.ledger,output=cls.root/'fit')
        cls.report=evaluate(cls.pool,manifests=cls.manifests,protocol=cls.protocol,ledger=cls.ledger,locked=cls.locked,output=cls.root/'eval',trusted_root=cls.root)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_empty_validation_no_selection_incomplete_not_pass(self):
        for m in self.manifests:
            self.assertEqual(m['sample_ids']['validation'],[])
            self.assertEqual(m['selection_sample_ids'],[])
            self.assertEqual(validate_split_manifest(m)['status'],'INCOMPLETE')
        self.assertEqual(len(self.report['runs']),36)

    def test_old_missing_validation_still_invalid(self):
        m=copy.deepcopy(self.priors[0]); m['sample_ids']['validation']=[]
        self.assertIn('TEST_NOT_REPRODUCIBLE',validate_split_manifest(reseal(m))['error_codes'])

    def test_test_ids_cannot_enter_train_or_cal(self):
        for part in ['train','calibration']:
            m=copy.deepcopy(self.manifests[0]); m['sample_ids'][part].append(m['sample_ids']['test'][0])
            self.assertIn('TEST_GROUP_LEAKAGE',validate_split_manifest(reseal(m))['error_codes'])

    def test_wrong_motor_cannot_enter_train_or_cal(self):
        for part in ['train','calibration']:
            m=copy.deepcopy(self.manifests[0]); sid=m['sample_ids'][part][0]
            next(r for r in m['records'] if r['sample_id']==sid)['t_code']=m['motor_roles']['test']
            self.assertIn('TEST_GROUP_LEAKAGE',validate_split_manifest(reseal(m))['error_codes'])

    def test_unknown_in_fit_or_cal_refused(self):
        for part in ['train','calibration']:
            m=copy.deepcopy(self.manifests[0]); sid=m['sample_ids'][part][0]
            next(r for r in m['records'] if r['sample_id']==sid)['label']=m['unknown_test_labels'][0]
            self.assertIn('UNKNOWN_LABEL_LEAKAGE',validate_split_manifest(reseal(m))['error_codes'])

    def test_calibration_cannot_enter_any_fitter(self):
        audits=json.loads(gzip.decompress(Path(self.locked['fit_audit_artifact']['path']).read_bytes()))
        for key in ['scaler_fit_ids','representation_fit_ids','classifier_fit_ids','reference_fit_ids','covariance_fit_ids','neighbor_reference_ids']:
            a=copy.deepcopy(audits[0]); a[key]+=a['calibration_sample_ids'][:1]
            with self.assertRaisesRegex(ValueError,key): audit_fixed_fit(a,self.manifests[0])

    def test_shared_validation_or_global_winner_refused(self):
        for changes in [dict(shared_validation_calibration=True),dict(global_winner='vibration75'),dict(selected_representation='baseline105'),dict(selection_sample_ids=['test-id']),dict(selection_policy='mean')]:
            m=copy.deepcopy(self.manifests[0]); m.update(changes)
            self.assertIn('TEST_USED_FOR_SELECTION',validate_split_manifest(reseal(m))['error_codes'])

    def test_rotation_allowed_history_retained(self):
        result=fixed_dependency(self.manifests)
        self.assertEqual(result['selection_ids'],0)
        self.assertEqual(result['status'],'NO_RECORDED_SELECTION_TEST_ID_OVERLAP')
        self.assertTrue(result['historical_test_exposed'])

    def test_config_tamper_and_resealed_budget_change_refused(self):
        for changes in [dict(seeds=[2]),dict(methods=['knn']),dict(selection_sample_ids=['x'])]:
            p=copy.deepcopy(self.protocol); p.update(changes)
            with self.assertRaises(ValueError): check_protocol(p,self.manifests,self.ledger)
            with self.assertRaises(ValueError): check_protocol(seal(p,'protocol_checksum'),self.manifests,self.ledger)

    def test_manifest_tamper_and_role_changes_refused(self):
        m=copy.deepcopy(self.manifests); m[0]['records'][0]['rpm']='tampered'
        with self.assertRaises(ValueError): check_protocol(self.protocol,m,self.ledger)

    def test_model_sha_tampering_refused(self):
        a=dict(self.locked['training_artifacts'][0],sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'checksum'): load_bound_model(a,self.root)
        with self.assertRaisesRegex(ValueError,'untrusted'): load_bound_model(self.locked['training_artifacts'][0],self.root/'other')

    def test_locked_winner_and_audit_sha_refused(self):
        for changes in [dict(global_winner='baseline105'),dict(unknown_labels=[]),dict(exposure_ledger_checksum='0'*64),dict(fit_audit_artifact=dict(self.locked['fit_audit_artifact'],sha256='0'*64))]:
            lock=seal(dict(self.locked,**changes),'locked_checksum')
            with self.assertRaises(ValueError): evaluate(self.pool,manifests=self.manifests,protocol=self.protocol,ledger=self.ledger,locked=lock,output=self.root/'rejected',trusted_root=self.root)

    def test_fit_does_not_load_validation_or_unknown_or_test(self):
        allowed=set().union(*(set(m['sample_ids']['train']+m['sample_ids']['calibration']) for m in self.manifests))
        # Across folds all samples become test, so check per loading call by motor
        # and known membership, not union of test IDs across rotated folds.
        actual=[]
        expected=[m['sample_ids'][p] for m in self.manifests for p in ['train','calibration']]
        class Spy:
            def load(inner,records):
                self.assertTrue({r['sample_id'] for r in records}<=allowed)
                self.assertTrue(all(r['label'] in self.locked['known_labels'] for r in records))
                self.assertEqual(len({r['t_code'] for r in records}),1)
                self.assertEqual([r['sample_id'] for r in records],expected[len(actual)])
                actual.append(len(records))
                return self.pool.load(records)
        lock=run(Spy(),manifests=self.manifests,protocol=self.protocol,ledger=self.ledger,output=self.root/'fit2')
        self.assertEqual(len(actual),6)
        self.assertEqual(len(lock['training_artifacts']),18)

    def test_factory_references_not_changed_by_calibration(self):
        X=np.random.default_rng(1).normal(size=(20,5)); y=np.zeros(20,dtype=int)
        for method in ['mahalanobis','knn']:
            a=create_openset_detector(method).fit(X,y,X+1,y)
            b=create_openset_detector(method).fit(X,y,X+100,y)
            if method=='mahalanobis':
                np.testing.assert_array_equal(a.distributions_[0].location,b.distributions_[0].location)
                np.testing.assert_array_equal(a.distributions_[0].precision,b.distributions_[0].precision)
            else: np.testing.assert_array_equal(a.models_[0].neighbors._fit_X,b.models_[0].neighbors._fit_X)
            self.assertNotEqual(a.class_summaries()[0]['threshold'],b.class_summaries()[0]['threshold'])

    def test_zero_threshold_and_factory_decomposition(self):
        X=np.zeros((8,3)); y=np.zeros(8,dtype=int)
        for method in ['mahalanobis','knn']:
            d=create_openset_detector(method).fit(X,y,X,y)
            raw,threshold,ratios,labels=raw_class_scores(d,X)
            self.assertTrue(np.isfinite(ratios).all())
            self.assertTrue(np.isfinite(d.score_samples(X)).all())
            self.assertEqual(labels,[0])

    def test_known_accuracy_shared_across_detectors_and_pair_ids(self):
        by={r['run_id']:r for r in self.report['runs']}
        for r in self.report['runs']:
            if r['method']=='knn': continue
            mate=by[r['run_id'].replace('_mahalanobis_','_knn_')]
            self.assertEqual(r['test_ids_checksum'],mate['test_ids_checksum'])
            self.assertEqual(r['metrics']['known_classification'],mate['metrics']['known_classification'])

    def test_seed_determinism_and_no_winner(self):
        for r in self.report['runs']:
            if r['seed']!=0: continue
            mates=[x for x in self.report['runs'] if (x['fold_id'],x['representation'],x['method'])==(r['fold_id'],r['representation'],r['method'])]
            self.assertEqual(len(mates),3)
            self.assertTrue(all(x['metrics']==r['metrics'] for x in mates))
        self.assertNotIn('selected_representation',self.locked)
        self.assertNotIn('global_winner',self.report)

    def test_repeated_same_source_config_predictions_identical(self):
        second=evaluate(self.pool,manifests=self.manifests,protocol=self.protocol,ledger=self.ledger,locked=self.locked,output=self.root/'repeat',trusted_root=self.root)
        self.assertEqual([r['prediction_artifact']['sha256'] for r in self.report['runs']],
                         [r['prediction_artifact']['sha256'] for r in second['runs']])

    def test_conditions_and_unknown_prevalence(self):
        self.assertEqual(len(self.protocol['conditions']),9)
        self.assertEqual(len(self.report['runs'][0]['rpm_metrics']),3)
        self.assertEqual(self.report['runs'][0]['metrics']['unknown_prevalence'],.4)
        self.assertEqual(len(self.report['runs'][0]['configuration_metrics']),10)

    def test_original_sources_and_manifests_unchanged(self):
        for prior in self.priors:
            self.assertTrue(prior['shared_validation_calibration'])
            self.assertTrue(prior['sample_ids']['validation'])
            self.assertEqual(prior['schema_version'],1)
        self.assertEqual(self.locked['exposure_ledger_checksum'],self.ledger['ledger_checksum'])

    def test_saved_prediction_verification_and_fixed_aggregator(self):
        result,_=verify_report(self.report,manifests=self.manifests,protocol=self.protocol,locked=self.locked)
        self.assertEqual(result['completed_evaluations'],36)
        self.assertEqual(result['unique_test_sample_ids'],1080)
        self.assertEqual(result['prediction_records'],12960)
        self.assertEqual(len(result['methods']),4)
        self.assertNotIn('selected_representation',result)

    def test_prediction_sha_tamper_refused(self):
        a=dict(self.report['runs'][0]['prediction_artifact'],sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'prediction SHA'): load_predictions(a)

    def test_score_direction_truth_and_condition_tamper_refused(self):
        run=self.report['runs'][0]; rows=load_predictions(run['prediction_artifact'])
        wrong_role='healthy' if rows[0]['true_role']=='unknown_test' else 'unknown_test'
        for change in [dict(is_unknown=not rows[0]['is_unknown']),dict(true_role=wrong_role),dict(rpm='bad'),dict(openset_score=-1),dict(nearest_known_class='bad')]:
            bad=copy.deepcopy(rows); bad[0].update(change)
            with self.subTest(change=change):
                with self.assertRaises(ValueError): verify_rows(bad,run,self.manifests[0],self.protocol,self.locked)

    def test_saved_metrics_and_incomplete_grid_refused(self):
        bad=copy.deepcopy(self.report); bad['runs'][0]['metrics']['known_classification']['accuracy']=99
        with self.assertRaisesRegex(ValueError,'metrics'): verify_report(seal(bad,'evaluation_checksum'),manifests=self.manifests,protocol=self.protocol,locked=self.locked)
        bad=copy.deepcopy(self.report); bad['runs'].pop()
        with self.assertRaisesRegex(ValueError,'inventory'): verify_report(seal(bad,'evaluation_checksum'),manifests=self.manifests,protocol=self.protocol,locked=self.locked)


if __name__=='__main__': unittest.main()
