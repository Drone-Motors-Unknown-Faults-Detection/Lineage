import unittest
import numpy as np
from core.fault_type_accuracy import verify_redundancy, VIBRATION66, study_metrics


class AccuracyHelpersTests(unittest.TestCase):
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
