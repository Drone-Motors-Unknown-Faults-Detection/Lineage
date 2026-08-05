"""把專案的 Markdown 文件轉成 HTML。

原本的 .html 是一次性手工產生的，改了 .md 之後沒有對應機制重新產出，
很快就會再度脫節（issue #38）。這支腳本讓轉換可重現：

    venv/bin/python scripts/render_docs.py            # 重新產生全部
    venv/bin/python scripts/render_docs.py --check    # 只檢查是否過期，不寫檔

標題錨點使用保留 CJK 的 slug，文件內以 `#中文標題` 形式撰寫的目錄連結
才能正常跳轉（Python-Markdown 預設的 slugify 會把中文全部濾掉，產生
`#_1`、`#_2` 這類無法對應的 id）。
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
CSS_FILE = Path(__file__).resolve().parent / "templates" / "doc.css"

# (Markdown 來源, 產出的 HTML)
TARGETS = [
    (ROOT / "README.md", ROOT / "README.html"),
    *[
        (p, p.with_suffix(".html"))
        for p in sorted((ROOT / "docs").glob("*.md"))
    ],
]

PAGE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>

<style>
{css}
</style>

</head>
<body>
{body}
</body>
</html>
"""


def slugify(value: str, separator: str = "-") -> str:
    """保留中日韓文字的 slug，讓 `#中文標題` 形式的目錄連結能對得上。"""
    value = unicodedata.normalize("NFKC", value).strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    return re.sub(r"[\s_]+", separator, value).strip(separator)


def render(md_path: Path, css: str) -> str:
    text = md_path.read_text(encoding="utf-8")

    # 第一個 h1 當標題；沒有的話退回檔名
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = m.group(1).strip() if m else md_path.stem

    # 文件間互相連結時指向 .md，輸出成 HTML 後要改指 .html
    body = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"slugify": lambda v, s: slugify(v, s)}},
    ).convert(text)
    body = re.sub(r'(href="[^"]*?)\.md(#[^"]*)?"', r'\1.html\2"', body)

    return PAGE.format(title=title, css=css, body=body)


def main() -> int:
    check_only = "--check" in sys.argv
    css = CSS_FILE.read_text(encoding="utf-8").rstrip("\n")

    stale = []
    for md_path, html_path in TARGETS:
        if not md_path.exists():
            print(f"  略過（來源不存在）：{md_path.relative_to(ROOT)}")
            continue
        rendered = render(md_path, css)
        current = html_path.read_text(encoding="utf-8") if html_path.exists() else None

        if rendered == current:
            print(f"  一致：{html_path.relative_to(ROOT)}")
            continue

        stale.append(html_path)
        if check_only:
            print(f"  過期：{html_path.relative_to(ROOT)}")
        else:
            html_path.write_text(rendered, encoding="utf-8")
            print(f"  已更新：{html_path.relative_to(ROOT)}")

    if check_only and stale:
        print(f"\n{len(stale)} 個 HTML 與 Markdown 不同步，請執行 "
              f"`venv/bin/python scripts/render_docs.py`")
        return 1

    print(f"\n完成，共 {len(TARGETS)} 份文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
