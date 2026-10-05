"""盤點 toy case；不載入正式模型或資料。"""
import json
import tempfile
import unittest
from pathlib import Path
from core.fault_type_final_guard import seal
from experiments.fault_type_research_closeout import inspect_index, decision, numeric_methods, check_summary, sha
from reports.research_closeout_20261005.build_report import pct, decimal, macro


class CloseoutTests(unittest.TestCase):
    def test_percent_and_missing_denominator_format(self):
        self.assertEqual(pct(.3125287386556079), '31.25')
        self.assertEqual(decimal(.26656112494836653), '0.2666')
        self.assertEqual(pct(None), 'NA')
        self.assertEqual(pct(0), '0.00')

    def test_old_unknown_alarm_is_not_total_healthy_alarm(self):
        values=macro({'equal_motor_descriptive': {'healthy_safety.false_positive_rate': {'mean': .02}}})
        self.assertNotIn('healthy_total_alarm', values)

    def test_sha_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.json'
            path.write_text('{}', encoding='utf-8')
            index = Path(folder) / 'index.json'
            index.write_text(json.dumps({'artifacts': [{'path': str(path), 'sha256': sha(path)}]}), encoding='utf-8')
            self.assertEqual(inspect_index(index)['checks'][0]['status'], 'VERIFIED')
            path.write_text('{"changed":1}', encoding='utf-8')
            with self.assertRaises(ValueError): inspect_index(index)

    def test_missing_not_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            index = Path(folder) / 'index.json'
            index.write_text(json.dumps({'artifacts': [{'path': str(Path(folder)/'missing.json'), 'sha256': '0'*64}]}), encoding='utf-8')
            self.assertEqual(inspect_index(index)['checks'][0]['status'], 'INCOMPLETE')

    def test_all_seeds_preserved(self):
        methods = {'M01': {'seeds': [{'seed': 0}, {'seed': 1}, {'seed': 2}]}}
        self.assertEqual(numeric_methods({'methods': methods}), methods)

    def test_duplicate_method_rejected(self):
        with self.assertRaises(ValueError):
            numeric_methods({'methods': [{'arm_id': 'X', 'score_id': 'M'}, {'arm_id': 'X', 'score_id': 'M'}]})

    def test_detector_pair_is_not_duplicate_classifier(self):
        methods = numeric_methods({'methods': [{'arm_id': 'X', 'score_id': 'M'}, {'arm_id': 'X', 'score_id': 'K'}]})
        self.assertEqual(len(methods), 2)

    def test_failed_routes_to_b_not_new_method(self):
        d = decision({'reliability': {'M01': {'main_screen': 'FAILED'}}, 'completed_runs': 216, 'paired_differences': [1]*1134})
        self.assertEqual(d['path'], 'B')
        self.assertFalse(d['reliable_improvement_reached'])
        self.assertIn('未實作', d['group_dro'])

    def test_incomplete_does_not_pass(self):
        d = decision({'reliability': {'M01': {'main_screen': 'INCOMPLETE'}}, 'completed_runs': 1, 'paired_differences': []})
        self.assertEqual(d['path'], 'B')

    def test_a_is_only_candidate_not_reliable(self):
        d = decision({'reliability': {'M01': {'main_screen': 'PASS'}}, 'completed_runs': 9, 'paired_differences': []})
        self.assertEqual(d['path'], 'A')
        self.assertFalse(d['reliable_improvement_reached'])

    def test_semantic_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'summary.json'
            data = seal({'methods': {}}, 'report_checksum')
            path.write_text(json.dumps(data), encoding='utf-8')
            check_summary(path)
            data['methods'] = {'bad': 1}
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(ValueError): check_summary(path)
