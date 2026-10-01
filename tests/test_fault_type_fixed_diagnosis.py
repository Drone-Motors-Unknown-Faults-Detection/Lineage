import unittest
import numpy as np
from experiments.fault_type_fixed_diagnosis import score_groups,healthy_shift,run


class FixedDiagnosisTests(unittest.TestCase):
    def test_raw_and_normalized_distributions_keep_class_thresholds(self):
        records=[{'sample_id':str(i),'label':'h' if i<2 else 'u','rpm':'6000rpm'} for i in range(4)]
        raw=np.array([[0.,1.],[1.,2.],[2.,3.],[3.,4.]])
        thresholds=np.array([1.,4.]); ratios=raw/thresholds
        groups=score_groups(records,raw,thresholds,ratios,[0,1],['h','k'])
        overall=next(g for g in groups if g['rpm']=='ALL' and g['configuration']=='ALL')
        self.assertEqual(overall['samples'],4)
        self.assertEqual(overall['rejection_rate'],0.)
        self.assertEqual(overall['normalized_min_score']['maximum'],1.)
        self.assertEqual(overall['per_reference_class'][1]['threshold'],4.)

    def test_same_rpm_shift_does_not_mix_unknown(self):
        parts={p:[{'label':'h','rpm':'6000rpm','t_code':t},{'label':'u','rpm':'6000rpm','t_code':t}] for p,t in [('train','T2'),('calibration','T3'),('test','T1')]}
        X={'train':np.array([[0.,0.],[999.,999.]]),'calibration':np.array([[2.,2.],[999.,999.]]),'test':np.array([[1.,1.],[999.,999.]])}
        shift=healthy_shift(parts,X,'h')
        self.assertEqual([r['mean_absolute_median_shift_train_scaled_units'] for r in shift],[2.,1.])
        self.assertTrue(all(r['samples']==1 for r in shift))

    def test_missing_condition_is_na_not_invented(self):
        parts={'train':[{'label':'h','rpm':'r','t_code':'T2'}], 'calibration':[{'label':'k','rpm':'r','t_code':'T3'}], 'test':[{'label':'h','rpm':'r','t_code':'T1'}]}
        shift=healthy_shift(parts,{p:np.ones((1,2)) for p in parts},'h')
        self.assertEqual(shift[0]['status'],'NA_MISSING_HEALTHY')


if __name__=='__main__': unittest.main()
