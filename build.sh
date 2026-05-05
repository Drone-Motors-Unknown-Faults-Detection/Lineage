#!/bin/bash

set -e

clear

echo "[INFO] Build Virtual Python3 Env."
python3.12 -m venv venv
echo "[INFO] Venv Build Completed"

echo "[INFO] Activate the Python3 venv"
source venv/bin/activate

echo "[INFO] Upgrade PIP Version."
pip install --upgrade pip

echo "[INFO] Install Python3 Required Package"
pip install -r requirements.txt
echo "[INFO] Install Completed"

deactivate