"""固定main唯讀稽核入口的工程測試，不評估馬達模型。"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import fault_type_issue_triage as triage


class IssueTriageTests(unittest.TestCase):
    def test_selected_does_not_execute_other_top_level_statements(self):
        namespace = triage.selected("raise RuntimeError('不可執行')\ndef kept():\n    return 7\n",
                                    ["kept"], {})
        self.assertEqual(namespace["kept"](), 7)

    def test_missing_expected_function_rejected(self):
        with self.assertRaises(ValueError):
            triage.selected("def other():\n    return 1\n", ["missing"], {})

    def test_api_keeps_single_object(self):
        with patch.object(triage.subprocess, "run") as command:
            command.return_value.stdout = json.dumps([{"state": "closed"}])
            self.assertEqual(triage.api("fixture"), {"state": "closed"})
            self.assertNotIn("--method", command.call_args.args[0])

    def test_api_flattens_all_list_pages(self):
        with patch.object(triage.subprocess, "run") as command:
            command.return_value.stdout = json.dumps([[{"number": 1}], [{"number": 2}]])
            self.assertEqual([item["number"] for item in triage.api("fixture")], [1, 2])

    def test_fixed_main_counterexamples_and_write_stub(self):
        paths = ["experiments/exp6_matrix.py", "experiments/exp6_formal_benchmark.py",
                 "core/data.py", "experiments/aggregate_exp6.py", "core/formal_data.py"]
        sources = {path: triage.git("show", triage.MAIN + ":" + path).decode("utf-8") for path in paths}
        with tempfile.TemporaryDirectory(prefix="lineage-triage-test-") as temporary:
            root = Path(temporary) / "fixtures"
            result = triage.fixtures(sources, root)
            self.assertTrue(result["summary_without_csv_log_accepted"])
            self.assertTrue(result["same_size_mtime_different_bytes_fingerprint_equal"])
            self.assertEqual(result["arbitrary_schema_healthy_only_loaded"], ["8screws"])
            self.assertEqual(result["tampered_manifest_fingerprint_published"], "TAMPERED")
            self.assertEqual(result["stage2_arbitrary_config_accepted"], "..")
            self.assertEqual(result["stage2_unequal_widths_rows"], 2)
            self.assertEqual(result["models_fit"], 0)
            self.assertFalse(result["formal_data_read"])
            self.assertFalse(result["actual_outside_files_written"])
            self.assertEqual(len(result["stage2_stub_write_targets"]), 1)
            captured = Path(result["stage2_stub_write_targets"][0])
            self.assertTrue(captured.is_relative_to(root.resolve()))
            self.assertFalse(captured.exists())
