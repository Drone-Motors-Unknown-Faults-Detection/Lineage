import copy
import unittest
from experiments.fault_type_continuous_report_v2 import paired_delta


class PartialReportTests(unittest.TestCase):
    def fixture(self):
        return {'metrics':{'known_classification':{'accuracy':.3},'known_fault_classification':{'accuracy':.2},
            'unknown_rejection':{'unknown_recall':.1},'healthy_safety_v2':{'healthy_total_alarm_rate':.4}}}
    def test_partial_method_needs_no_global_table(self):
        old=self.fixture();new=copy.deepcopy(old);new['metrics']['known_fault_classification']['accuracy']=.25
        delta=paired_delta(new,old);self.assertAlmostEqual(delta['fault_accuracy'],5.)
        self.assertEqual(delta['known_accuracy'],0.)
    def test_missing_is_not_zero(self):
        old=self.fixture();new=copy.deepcopy(old);new['metrics']['unknown_rejection']['unknown_recall']=None
        self.assertIsNone(paired_delta(new,old)['unknown_recall'])
