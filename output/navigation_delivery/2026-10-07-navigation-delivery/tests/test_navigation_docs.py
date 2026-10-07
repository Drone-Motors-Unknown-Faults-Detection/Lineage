"""導覽文件的結構驗收。"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NavigationDocsTests(unittest.TestCase):
    def test_overview_seven_questions(self):
        text = (ROOT / "docs/navigation/實驗總覽.md").read_text(encoding="utf-8")
        rows = [line for line in text.splitlines() if line.startswith("|")]
        self.assertGreaterEqual(len(rows), 20)
        self.assertTrue(all(len(row.strip("|").split("|")) == 8 for row in rows))
        for word in ("冷啟動", "LW", "PolarMap", "跨馬達", "到達樣本", "FAILED", "UNKNOWN"):
            self.assertIn(word, text)

    def test_explanations_separate_evidence(self):
        text = (ROOT / "docs/navigation/結果白話解讀.md").read_text(encoding="utf-8")
        for word in ("4.52", "0%", "解釋", "推論", "限制"):
            self.assertIn(word, text)
