"""Engineering checks for read-only summaries, not research performance."""
import unittest
import numpy as np
from experiments.fault_type_literature_diagnosis import distribution, summarize


class DiagnosisTests(unittest.TestCase):
    def test_signed_threshold_strict_and_unchanged(self):
        x=np.array([-3.,-2.,-1.]);before=x.copy()
        d=distribution(x,-2.)
        self.assertEqual(d['reject_rate'],1/3)
        self.assertEqual(d['median_minus_threshold'],0.)
        np.testing.assert_array_equal(x,before)

    def test_zero_threshold_safe(self):
        d=distribution([-1.,0.,1.],0.)
        self.assertEqual(d['reject_rate'],1/3)
        self.assertEqual(d['threshold'],0.)

    def test_invalid_scores_rejected(self):
        for x,t in [([],0),([np.nan],0),([1],np.inf),([[1]],0)]:
            with self.assertRaises(ValueError):distribution(x,t)

    def test_truth_groups_only_for_report_and_rpm_coverage(self):
        records=[{'label':'healthy','rpm':'6000rpm'},
                 {'label':'known','rpm':'8000rpm'},
                 {'label':'unknown','rpm':'6000rpm'}]
        groups=summarize(records,[0.,2.,3.],1.,['healthy','known'])
        all_group=next(g for g in groups if g['label']=='all' and g['rpm']=='all')
        self.assertEqual(all_group['samples'],3)
        unknown=next(g for g in groups if g['label']=='unknown' and g['rpm']=='all')
        self.assertEqual(unknown['class_role'],'unknown_fault')
        self.assertEqual(unknown['reject_rate'],1.)
        with self.assertRaises(ValueError):summarize(records,[1],1.,['healthy','known'])
