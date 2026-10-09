"""操作文件的本機目標與版本界線；不以文字測試代替模型驗證。"""
from pathlib import Path
import unittest

from tests.issue_delivery_evidence import local_links


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ("docs/README.md", "docs/ci_contract.md", "docs/runtime_policy.md",
             "docs/formal_materialization_contract.md", "docs/health_and_reports.md",
             "docs/navigation/exp24_README.md")


class DocumentationContractTests(unittest.TestCase):
    def test_local_targets_exist(self):
        for name in DOCUMENTS:
            with self.subTest(document=name):
                rows = local_links(ROOT / name, ROOT)
                self.assertFalse([row for row in rows if not row["exists"]])

    def test_historical_reports_use_fixed_revision(self):
        for name in DOCUMENTS[1:5]:
            with self.subTest(document=name):
                content = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn("/blob/791216cf5602c370091fa516264f1ce6aaad6ab1/", content)
        runtime = (ROOT / "docs/runtime_policy.md").read_text(encoding="utf-8")
        self.assertIn("-m pip install -c runtime-constraints.txt pytest", runtime)
        self.assertIn("-m pytest tests", runtime)
        ci = (ROOT / "docs/ci_contract.md").read_text(encoding="utf-8")
        self.assertIn("checks[].skipped", ci)
        self.assertIn("只有 Ubuntu", ci)
