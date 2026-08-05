#!/bin/bash

set -e

# clear 在無 TTY 時（nohup / cron / CI）會回傳 1，配上 set -e 會讓整支腳本靜默中止
if [ -t 1 ]; then clear 2>/dev/null || true; fi

VENV_DIR="venv"
PYTHON_VERSION="3.10.19"

echo "[INFO] Remove Virtual Python${PYTHON_VERSION} Environment."
rm -rf "$VENV_DIR"

echo "[INFO] Build Virtual Python${PYTHON_VERSION} Environment."
uv venv --python "${PYTHON_VERSION}" --seed "$VENV_DIR"
echo "[INFO] Venv Build Completed"

echo "[INFO] Upgrade PIP Version."
"$VENV_DIR/bin/pip" install --upgrade pip

echo "[INFO] Install Python3 Required Package"
"$VENV_DIR/bin/pip" install ".[mac]"
echo "[INFO] Install Completed"