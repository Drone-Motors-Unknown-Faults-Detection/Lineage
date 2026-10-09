#!/usr/bin/env bash
set -euo pipefail
# 保留歷史入口名稱；環境管理工具固定為 uv，單一 constraints，不刪除既有環境。
cd -- "$(dirname -- "$0")"
PYTHON_BIN="python3.10"
VENV_DIR=".venv310"
EXTRA=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --python) PYTHON_BIN="$2"; shift 2 ;;
        --venv) VENV_DIR="$2"; shift 2 ;;
        --legacy) EXTRA="legacy-linux"; shift ;;
        --legacy-mac) EXTRA="legacy-mac"; shift ;;
        *) echo "未知參數：$1" >&2; exit 2 ;;
    esac
done
if [ -e "$VENV_DIR" ] || [ -L "$VENV_DIR" ]; then
    echo "目標已存在，保留原環境：$VENV_DIR" >&2
    exit 2
fi
command -v uv >/dev/null 2>&1 || { echo "需要先安裝 uv：https://docs.astral.sh/uv/getting-started/installation/" >&2; exit 2; }
"$PYTHON_BIN" -c 'import sys; assert sys.version_info[:2] == (3, 10), "正式安裝要求 Python 3.10.x"'
uv venv --seed --python "$PYTHON_BIN" "$VENV_DIR"
uv pip install --python "$VENV_DIR/bin/python" -c runtime-constraints.txt pip setuptools wheel
TARGET="."
if [ -n "$EXTRA" ]; then
    echo "legacy extras 未完整鎖版，不屬於正式驗證環境" >&2
    TARGET=".[$EXTRA]"
fi
uv pip install --python "$VENV_DIR/bin/python" --no-build-isolation -c runtime-constraints.txt "$TARGET"
"$VENV_DIR/bin/python" -m pip check
"$VENV_DIR/bin/python" -m core.runtime_environment
