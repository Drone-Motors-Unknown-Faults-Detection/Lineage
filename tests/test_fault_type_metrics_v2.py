import unittest
from core.fault_type_metrics_v2 import metrics_v2, decision


def example():
    # Nine mutually exclusive routes, three healthy / three fault / three unknown.
    pairs = [('H','H',False),('H','F',False),('H','F',True),
             ('F','F',False),('F','H',False),('F','F',True),
             ('U','H',False),('U','F',False),('U','F',True)]
    return [dict(sample_id=str(i), true_label=t, predicted_known_class=p,
                 openset_score=2. if rejected else 1., threshold=1., is_unknown=rejected)
            for i,(t,p,rejected) in enumerate(pairs)]


class MetricsV2Test(unittest.TestCase):
    def test_nine_routes(self):
        m=metrics_v2(example(), ['H','F'], ['U'])
        h=m['healthy_safety_v2']
        self.assertEqual(h['healthy_to_unknown_rate'], 1/3)
        self.assertEqual(h['healthy_to_known_fault_rate'], 1/3)
        self.assertEqual(h['healthy_total_alarm_rate'], 2/3)
        self.assertEqual(m['selective']['coverage'], 6/9)
        self.assertEqual(m['selective']['accuracy_all_accepted'], 2/6)
        self.assertEqual(m['known_correct_after_rejection'], 2/6)
        self.assertEqual(m['final_open_set_classification']['confusion_matrix'], [[1,1,1],[1,1,1],[1,1,1]])
        self.assertEqual(m['known_fault_classification']['confusion_matrix'], [[0,0],[1,2]])
        self.assertEqual(m['unknown_rejection']['unknown_recall'], 1/3)

    def test_signed_and_tie(self):
        self.assertEqual(decision('F', -2., -2.), 'F')
        self.assertEqual(decision('F', -1., -2.), 'unknown')

    def test_truth_independent_decision(self):
        row=example()[0]; a=decision(row['predicted_known_class'],row['openset_score'],row['threshold'])
        row['true_label']='U'
        self.assertEqual(a,decision(row['predicted_known_class'],row['openset_score'],row['threshold']))

    def test_missing_support(self):
        m=metrics_v2(example()[6:], ['H','F'], ['U'])
        self.assertIsNone(m['healthy_safety_v2']['healthy_total_alarm_rate'])
        self.assertIsNone(m['unknown_rejection']['auroc_unknown_positive'])
        self.assertIsNone(m['known_correct_after_rejection'])

    def test_all_rejected(self):
        rows=example()
        for r in rows:r['is_unknown']=True;r['openset_score']=2.
        m=metrics_v2(rows,['H','F'],['U'])
        self.assertEqual(m['selective']['coverage'],0.)
        self.assertIsNone(m['selective']['accuracy_all_accepted'])

    def test_mapping_guard(self):
        rows=example();rows[0]['predicted_known_class']='U'
        with self.assertRaises(ValueError):metrics_v2(rows,['H','F'],['U'])

    def test_duplicate_guard(self):
        rows=example();rows[1]['sample_id']=rows[0]['sample_id']
        with self.assertRaises(ValueError):metrics_v2(rows,['H','F'],['U'])

    def test_rejection_guard(self):
        rows=example();rows[0]['is_unknown']=True
        with self.assertRaises(ValueError):metrics_v2(rows,['H','F'],['U'])

    def test_final_guard(self):
        rows=example();rows[0]['final_decision']='unknown'
        with self.assertRaises(ValueError):metrics_v2(rows,['H','F'],['U'])

    def test_nonfinite(self):
        with self.assertRaises(ValueError):decision('H',float('nan'),1.)

    def test_empty_and_zero_alarms(self):
        m=metrics_v2([],['H','F'],['U'])
        self.assertIsNone(m['selective']['coverage'])
        m=metrics_v2(example()[:1],['H','F'],['U'])
        self.assertEqual(m['healthy_safety_v2']['healthy_total_alarm_rate'],0.)

    def test_class_order(self):
        m=metrics_v2(example(),['H','F'],['U'])
        self.assertEqual(m['known_fault_classification']['per_class'][0]['label'],'F')
        self.assertEqual(m['known_fault_classification']['per_class'][0]['recall'],2/3)

    def test_constraint_does_not_tune(self):
        m=metrics_v2(example(),['H','F'],['U'],healthy_limit=.1)
        self.assertFalse(m['healthy_safety_v2']['fixed_point_constraint_satisfied'])
        self.assertIsNone(m['healthy_safety_v2']['unknown_recall_at_fixed_point_under_constraint'])
