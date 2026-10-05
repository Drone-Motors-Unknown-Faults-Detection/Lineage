"""引用候選擷取的工程測試，不驗證研究成績。"""
import json
import unittest

from experiments.fault_type_citation_audit import eligible, extract_urls, notebook_lines, occurrences


class CitationAuditTests(unittest.TestCase):
    def test_excludes_data_and_outputs(self):
        for path in ["data/raw.txt", "output/x/protocol.json", "venv/test.py"]:
            self.assertFalse(eligible(path))
        self.assertTrue(eligible("docs/README.md"))

    def test_no_notebook_outputs_or_execution(self):
        notebook = json.dumps({"cells": [
            {"cell_type": "markdown", "source": ["LMNN (2009)"]},
            {"cell_type": "code", "source": ["# RSC source\n", "raise RuntimeError()"],
             "outputs": [{"text": "UNTRUSTED citation (2020)"}]},
        ]})
        rows = list(notebook_lines(notebook))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["cell"], 1)
        self.assertNotIn("UNTRUSTED", str(rows))

    def test_keeps_line_and_url_not_support_claim(self):
        rows = occurrences("第一行\nLMNN https://jmlr.org/paper.pdf", "docs/x.md")
        self.assertEqual(rows[0]["line"], 2)
        self.assertEqual(rows[0]["urls"], ["https://jmlr.org/paper.pdf"])
        self.assertEqual(rows[0]["review_status"], "UNREVIEWED")

    def test_unsupported_binary_not_eligible(self):
        self.assertFalse(eligible("models/a.joblib"))
        self.assertFalse(eligible("paper.pdf"))

    def test_code_comments_only_for_notebook(self):
        rows = occurrences(json.dumps({"cells": [
            {"cell_type": "code", "source": ["url='https://arxiv.org/pdf/2007.02454'"]},
        ]}), "history/a.ipynb")
        self.assertEqual(rows, [])

    def test_unicode_and_html(self):
        rows = occurrences('參考文獻\n<a href="https://doi.org/10.1/x">作者</a>', "a.html")
        self.assertEqual(rows[1]["urls"], ["https://doi.org/10.1/x"])

    def test_doi_parentheses_and_markdown_wrapper(self):
        self.assertEqual(extract_urls('[LW](https://doi.org/10.1016/S0047-259X(03)00096-4)。'),
                         ['https://doi.org/10.1016/S0047-259X(03)00096-4'])

    def test_chinese_punctuation_does_not_become_url(self):
        self.assertEqual(extract_urls('https://jmlr.org/a.pdf；本地改編'), ['https://jmlr.org/a.pdf'])


if __name__ == "__main__":
    unittest.main()
