#!/bin/bash

set -e

clear

VENV_DIR="venv"

echo "[INFO] Remove Virtual Python3.12.13 Environment."
rm -rf "$VENV_DIR"

echo "[INFO] Build Virtual Python3.12.13 Environment."
python3.12 -m venv "$VENV_DIR"
echo "[INFO] Venv Build Completed"

echo "[INFO] Upgrade PIP Version."
"$VENV_DIR/bin/pip" install --upgrade pip

echo "[INFO] Install Python3 Required Package"
"$VENV_DIR/bin/pip" install -r requirements.txt
echo "[INFO] Install Completed"