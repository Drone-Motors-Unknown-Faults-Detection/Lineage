"""實驗手冊的連結、CLI及Web入口回歸；不讀正式data、不執行研究。"""
from __future__ import annotations

import ast
from functools import lru_cache
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from tests.issue_delivery_evidence import local_links
from web.experiments import CATALOG

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/experiments"


def anchors(text: str) -> set[str]:
    """核對本輪使用的GitHub標題錨點；忽略程式碼區塊。"""
    found, counts, fenced = set(), {}, False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if fenced:
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        title = re.sub(r"[^\w\- ]", "", match[1].replace("`", "").lower()).replace(" ", "-")
        count = counts.get(title, 0)
        counts[title] = count + 1
        found.add(title + (f"-{count}" if count else ""))
    return found


def commands(text: str) -> list[list[str]]:
    return [shlex.split(line) for line in text.splitlines()
            if line.startswith("uv run --locked python -m ")]


@lru_cache
def module_help(module: str) -> str:
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
    result = subprocess.run([sys.executable, "-m", module, "--help"], cwd=ROOT,
                            env=env, capture_output=True, text=True, encoding="utf-8",
                            timeout=60)
    assert result.returncode == 0, (module, result.returncode)
    return result.stdout + result.stderr


def selected_documents() -> list[Path]:
    name = os.environ.get("LINEAGE_HANDBOOK_DOCUMENT")
    if name:
        if not re.fullmatch(r"exp[0-9]+_[A-Za-z0-9_]+\.md", name):
            raise ValueError("只接受既有實驗手冊檔名")
        return [DOCS / name]
    return [p for p in sorted(DOCS.glob("exp*.md")) if not p.stem.endswith("_delivery")]


def test_anchor_fixture_detects_missing_and_duplicate():
    actual = anchors("# 健康資料\n## 如何使用\n## 如何使用\n```python\n# 不算標題\n```")
    assert actual == {"健康資料", "如何使用", "如何使用-1"}
    assert "不存在" not in actual


def test_commands_fixture_keeps_parameter_values():
    parsed = commands("uv run --locked python -m experiments.exp1_cold_start --seed 42")
    assert parsed == [["uv", "run", "--locked", "python", "-m",
                       "experiments.exp1_cold_start", "--seed", "42"]]


def test_handbook_relative_links_and_anchors():
    for doc in selected_documents():
        for row in local_links(doc, ROOT):
            assert row["exists"], (doc.name, row["link"])
            if row["anchor"] and row["target"].endswith(".md"):
                target = ROOT / row["target"]
                assert unquote(row["anchor"]) in anchors(target.read_text(encoding="utf-8")), (
                    doc.name, row["link"])


def test_documented_uv_commands_match_real_help():
    for doc in selected_documents():
        for command in commands(doc.read_text(encoding="utf-8")):
            module = command[5]
            help_text = module_help(module)
            for value in command[6:]:
                if value.startswith("--"):
                    flag = value.split("=")[0]
                    assert re.search(r"(?<![\w-])" + re.escape(flag) + r"(?![\w-])", help_text), (
                        doc.name, module, flag)


def test_exp1_fit_roles_and_legacy_exception_are_explicit():
    text = (DOCS / "exp1_cold_start.md").read_text(encoding="utf-8")
    for term in ("legacy例外", "train本身", "沒有去重", "stride", "未知召回率",
                 "同馬達、同轉速", "沒有epoch", "macro_detect_rate"):
        assert term in text, term
    source = ast.parse((ROOT / "experiments/exp1_cold_start.py").read_text(encoding="utf-8"))
    assert {"run", "iter_run", "main"}.issubset(
        {n.name for n in source.body if isinstance(n, ast.FunctionDef)})


def test_web_catalog_documents_and_guide_parser_unchanged():
    for entry in CATALOG:
        assert (ROOT / entry["doc"]).is_file(), entry["id"]
    overview = (ROOT / "docs/navigation/exp24_實驗總覽.md").read_text(encoding="utf-8")
    table = [line for line in overview.splitlines() if line.startswith("|")]
    assert len(table) == 26
    assert all(len(line.split("|")[1:-1]) == 8 for line in table)
    # 實驗手冊不改導覽表格的內容或頁面行為。
    for doc in selected_documents():
        for target in re.findall(r"\]\((https?://[^)]+)\)", doc.read_text(encoding="utf-8")):
            assert not urlsplit(target).path.startswith("/Users/")
