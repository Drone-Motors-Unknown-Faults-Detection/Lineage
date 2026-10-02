import copy
import unittest
from core.fault_type_metrics_v2 import metrics_v2
from core.fault_type_reliability import assess, CONTRACT, check_contract


class ReliabilityTests(unittest.TestCase):
    def runs(self):
        rows = [{'sample_id':str(i),'true_label':t,'predicted_known_class':p,'openset_score':s,'threshold':1.,'is_unknown':s>1.}
                for i,(t,p,s) in enumerate([('8screws','8screws',0.),('2screws','2screws',0.),('U','8screws',2.)])]
        m = metrics_v2(rows,['8screws','2screws'],['U'])
        return [{'seed':s,'motor_roles':{'test':t},'metrics':copy.deepcopy(m),
                 'rpm_metrics':[{'rpm':r,'metrics':copy.deepcopy(m)} for r in ['6000rpm','8000rpm','11000rpm']]}
                for t in ['T1','T2','T3'] for s in [0,1,2]]
    def controls(self, rr):
        cc = {k:copy.deepcopy(rr) for k in ['C02','C17','C24','D01']}
        for r in cc['C17']: r['metrics']['known_fault_classification']['macro_f1'] = .5
        for r in cc['C24']: r['metrics']['known_fault_classification']['accuracy'] = .5
        return cc
    def test_no_C_and_B_requires_subsets(self):
        r=self.runs(); a=assess(r,self.controls(r)); self.assertEqual(a['main_screen'],'PASS'); self.assertFalse(a['evidence_B']); self.assertFalse(a['evidence_C'])
        self.assertTrue(assess(r,self.controls(r),subsets_verified=3)['evidence_B'])
    def test_full_health_not_unknown_only(self):
        r=self.runs(); cc=self.controls(r); r[0]['rpm_metrics'][0]['metrics']['healthy_safety_v2']['healthy_total_alarm_rate']=.11
        self.assertEqual(assess(r,cc)['main_screen'],'FAILED')
    def test_missing_cell_not_pass(self):
        r=self.runs(); cc=self.controls(r); r[0]['rpm_metrics'].pop(); self.assertEqual(assess(r,cc)['main_screen'],'INCOMPLETE')
    def test_duplicate_cell_rejected(self):
        r=self.runs(); cc=self.controls(r); r[0]['rpm_metrics'].append(r[0]['rpm_metrics'][0])
        with self.assertRaises(ValueError): assess(r,cc)
    def test_one_bad_seed_fails(self):
        r=self.runs(); cc=self.controls(r); r[1]['metrics']['known_fault_classification']['macro_f1']=0.
        self.assertEqual(assess(r,cc)['main_screen'],'FAILED')
    def test_one_bad_motor_not_hidden(self):
        r=self.runs(); cc=self.controls(r); r[0]['metrics']['unknown_rejection']['unknown_recall']=0.
        self.assertEqual(assess(r,cc)['main_screen'],'FAILED')
    def test_contract_cannot_move(self):
        c=dict(CONTRACT,healthy_total_alarm_max_each_motor_rpm=1.)
        with self.assertRaises(ValueError): check_contract(c)
    def test_missing_overall_is_incomplete_not_exception_or_pass(self):
        for field in ['macro_f1', 'accuracy']:
            r=self.runs(); cc=self.controls(r)
            r[0]['metrics']['known_fault_classification'][field]=None
            self.assertEqual(assess(r,cc)['main_screen'],'INCOMPLETE')
    def test_missing_control_motor_and_nan_are_incomplete(self):
        r=self.runs(); cc=self.controls(r); cc['C17'].pop()
        self.assertEqual(assess(r,cc)['main_screen'],'INCOMPLETE')
        cc=self.controls(r); cc['C24'][0]['metrics']['known_fault_classification']['accuracy']=float('nan')
        self.assertEqual(assess(r,cc)['main_screen'],'INCOMPLETE')
    def test_unknown_noninferiority(self):
        r=self.runs(); cc=self.controls(r); r[0]['rpm_metrics'][0]['metrics']['unknown_rejection']['unknown_recall']=.9
        self.assertTrue(any('noninferiority' in v for v in assess(r,cc)['reasons']))
    def test_postrejection_not_selective_accuracy(self):
        r=self.runs(); cc=self.controls(r)
        for x in r: x['metrics']['known_correct_after_rejection']=0.
        self.assertTrue(any('postrejection' in v for v in assess(r,cc)['reasons']))
