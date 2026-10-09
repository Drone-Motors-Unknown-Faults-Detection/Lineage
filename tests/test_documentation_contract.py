"""操作文件的本機目標與版本界線；不以文字測試代替模型驗證。"""
from pathlib import Path
import unittest
import json
import subprocess

from tests.issue_delivery_evidence import local_links


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ("docs/README.md", "docs/ci_contract.md", "docs/runtime_policy.md",
             "docs/formal_materialization_contract.md", "docs/health_and_reports.md",
             "docs/navigation/exp24_README.md")


class DocumentationContractTests(unittest.TestCase):
    def test_report_attachments_and_readers_resolve(self):
        from tests.ci_evidence import DOCUMENTS as ci_documents
        reports = [*ROOT.glob("reports/Andy_20261008_*/*.md"),
                   *ROOT.glob("reports/Andy_20261009_*/*.md")]
        self.assertTrue(reports)
        for path in reports:
            self.assertFalse([row for row in local_links(path, ROOT) if not row["exists"]], path)
        self.assertTrue(all((ROOT / name).is_file() for name in ci_documents))

    def test_backup_manifest_preserves_bytes_and_paths(self):
        path = "reports/Andy_20261009_主線交付/backup_manifest.json"
        original = subprocess.check_output(
            ["git", "show", "42ee1b7abee92f85088b6150d64e113931104203:docs/project_closeout_20261009/backup_manifest.json"],
            cwd=ROOT)
        current = (ROOT / path).read_bytes()
        self.assertEqual(current.replace(b"\r\n", b"\n"), original.replace(b"\r\n", b"\n"))
        record = json.loads(current)
        self.assertEqual(record["verified_archive"]["status"], "VERIFIED")
        self.assertEqual(record["preserved_failed_archive"]["status"], "FAILED_PARTIAL")

    def test_local_targets_exist(self):
        for name in DOCUMENTS:
            with self.subTest(document=name):
                rows = local_links(ROOT / name, ROOT)
                self.assertFalse([row for row in rows if not row["exists"]])

    def test_operations_and_history_have_separate_contracts(self):
        for name in DOCUMENTS[1:5]:
            with self.subTest(document=name):
                content = (ROOT / name).read_text(encoding="utf-8")
                self.assertRegex(content, r"/blob/[0-9a-f]{40}/")
        runtime = (ROOT / "docs/runtime_policy.md").read_text(encoding="utf-8")
        self.assertIn("uv sync", runtime)
        self.assertIn("uv.lock", runtime)
        self.assertIn("-m pytest tests", runtime)
        ci = (ROOT / "docs/ci_contract.md").read_text(encoding="utf-8")
        self.assertIn("./run_ruff.sh", ci)
        self.assertIn("./run_pytest.sh", ci)
        self.assertIn("不在其中重跑 pytest／ruff", ci)
        self.assertIn("只有 Ubuntu", ci)
