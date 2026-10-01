import unittest
import numpy as np
from core.fault_type_accuracy import verify_redundancy, VIBRATION66, study_metrics
from core.fault_type_accuracy_pipeline import StudyRepresentation, check_cell, records_for, validate_node_audit


class AccuracyHelpersTests(unittest.TestCase):
    def test_signed_log_scale_zero_sign_inverse_train_only(self):
        from experiments.fault_type_accuracy_registry import ARMS
        from sklearn.preprocessing import RobustScaler
        X=np.ones((10,105));X[:,15]=0;X[:,27]=0;X[:,16]=np.arange(-5,5)
        transform=StudyRepresentation(ARMS[4],RobustScaler().get_params()).fit(X)
        self.assertEqual(transform.signed_scale[0],1e-12)
        signed=transform._signed(X[:,VIBRATION66])
        np.testing.assert_allclose(transform.inverse_signed(signed),X[:,VIBRATION66],atol=1e-12)
        checksum=transform.transform_checksum
        self.assertTrue(np.isfinite(transform.transform(X*1e100)).all())
        self.assertEqual(transform.transform_checksum,checksum)
        transform.scaler.center_[0]+=1
        with self.assertRaisesRegex(ValueError,'tampered'): transform.transform(X)

    def test_axis_mapping_dimension_and_finite(self):
        from experiments.fault_type_accuracy_registry import ARMS
        from sklearn.preprocessing import RobustScaler
        arm=dict(ARMS[3],indices=list(reversed(VIBRATION66)))
        with self.assertRaisesRegex(ValueError,'axis'): StudyRepresentation(arm,RobustScaler().get_params()).fit(np.ones((5,105)))
        t=StudyRepresentation(ARMS[3],RobustScaler().get_params()).fit(np.ones((5,105)))
        self.assertEqual(t.transform(np.ones((5,105))).shape,(5,66))
        with self.assertRaises(ValueError): t.transform(np.full((5,105),np.nan))

    def test_missing_cal_class_and_minimum_reference(self):
        train=[{'label':'a'}]*5+[{'label':'b'}]*5
        cal=[{'label':'a'},{'label':'b'}]
        self.assertEqual(check_cell(train,cal,['a','b'])['train']['a'],5)
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):check_cell(train,cal[:1],['a','b'])
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):check_cell(train[:5],cal,['a','b'])

    def test_fixed_classifiers_fit_only_train_with_no_early_stop(self):
        from experiments.fault_type_accuracy_registry import classifier
        rng=np.random.default_rng(1);X=rng.normal(size=(60,6));y=np.repeat(np.arange(3),20)
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=1):
            for name in ['linear','extra_trees','hist_gradient','shrinkage_lda','rbf_svm']:
                model=classifier(name,1,3).fit(X,y)
                self.assertEqual(model.predict(X).shape,(60,))
                if name=='hist_gradient':self.assertFalse(model.do_early_stopping_)

    def test_preregistered_budget_and_classifier_parameters(self):
        from experiments.fault_type_accuracy_registry import ARMS, SCORES, classifier
        self.assertEqual((len(ARMS)-1)*3*3*2+len(SCORES)*3*3,198)
        hgb=classifier('hist_gradient',2,6).get_params()
        self.assertIs(hgb['early_stopping'],False)
        self.assertEqual(hgb['random_state'],2)
        self.assertEqual(hgb['class_weight'],'balanced')
        lda=classifier('shrinkage_lda',2,6).get_params()
        self.assertEqual(lda['solver'],'lsqr')
        self.assertEqual(lda['priors'],[1/6]*6)
        self.assertIs(classifier('rbf_svm',2,6).get_params()['probability'],False)

    def test_fixed_66_mapping_and_train_relations(self):
        X = np.ones((5,105))
        self.assertEqual(len(VIBRATION66),66)
        self.assertEqual(len(verify_redundancy(X)['checks']),9)
        X[:,22] = 2
        with self.assertRaisesRegex(ValueError,'contract mismatch'): verify_redundancy(X)

    def test_selective_zero_coverage_and_healthy_contribution(self):
        rows = [{'sample_id':'h','true_label':'h','predicted_known_class':'h','openset_score':2.,'is_unknown':True},
                {'sample_id':'f','true_label':'f','predicted_known_class':'h','openset_score':2.,'is_unknown':True},
                {'sample_id':'u','true_label':'u','predicted_known_class':'h','openset_score':2.,'is_unknown':True}]
        r = study_metrics(rows,['h','f'],['u'])
        self.assertIsNone(r['selective']['accuracy_all_accepted'])
        self.assertEqual(r['selective']['coverage'],0)
        self.assertEqual(r['healthy_contribution']['healthy_correct_fraction_of_all_known'],.5)
        self.assertEqual(r['known_fault_classification']['accuracy'],0)
        rows[-1]['is_unknown']=False
        r=study_metrics(rows,['h','f'],['u'])
        self.assertEqual(r['selective']['accuracy_all_accepted'],0)


if __name__=='__main__': unittest.main()
