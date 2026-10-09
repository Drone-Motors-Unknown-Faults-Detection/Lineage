#!/usr/bin/env bash
set -euo pipefail
# 保留歷史入口名稱；使用官方 venv 與單一 constraints，不刪除既有環境。
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
"$PYTHON_BIN" -c 'import sys; assert sys.version_info[:2] == (3, 10), "正式安裝要求 Python 3.10.x"'
"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install -c runtime-constraints.txt pip setuptools wheel
TARGET="."
if [ -n "$EXTRA" ]; then
    echo "legacy extras 未完整鎖版，不屬於正式驗證環境" >&2
    TARGET=".[$EXTRA]"
fi
"$VENV_DIR/bin/python" -m pip install --no-build-isolation -c runtime-constraints.txt "$TARGET"
"$VENV_DIR/bin/python" -m pip check
"$VENV_DIR/bin/python" -m core.runtime_environment
