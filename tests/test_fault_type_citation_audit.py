"""引用候選擷取的工程測試，不驗證研究成績。"""
import json
import unittest

from experiments.fault_type_citation_audit import CitationMeta, canonical_source, eligible, extract_urls, notebook_lines, occurrences
from experiments.fault_type_citation_catalog import catalogue
from reports.issue_delivery_20261005.word_format import inline, visible


class CitationAuditTests(unittest.TestCase):
    def test_excludes_data_and_outputs(self):
        for path in ["data/raw.txt", "output/x/protocol.json", "venv/test.py"]:
            self.assertFalse(eligible(path))
        self.assertTrue(eligible("docs/README.md"))
        self.assertTrue(eligible("論文全文.md"))

    def test_no_notebook_outputs_or_execution(self):
        notebook = json.dumps({"cells": [
            {"cell_type": "markdown", "source": ["LMNN (2009)"]},
            {"cell_type": "code", "source": ["# RSC source\n", "raise RuntimeError()"],
             "outputs": [{"text": "UNTRUSTED citation (2020)"}]},
        ]})
        rows = list(notebook_lines(notebook))
        self.assertEqual(len(rows), 3)
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

    def test_notebook_source_urls_are_read_only_candidates(self):
        rows = occurrences(json.dumps({"cells": [
            {"cell_type": "code", "source": ["url='https://arxiv.org/pdf/2007.02454'"]},
        ]}), "history/a.ipynb")
        self.assertEqual(rows[0]['urls'], ['https://arxiv.org/pdf/2007.02454'])
        self.assertEqual(rows[0]['review_status'], 'UNREVIEWED')

    def test_standalone_source_url_and_bare_doi(self):
        self.assertEqual(occurrences('https://epub.uni-bayreuth.de/id/eprint/4600/', 'x.md')[0]['line'], 1)
        self.assertEqual(occurrences('DOI10.1299/kikaic.64.465：', 'x.md')[0]['bare_dois'], ['10.1299/kikaic.64.465'])
        row = occurrences('DOI [10.1016/S0047-259X(03)00096-4](https://doi.org/10.1/x)', 'x.md')
        self.assertEqual(row[0]['bare_dois'], [])
        row = occurrences('"citation":"DOI 10.1/x", "url":"https://jmlr.org/a"', 'x.json')
        self.assertEqual(row[0]['bare_dois'], [])

    def test_bare_doi_in_json_stops_before_other_fields(self):
        row = occurrences('"citation":"DOI 10.1007/s10994-007-5009-7.","url":"https://lmb/a"', 'x.json')
        self.assertEqual(row[0]['bare_dois'], ['10.1007/s10994-007-5009-7'])

    def test_unicode_and_html(self):
        rows = occurrences('參考文獻\n<a href="https://doi.org/10.1/x">作者</a>', "a.html")
        self.assertEqual(rows[1]["urls"], ["https://doi.org/10.1/x"])

    def test_doi_parentheses_and_markdown_wrapper(self):
        self.assertEqual(extract_urls('[LW](https://doi.org/10.1016/S0047-259X(03)00096-4)。'),
                         ['https://doi.org/10.1016/S0047-259X(03)00096-4'])

    def test_chinese_punctuation_does_not_become_url(self):
        self.assertEqual(extract_urls('https://jmlr.org/a.pdf；本地改編'), ['https://jmlr.org/a.pdf'])
        self.assertEqual(extract_urls('[來源](https://jmlr.org/a.pdf)及本站改編'), ['https://jmlr.org/a.pdf'])

    def test_explicit_versions_alias_but_distinct_dois(self):
        self.assertEqual(canonical_source('https://arxiv.org/pdf/1610.02136v3'), 'arxiv:1610.02136')
        self.assertEqual(canonical_source('https://proceedings.mlr.press/v139/krueger21a/krueger21a.pdf'), 'pmlr:v139/krueger21a')
        self.assertNotEqual(canonical_source('https://doi.org/10.1145/342009.335388'),
                            canonical_source('https://doi.org/10.1145/335191.335388'))

    def test_title_without_citation_metadata_is_not_paper_proof(self):
        parser = CitationMeta(); parser.feed('<title>Sign in</title><meta name="citation_title" content="Paper">')
        self.assertEqual(parser.values['citation_title'], ['Paper'])
        self.assertEqual(parser.title, ['Sign in'])

    def test_catalog_keeps_content_unverified_after_metadata(self):
        md = [{"source_id":"arxiv:1234.12345", "original_url":"https://arxiv.org/abs/1234.12345",
               "query_url":"https://arxiv.org/abs/1234.12345", "existence":"METADATA_VERIFIED",
               "metadata":{"citation_title":["Title"]}}]
        row = {"ref":"abc", "path":"x.md", "line":1, "text":"https://arxiv.org/pdf/1234.12345",
               "urls":["https://arxiv.org/pdf/1234.12345"], "bare_dois":[]}
        papers, rows, unknown = catalogue([row], md, [], {"aliases":{}, "reviewed_sections":{}, "supplementary":[]})
        self.assertEqual(papers[0]["content_status"], "UNVERIFIED")
        self.assertEqual(papers[0]["existence"], "METADATA_ONLY")
        self.assertEqual(rows[0]["paper_ids"], [papers[0]["id"]])
        self.assertEqual(unknown, [])

    def test_author_year_not_guessed_into_paper(self):
        row = {"ref":"abc", "path":"論文全文.md", "line":3, "text":"Wang (2008)",
               "urls":[], "bare_dois":[]}
        papers, rows, unknown = catalogue([row], [], [], {"aliases":{}, "reviewed_sections":{}, "supplementary":[]})
        self.assertEqual(rows[0]["classification"], "AMBIGUOUS_CANDIDATE")
        self.assertEqual(unknown[0]["text"], "Wang (2008)")

    def test_software_links_do_not_become_verified_papers(self):
        row = {"ref":"abc", "path":"x.md", "line":3, "text":"https://github.com/a/b",
               "urls":["https://github.com/a/b"], "bare_dois":[]}
        papers, rows, unknown = catalogue([row], [], [], {"aliases":{}, "reviewed_sections":{}, "supplementary":[]})
        self.assertEqual(rows[0]["classification"], "SOFTWARE_LINK")
        self.assertEqual(papers, [])

    def test_word_hyperlink_keeps_doi_parentheses(self):
        parts = inline("來源 [LW](https://doi.org/10.1016/S0047-259X(03)00096-4)。")
        self.assertIn(("LW", "https://doi.org/10.1016/S0047-259X(03)00096-4"), parts)
        self.assertEqual(visible("來源 [LW](https://doi.org/10.1016/S0047-259X(03)00096-4)。"),"來源 LW。")

    def test_word_plain_math_and_identifiers_not_removed(self):
        self.assertEqual(visible("**FAILED** x − μ 0.2404"),"FAILED x − μ 0.2404")

    def test_incomplete_markdown_link_not_silently_dropped(self):
        self.assertEqual(visible("[x](https://example.org"),"[x](https://example.org")


if __name__ == "__main__":
    unittest.main()
