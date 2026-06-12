#!/bin/bash

set -e

clear

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