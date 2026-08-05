#!/bin/bash

set -e

# clear 在無 TTY 時（nohup / cron / CI）會回傳 1，配上 set -e 會讓整支腳本靜默中止
if [ -t 1 ]; then clear 2>/dev/null || true; fi

VENV_DIR="venv"

echo "[INFO] Remove Virtual Python3.10.19 Environment."
rm -rf "$VENV_DIR"

echo "[INFO] Build Virtual Python3.10.19 Environment."
python3.10 -m venv "$VENV_DIR"
echo "[INFO] Venv Build Completed"

echo "[INFO] Upgrade PIP Version."
"$VENV_DIR/bin/pip" install --upgrade pip

echo "[INFO] Install Python3 Required Package"
"$VENV_DIR/bin/pip" install ".[linux]"
echo "[INFO] Install Completed"