"""固定版本的唯讀引用盤點；不擬合模型、不讀取正式特徵值。"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from core.logger import setup_run

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".html", ".py", ".json", ".txt", ".bib", ".ipynb"}
EXCLUDED = {"output", "logs", "data", "venv", ".venv310", ".git", ".codex", ".aws"}
PATTERN = re.compile(
    r"doi\.org|arxiv\.org|jmlr|proceedings\.mlr|papers\.nips|neurips|"
    r"references|citation|bibliography|參考文獻|引用文獻|"
    r"(?:[A-Z][a-z]+[^\n]{0,50}(?:19[0-9]{2}|20[0-9]{2}))|"
    r"(?:LMNN|RSC|REx|HDBSCAN|EWMA|CUSUM|t-SNE|Conformal)",
    re.IGNORECASE,
)
URL = re.compile(r"https?://[^\s<>\]\"'`。；，]+")


def extract_urls(text):
    """保留 DOI 內的括號，只移除 Markdown 外層括號及句末標點。"""
    result = []
    for value in URL.findall(text):
        value = value.rstrip(",;.")
        while value.endswith(")") and value.count(")") > value.count("("):
            value = value[:-1]
        result.append(value)
    return result


def git(*args, input=None, cwd=ROOT):
    result = subprocess.run(["git", *args], cwd=cwd, input=input, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def notebook_lines(text):
    """只讀 Markdown 與 code 註解；不執行、不納入保存的 cell outputs。"""
    document = json.loads(text)
    for cell_index, cell in enumerate(document.get("cells", [])):
        source = cell.get("source", [])
        source = source if isinstance(source, str) else "".join(source)
        for line_number, line in enumerate(source.splitlines(), 1):
            if cell.get("cell_type") == "markdown" or line.lstrip().startswith("#"):
                yield {"cell": cell_index, "line": line_number, "text": line}


def occurrences(text, path):
    lines = notebook_lines(text) if path.endswith(".ipynb") else (
        {"line": number, "text": line} for number, line in enumerate(text.splitlines(), 1)
    )
    return [{**line, "urls": extract_urls(line["text"]), "review_status": "UNREVIEWED"}
            for line in lines if PATTERN.search(line["text"])]


def eligible(path):
    return not (set(Path(path).parts) & EXCLUDED) and Path(path).suffix.lower() in TEXT_SUFFIXES


def scan_ref(ref, repository_url, *, preload=False):
    """讀 Git blobs；缺物件時只向宣告 repo 取物件，不切換或合併工作樹。"""
    tree = git("ls-tree", "-r", "-l", ref).decode("utf-8").splitlines()
    files, skipped = [], []
    for line in tree:
        metadata, path = line.split("\t", 1)
        mode, kind, oid, size = metadata.split()
        if not eligible(path):
            continue
        if kind != "blob" or int(size) > 50 * 1024 * 1024:
            skipped.append({"path": path, "reason": "非 blob 或大於 50 MiB，待專用抽取"})
            continue
        files.append({"path": path, "git_blob": oid, "bytes": int(size)})
    if preload and files:
        env = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}
        check = subprocess.run(["git", "cat-file", "--batch-check"],
                               cwd=ROOT, env=env, capture_output=True,
                               input=("\n".join(x["git_blob"] for x in files)+"\n").encode())
        missing = [line.split()[0] for line in check.stdout.decode().splitlines()
                   if line.endswith(" missing")]
        for offset in range(0, len(missing), 100):
            git("fetch", "--no-tags", "--filter=blob:none", repository_url,
                *missing[offset:offset+100])
    request = ("\n".join(x["git_blob"] for x in files)+"\n").encode()
    payload = git("cat-file", "--batch", input=request)
    cursor, found = 0, []
    for file in files:
        end = payload.index(b"\n", cursor)
        header = payload[cursor:end].decode()
        if header.endswith(" missing"):
            file["status"] = "MISSING_BLOB"; cursor=end+1; continue
        oid, kind, size = header.split()
        cursor=end+1; blob=payload[cursor:cursor+int(size)]; cursor+=int(size)+1
        file["sha256"] = hashlib.sha256(blob).hexdigest()
        try:
            text = blob.decode("utf-8-sig")
            matches = occurrences(text, file["path"])
            found.extend({**match, "ref": ref, "repository": repository_url,
                          "path": file["path"], "file_sha256": file["sha256"]}
                         for match in matches)
            file["status"] = "SCANNED"
        except (UnicodeError, ValueError) as error:
            file["status"] = "UNPARSED"; file["error"] = str(error)
    return {"ref": ref, "repository": repository_url, "files": files,
            "excluded_rule": sorted(EXCLUDED), "skipped": skipped,
            "claim": "固定版本候選匹配；未宣稱全部 Git 歷史或逐篇全文閱讀"}, found


def github_snapshot(repo):
    """取得分頁 issue／PR 與全部留言，僅 GET。"""
    def api(endpoint):
        result = subprocess.run(["gh", "api", "--paginate", "--slurp", endpoint],
                                cwd=ROOT, capture_output=True, check=True, encoding="utf-8")
        return json.loads(result.stdout)
    issue_pages = api(f"repos/{repo}/issues?state=open&per_page=100")
    issues = [item for page in issue_pages for item in page if "pull_request" not in item]
    for issue in issues:
        issue["all_comments"] = [x for page in api(issue["comments_url"]) for x in page]
    prs = [item for page in api(f"repos/{repo}/pulls?state=open&per_page=100") for item in page]
    for pr in prs:
        pr["all_comments"] = [x for page in api(pr["comments_url"]) for x in page]
        pr["changed_files"] = [x["filename"] for page in api(pr["url"]+"/files") for x in page]
    return {"issues": issues, "issue_count_excluding_pr": len(issues),
            "issue_pages": len(issue_pages), "open_prs": prs, "mode": "GET_ONLY"}


def verify_existing():
    """核對既有封存；沒有模型 fit 或 prediction 呼叫。"""
    from core.fault_type_final_guard import verify_seal
    from core.fault_type_sample_split import load_formal_catalog
    def read(path):
        path = Path(path)
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                return json.load(stream)
        return json.loads(path.read_text(encoding="utf-8"))
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    records, formal = load_formal_catalog(ROOT/"data/formal_local")
    expected = "c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d"
    if formal["dataset_fingerprint"] != expected:
        raise ValueError("正式資料指紋與基線不同")
    index = read(ROOT/"reports/metric_classification_v1/result_index.json")
    artifacts, objects = {}, {}
    for name, key in [("protocol", "protocol_checksum"), ("evaluation", "evaluation_checksum"),
                      ("verification", "verification_checksum"), ("summary", "report_checksum")]:
        path = ROOT/index[name]; value = read(path); verify_seal(value, key)
        artifacts[name] = {"path": str(path), "sha256": sha(path), "semantic_checksum": value[key], "seal": "VERIFIED"}
        objects[name] = value
    protocol = objects["protocol"]
    for value in protocol["weight_artifacts"] + [protocol["solver_diagnosis"], protocol["solver_protocol"]]:
        if sha(value["path"]) != value["sha256"]:
            raise ValueError("hard600 來源 SHA 不符："+value["path"])
    for name in ("evaluation", "verification", "summary"):
        if objects[name]["protocol_checksum"] != protocol["protocol_checksum"]:
            raise ValueError("封存 protocol binding 不符")
    matrices = []
    for stamp in ["2026-09-30-19-05-42", "2026-09-30-19-37-27", "2026-09-30-19-37-39"]:
        path = ROOT/"output/fault_type_matrix"/stamp/"matrix_index.json"
        value = read(path)
        matrices.append({"path": str(path), "sha256": sha(path), **value})
    return {"formal": formal, "motor_sample_counts": {t: sum(r["t_code"] == t for r in records) for t in ["T1", "T2", "T3"]},
            "exp13_artifacts": artifacts, "hard600_weight_sha_verified": len(protocol["weight_artifacts"]),
            "exp13_completed": objects["verification"]["completed_runs"],
            "exp13_failed": objects["verification"]["failed_runs"],
            "exp13_summary": objects["summary"], "exp13_protocol": protocol,
            "historical_matrices": matrices, "historical_total_completed": sum(m["completed"] for m in matrices),
            "trained_models": 0, "new_predictions": 0, "raw_independence": "UNKNOWN", "fresh_final_test": "INCOMPLETE"}


def run(pools=None, *, refs, preload=False, snapshot=False, verify=False):
    logger, paths = setup_run("fault_type_citation_audit")
    scopes, found = [], []
    for spec in refs:
        logger.info("掃描固定版本 {}", spec["ref"])
        scope, matches = scan_ref(spec["ref"], spec["repository"], preload=preload)
        scopes.append(scope); found.extend(matches)
    target = paths.output_dir
    (target/"citation_scope.json").write_text(json.dumps(scopes, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    # 候選原句屬 immutable 來源摘錄，只保留短定位。新內容筆記另用繁體中文。
    with gzip.open(target/"citation_candidates.json.gz", "wt", encoding="utf-8") as stream:
        json.dump(found, stream, ensure_ascii=False)
    urls = sorted({url.rstrip("。，；,;") for row in found for url in row["urls"]})
    (target/"candidate_urls.json").write_text(json.dumps(urls, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    if snapshot:
        (target/"github_snapshot.json").write_text(json.dumps(
            github_snapshot("Drone-Motors-Unknown-Faults-Detection/Lineage"),
            ensure_ascii=False, indent=2), encoding="utf-8")
    if verify:
        with gzip.open(target/"existing_evidence_verified.json.gz", "wt", encoding="utf-8") as stream:
            json.dump(verify_existing(), stream, ensure_ascii=False)
    result = {"output": str(target), "scope_count": len(scopes), "candidates": len(found),
              "urls": len(urls), "full_content_review": False, "trained_models": 0}
    (target/"summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    logger.info("完成候選盤點，內容判定仍需人工核對：{}", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refs", type=Path, required=True)
    parser.add_argument("--preload", action="store_true")
    parser.add_argument("--github-snapshot", action="store_true")
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    result = run(refs=json.loads(args.refs.read_text(encoding="utf-8")),
                 preload=args.preload, snapshot=args.github_snapshot, verify=args.verify_existing)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
