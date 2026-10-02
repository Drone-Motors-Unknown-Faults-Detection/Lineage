import unittest
from core.fault_type_metrics_v2 import metrics_v2
from experiments.fault_type_mechanism_report import summarize


class MechanismReportTest(unittest.TestCase):
    def sample(self):
        p={'known_labels':['8screws','2screws'],'unknown_labels':['U'],'seeds':[0,1,2]}
        rows=[{'sample_id':str(i),'true_label':truth,'predicted_known_class':pred,'openset_score':score,'threshold':1.,'is_unknown':score>1} for i,(truth,pred,score) in enumerate([('8screws','2screws',0.),('2screws','2screws',0.),('U','8screws',2.)])]
        m=metrics_v2(rows,p['known_labels'],p['unknown_labels'])
        rr=[{'seed':s,'samples':3,'motor_roles':{'test':t},'metrics':m,'rpm_metrics':[{'rpm':rpm,'metrics':m} for rpm in ['a','b','c']],
            'configuration_metrics':[{'label':'2screws','classifier_recall':1.}]} for s in p['seeds'] for t in ['T1','T2','T3']]
        return p,rows,rr

    def test_complete_health_gate_not_unknown_only(self):
        p,rows,rr=self.sample();s=summarize(rr,rows,p)
        self.assertEqual(s['motor_macro_seed0']['healthy_unknown_alarm'],0)
        self.assertEqual(s['worst_rpm_healthy_total_alarm'],1)
        self.assertFalse(s['all_nine_health_groups_within_research_limit'])

    def test_seed_duplicates_not_new_data(self):
        p,rows,rr=self.sample();s=summarize(rr,rows,p)
        self.assertEqual(s['sample_weighted_seed0']['unknown_recall'],1)
        self.assertEqual(s['seed_descriptive_range']['unknown_recall'],{'min':1.,'max':1.})
        self.assertEqual(s['worst_motor_fault_class_recall'],1)

    def test_no_cross_model_auc_ranking(self):
        p,rows,rr=self.sample();rr[0]=dict(rr[0],metrics=dict(rr[0]['metrics'],unknown_rejection=dict(rr[0]['metrics']['unknown_rejection'],auroc_unknown_positive=.4)))
        s=summarize(rr,rows,p)
        self.assertAlmostEqual(s['sample_weighted_seed0']['unknown_auroc'],.8)

    def test_missing_runtime_not_zero(self):
        p,rows,rr=self.sample();s=summarize(rr,rows,p)
        self.assertIsNone(s['runtime']['process_peak_memory_bytes'])
        self.assertIsNone(s['runtime']['shared_bundle_inference_seconds'])
