#!/bin/bash

set -e

clear

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
"$VENV_DIR/bin/pip" install -r requirements_mac.txt
echo "[INFO] Install Completed"