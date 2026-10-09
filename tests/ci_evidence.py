"""CI 工程證據：真實執行指定命令，只公開白名單摘要。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from core.logger import setup_run
from core.runtime_environment import collect_environment
from tests.issue_delivery_evidence import local_links

ROOT = Path(__file__).resolve().parents[1]
CLIS = ("experiments.exp1_cold_start", "experiments.exp2_scale_growth",
        "experiments.exp3_trend", "experiments.exp4_polar_map",
        "experiments.compare_openset", "experiments.exp6_formal_benchmark", "web.server")
DOCUMENTS = ("TODO.md", "docs/README.md", "docs/health_and_reports.md",
             "docs/runtime_policy.md", "docs/ci_contract.md",
             "docs/project_closeout_20261009/README.md",
             "docs/project_closeout_20261009/execution_log.md",
             "docs/project_closeout_20261009/runtime_delivery.md")


def execute(arguments: list[str], timeout: int = 600) -> dict:
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", MPLBACKEND="Agg")
    try:
        result = subprocess.run([sys.executable, *arguments], cwd=ROOT, env=env,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout)
        output = result.stdout + "\n" + result.stderr
        # 任意 exception payload、絕對路徑與 token 都不進公開 artifact。
        count = re.search(r"Ran (\d+) tests? in", output)
        failures = re.search(r"FAILED \(([^\r\n]+)\)", output)
        totals = {key: int(value) for key, value in
                  re.findall(r"(failures|errors|skipped)=(\d+)", failures.group(1) if failures else output[-1000:])}
        return {"arguments": arguments, "returncode": result.returncode,
                "tests_run": int(count.group(1)) if count else None,
                "failed": totals.get("failures", 0), "errors": totals.get("errors", 0),
                "skipped": totals.get("skipped", 0),
                "failure_ids": re.findall(r"^(?:FAIL|ERROR): ([\w]+) \(([\w.]+)\)", output, re.MULTILINE),
                "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
                "diagnostic_policy": "原始輸出只留行程記憶體；公開摘要不收錄任意例外文字"}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"arguments": arguments, "returncode": -1, "error_type": type(exc).__name__}


def run() -> dict:
    logger, paths = setup_run("ci_evidence")
    environment = collect_environment(ROOT)
    checks = []
    # 即使正式 data 在開發機存在，本入口與 tests 也不將它當測試輸入。
    with tempfile.TemporaryDirectory(prefix="lineage_ci_") as directory:
        previous_tmp = {name: os.environ.get(name) for name in ("TMP", "TEMP", "TMPDIR")}
        try:
            for name in previous_tmp:
                os.environ[name] = directory
            checks.append(execute(["-m", "pip", "check"]))
            checks.append(execute(["-m", "unittest", "discover", "-s", "tests", "-t", "."]))
            checks.extend(execute(["-m", module, "--help"], 60) for module in CLIS)
        finally:
            for name, old in previous_tmp.items():
                if old is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = old
    links = [row for name in DOCUMENTS for row in local_links(ROOT / name, ROOT)]
    broken = [{"source": row["source"], "link": row["link"]} for row in links if not row["exists"]]
    result = {"schema_version": "ci_evidence_v1", "environment": environment,
              "checks": checks, "document_count": len(DOCUMENTS), "relative_targets": len(links),
              "broken_targets": broken, "ignored_data_required": False,
              "status": "PASS" if not broken and all(row["returncode"] == 0 for row in checks) else "FAILED",
              "scope": "工程契約；任意Origin現狀不代表安全，無新模型成績，macOS未驗證"}
    (paths.output_dir / "public_summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    suite = checks[1]
    logger.info("CI 工程驗證：{}；測試數={}；failed={}；errors={}；skipped={}；失效目標={}",
                result["status"], suite.get("tests_run"), suite.get("failed"), suite.get("errors"), suite.get("skipped"), len(broken))
    for check in checks:
        if check["returncode"]:
            logger.error("失敗命令={}；測試ID={}", check["arguments"], check.get("failure_ids", []))
    return result


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    return 0 if run()["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
