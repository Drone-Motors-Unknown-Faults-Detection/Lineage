#!/bin/bash

set -e

clear

echo "[INFO] Remove Virtual Python3.12.13 Environment."
rm -rf venv

echo "[INFO] Build Virtual Python3.12.13 Environment.."
python3.12 -m venv venv
echo "[INFO] Venv Build Completed"

echo "[INFO] Activate the Python3.12.13 Environment."
source venv/bin/activate

echo "[INFO] Upgrade PIP Version."
pip install --upgrade pip

echo "[INFO] Install Python3 Required Package"
pip install -r requirements.txt
echo "[INFO] Install Completed"

deactivate