import unittest
from experiments.fault_type_literature_report import historical_comparison


def method(acc=.3, auc=.6):
    return {'equal_motor_descriptive':{
        'known_fault_classification.accuracy':{'mean':acc},
        'unknown_rejection.auroc_unknown_positive':{'mean':auc}}}


class HistoricalScopeTests(unittest.TestCase):
    def test_exact_mixed_control(self):
        r=historical_comparison(method(),method(),'C02','A0','mahalanobis')
        self.assertTrue(r['matches'])
        self.assertTrue(r['classification_matches'])
        self.assertTrue(r['expected_entire_method_match'])

    def test_rpm_classifier_control_not_whole_detector_control(self):
        r=historical_comparison(method(auc=.5),method(),'C24','A7','knn')
        self.assertFalse(r['matches'])
        self.assertTrue(r['classification_matches'])
        self.assertFalse(r['expected_entire_method_match'])
        self.assertIn('shared the mixed-RPM',r['reference_scope_note'])

    def test_classification_mismatch_never_hidden(self):
        r=historical_comparison(method(acc=.2),method(),'C24','A7','mahalanobis')
        self.assertFalse(r['classification_matches'])
        self.assertAlmostEqual(r['mean_differences']['known_fault_classification.accuracy'],-.1)
