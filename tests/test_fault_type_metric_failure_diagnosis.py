import unittest
from copy import deepcopy
from experiments.fault_type_metric_failure_diagnosis import distribution,paired_equal,verify_run_binding


class MetricDiagnosisTests(unittest.TestCase):
    def rows(self):
        return [{'sample_id':'a','true_label':'x','source_sha256':'h','predicted_known_class':'x','openset_score':1.,'threshold':1.,'is_unknown':False}]

    def test_empty_and_tie(self):
        self.assertEqual(distribution([])['status'],'N/A')
        self.assertEqual(distribution(self.rows())['fixed_rejection_rate'],0.)

    def test_nonfinite_and_direction(self):
        r=self.rows();r[0]['openset_score']=float('nan')
        with self.assertRaises(ValueError):distribution(r)
        r=self.rows();r[0]['is_unknown']=True
        with self.assertRaises(ValueError):distribution(r)

    def test_exact_pair_and_mutation(self):
        self.assertEqual(paired_equal(self.rows(),self.rows()),1)
        r=self.rows();r[0]['threshold']=2
        with self.assertRaises(ValueError):paired_equal(self.rows(),r)

    def binding(self):
        common={'source_before':'sha','source_after':'sha','unique_samples':3,'failed_runs':[]}
        return (dict(common,runs=[{'run_id':'a','samples':3,'metrics':{'x':1}}]),
                dict(common,runs=[{'run_id':'a','rows':3,'reinference_exact':True,'truth_mutation_invariant':True}]))

    def test_distinct_schemas_are_bound(self):
        verify_run_binding(*self.binding())

    def test_tampered_coverage_and_sources(self):
        e,v=self.binding()
        for key,value in [('run_id','b'),('rows',2),('reinference_exact',False),('truth_mutation_invariant',False)]:
            bad=deepcopy(v);bad['runs'][0][key]=value
            with self.assertRaises(ValueError):verify_run_binding(e,bad)
        bad=deepcopy(v);bad['source_after']='mutated'
        with self.assertRaises(ValueError):verify_run_binding(e,bad)
        bad=deepcopy(v);bad['runs']*=2
        with self.assertRaises(ValueError):verify_run_binding(e,bad)


if __name__=='__main__':unittest.main()
