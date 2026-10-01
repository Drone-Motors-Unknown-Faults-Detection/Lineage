import unittest
from experiments.fault_type_accuracy_summary import pareto, AXES, run_entry, save_summary


class SummaryTests(unittest.TestCase):
    def point(self,name,values):
        return {'arm_id':name,'score_id':'test','equal_motor_descriptive':{k:{'mean':v} for k,v in zip(AXES,values)}}

    def test_descriptive_tradeoff_no_selected_winner(self):
        result=pareto([self.point('A',[.3,.2,.0]),self.point('B',[.3,.4,.0]),self.point('C',[.4,.2,.1])])
        relations={r['method_id']:r for r in result['relations']}
        self.assertEqual(relations['A/test']['dominated_by'],['B/test'])
        self.assertTrue(relations['B/test']['non_dominated']);self.assertTrue(relations['C/test']['non_dominated'])
        self.assertNotIn('global_winner',result)

    def test_missing_metric_is_not_fabricated(self):
        result=pareto([self.point('A',[None,.2,.0]),self.point('B',[.3,.4,.0])])
        self.assertEqual([r['method_id'] for r in result['relations']],['B/test'])
        self.assertIsNone(result['points']['A/test'][0])

    def test_historical_baseline_count_and_tampered_new_count(self):
        r={'arm_id':'A0','score_id':'knn','fold_id':'f','seed':0,'test_ids_checksum':'sha','prediction_artifact':{'rows':7}}
        self.assertEqual(run_entry(r)['samples'],7)
        with self.assertRaises(ValueError):run_entry(dict(r,samples=8))

    def test_lossless_compact_summary_roundtrip(self):
        import tempfile, gzip, json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);result={'metrics':[.123456789,None],'selection_policy':'none'}
            save_summary(p,result)
            self.assertEqual(json.loads(gzip.decompress((p/'summary.json.gz').read_bytes())),result)
            self.assertEqual(json.loads((p/'summary.json').read_text(encoding='utf-8')),result)
