"""從唯讀盤點建立引用清冊；未閱讀的內容不自動通過。"""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from core.logger import setup_run
from experiments.fault_type_citation_audit import canonical_source

ROOT = Path(__file__).resolve().parents[1]
SOFTWARE = {"github.com", "scikit-learn.org", "contrib.scikit-learn.org", "json-schema.org", "localhost", "127.0.0.1"}

def load(path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f: return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))

def dump(path, value):
    if path.suffix == ".gz":
        with gzip.open(path, "wt", encoding="utf-8") as f: json.dump(value, f, ensure_ascii=False)
    else: path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def catalogue(candidates, metadata, legacy, annotations):
    papers, aliases = {}, {}
    def add(row):
        row = dict(row)
        row.setdefault("content_status", "UNVERIFIED")
        row.setdefault("reading_scope", "本輪尚未核對全文；歷史聲明另存")
        row.setdefault("existence", "AMBIGUOUS" if not row.get("url") else "UNVERIFIED")
        row.update(full_text_cache=None, cache_sha256=None, occurrences=[],
                   acquisition_date="2026-10-06", interpretation="有來源不等於支持本地成績")
        papers[row["id"]] = row
        for url in [row.get("url"), *row.get("aliases", [])]:
            if url: aliases[canonical_source(url)] = row["id"]
    for old in legacy:
        identifier = old["id"]
        urls = annotations["aliases"].get(identifier, [])[:]
        urls += ["https://doi.org/"+m for m in re.findall(r"DOI\s+(10\.[^\s]+)", old["citation"])]
        add(dict(id=identifier, citation=old["citation"], title=None, authors=None, year=None, venue=None,
                 url=old["url"], aliases=urls, use=old["use"], prior_reading_claim=old["depth"],
                 reading_scope=annotations["reviewed_sections"].get(identifier, "本輪未精讀；見 prior_reading_claim"),
                 content_status="PARTIAL" if identifier in annotations["reviewed_sections"] else "UNVERIFIED"))
    for extra in annotations["supplementary"]:
        add(extra)
        if extra.get("url"): papers[extra["id"]]["existence"] = "METADATA_ONLY"
    for number, item in enumerate(sorted(metadata, key=lambda x:x["source_id"]), 1):
        identifier = aliases.get(item["source_id"])
        md = item.get("metadata", {})
        metadata_doi = md.get("DOI", md.get("citation_doi", []))
        metadata_doi = metadata_doi[0] if isinstance(metadata_doi, list) and metadata_doi else metadata_doi
        if not identifier and isinstance(metadata_doi, str):
            identifier = aliases.get(canonical_source("https://doi.org/"+metadata_doi))
        if not identifier:
            identifier = f"P{number:03d}"
            add(dict(id=identifier, url=item["original_url"], title=None, authors=None, year=None, venue=None,
                     use="候選來源；是否為論文及本地取用待核對"))
        paper = papers[identifier]
        aliases[item["source_id"]] = identifier
        paper.setdefault("metadata_evidence", []).append(item)
        title = md.get("citation_title", md.get("title"))
        if title: paper["title"] = title[0] if isinstance(title, list) else title
        authors = md.get("citation_author", md.get("author"))
        if authors: paper["authors"] = authors
        paper["venue"] = md.get("container-title", md.get("citation_journal_title", paper.get("venue")))
        paper["doi"] = md.get("DOI", md.get("citation_doi", paper.get("doi")))
        dates = md.get("published", {}).get("date-parts", []) if isinstance(md.get("published"), dict) else []
        if dates: paper["year"] = dates[0][0]
        elif md.get("citation_date"): paper["repository_deposit_date"] = md["citation_date"]
        paper["version"] = item["original_url"]
        paper["official_metadata_url"] = item["query_url"]
        if item["existence"] == "METADATA_VERIFIED": paper["existence"] = "METADATA_ONLY"
        elif item["existence"] == "PRIMARY_PDF_RETRIEVED": paper["existence"] = "VERIFIED"
    rows, unresolved = [], []
    for i, original in enumerate(candidates, 1):
        row = dict(original, occurrence_id=f"O{i:05d}")
        keys = [canonical_source(url) for url in row["urls"]]
        keys += [canonical_source("https://doi.org/"+doi) for doi in row["bare_dois"]]
        ids = sorted({aliases[k] for k in keys if k in aliases})
        row.update(paper_ids=ids, claim_status="UNVERIFIED",
                   classification="SOURCE_LINK" if ids else "SOFTWARE_LINK" if keys and all(
                       urlparse(url).hostname in SOFTWARE for url in row["urls"]) else "AMBIGUOUS_CANDIDATE")
        for identifier in ids: papers[identifier]["occurrences"].append(row["occurrence_id"])
        if row["classification"] == "AMBIGUOUS_CANDIDATE":
            unresolved.append({k:row[k] for k in ["occurrence_id", "ref", "path", "line", "text"]})
        rows.append(row)
    for row in rows:
        if not set(row["paper_ids"]) <= papers.keys(): raise ValueError("出現孤兒 paper ID")
    return list(papers.values()), rows, unresolved

def run(pools=None, *, scan, annotations):
    logger, paths = setup_run("fault_type_citation_catalog")
    annotations = load(annotations)
    papers, rows, unresolved = catalogue(load(scan/"citation_candidates.json.gz"),
        load(scan/"metadata_inventory.json"), load(ROOT/"reports/research_closeout_20261005/references.json"), annotations)
    target = paths.output_dir
    dump(target/"paper_catalog.json", papers)
    dump(target/"citation_occurrences.json.gz", rows)
    dump(target/"unresolved.json.gz", unresolved)
    dump(target/"search_log.json", {"queries": load(scan/"metadata_inventory.json"),
         "manual_source_checks": annotations["supplementary"], "important_unresolved": annotations["important_unresolved"],
         "scope":"125 個原保存 HTTP 查詢加本輪原網站章節核對；不把 HTTP 成功當全文閱讀"})
    counts = dict(Counter(p["existence"] for p in papers))
    result = dict(scan=str(scan), papers=len(papers), occurrences=len(rows), ambiguous_occurrences=len(unresolved),
                  existence_counts=counts, orphan_ids=0, all_content_reviewed=False,
                  issue19_status="OPEN", trained_models=0, new_predictions=0)
    dump(target/"consistency.json", result)
    heading = "# 固定範圍文獻清冊\n\n存在與內容分開。B01–B40保留歷史來源，S為人工核對補充，P為自動候選；P不代表獨立論文數。全部未核內容仍UNVERIFIED，#19保持OPEN。\n\n"
    table = ["| ID | 題名／原引用 | 存在 | 內容 | 閱讀與適配 |", "|---|---|---|---|---|"]
    for p in papers:
        name = p.get("title") or p.get("citation") or "題名未能辨識"
        label = name.replace("|", "／").replace("\n"," ")
        if p.get("url"): label = f"[{label}]({p['url']})"
        table.append(f"| {p['id']} | {label} | {p['existence']} | {p['content_status']} | {p['reading_scope']}；{p['use']} |")
    (target/"catalog.md").write_text(heading+"\n".join(table)+"\n", encoding="utf-8")
    logger.info("清冊完成，仍有未核內容：{}", result)
    return result

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scan", type=Path, required=True)
    p.add_argument("--annotations", type=Path, required=True)
    print(json.dumps(run(**vars(p.parse_args(argv))), ensure_ascii=False))

if __name__ == "__main__": main()
