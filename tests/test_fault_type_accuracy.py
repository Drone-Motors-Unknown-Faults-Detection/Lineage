import unittest
import numpy as np
from core.fault_type_accuracy import verify_redundancy, VIBRATION66, study_metrics


class AccuracyHelpersTests(unittest.TestCase):
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
