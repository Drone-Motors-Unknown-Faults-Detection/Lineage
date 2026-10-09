"""清冊核對：不以副檔名、同目錄或 writer 存在冒充來源證明。"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.output_inventory_evidence import inspect


class OutputInventoryTests(unittest.TestCase):
    def test_writer_unknown_and_screenshot_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tests").mkdir()
            (root / "tests/example.py").write_text('def run():\n    target.write_text("results.json")\n', encoding="utf-8")
            for name in ("example/run/results.json", "example/run/manual.md", "integration_browser/run/image.png"):
                path = root / "output" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")
            with patch("tests.output_inventory_evidence.subprocess.check_output", side_effect=["", "fixture-head"]):
                result = inspect(root)
            by_name = {row["path"]: row for row in result["files"]}
            self.assertEqual(by_name["output/example/run/results.json"]["category"], "WRITER_MATCH_HISTORY_UNCONFIRMED")
            self.assertEqual(by_name["output/example/run/manual.md"]["category"], "UNKNOWN_HISTORY")
            self.assertEqual(by_name["output/integration_browser/run/image.png"]["category"], "DOCUMENTED_EXTERNAL_SCREENSHOT")
            self.assertTrue(all(row["action"] == "KEEP" for row in result["files"]))
            self.assertNotIn(str(root), json.dumps(result))

    def test_repeat_inventory_is_stable_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "output/history/run").mkdir(parents=True)
            path = root / "output/history/run/evidence.json"
            path.write_bytes(b"historical\r\n")
            with patch("tests.output_inventory_evidence.subprocess.check_output", side_effect=["", "head", "", "head"]):
                first, second = inspect(root), inspect(root)
            self.assertEqual(first, second)
            self.assertEqual(path.read_bytes(), b"historical\r\n")
