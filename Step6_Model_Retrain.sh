#!/bin/bash

# 參考指令
# albert@aero01:~/Lineage$ source venv/bin/activate
# ((venv) ) albert@aero01:~/Lineage$ jupyter execute Step6_Model_1_Retrain.ipynb

set -e

# clear 在無 TTY 時（nohup / cron / CI）會回傳 1，配上 set -e 會讓整支腳本靜默中止
if [ -t 1 ]; then clear 2>/dev/null || true; fi

VENV_DIR="venv"
JUPYTER="$VENV_DIR/bin/jupyter"

NOTEBOOKS=(
    Step6_Model_01_Retrain.ipynb
    Step6_Model_02_Retrain.ipynb
    Step6_Model_03_Retrain.ipynb
    Step6_Model_04_Retrain.ipynb
    Step6_Model_05_Retrain.ipynb
    Step6_Model_06_Retrain.ipynb
    Step6_Model_07_Retrain.ipynb
    Step6_Model_08_Retrain.ipynb
    Step6_Model_09_Retrain.ipynb
    Step6_Model_10_Retrain.ipynb
    Step6_Model_11_Retrain.ipynb
    Step6_Model_12_Retrain.ipynb
    Step6_Model_13_Retrain.ipynb
    Step6_Model_14_Retrain.ipynb
    Step6_Model_15_Retrain.ipynb
    Step6_Model_16_Retrain.ipynb
    Step6_Model_17_Retrain.ipynb
    Step6_Model_18_Retrain.ipynb
    Step6_Model_19_Retrain.ipynb
    Step6_Model_20_Retrain.ipynb
    Step6_Model_21_Retrain.ipynb
    Step6_Model_22_Retrain.ipynb
    Step6_Model_23_Retrain.ipynb
    Step6_Model_24_Retrain.ipynb
    Step6_Model_25_Retrain.ipynb
    Step6_Model_26_Retrain.ipynb
    Step6_Model_27_Retrain.ipynb
)

TOTAL=${#NOTEBOOKS[@]}
COUNT=0

for NOTEBOOK in "${NOTEBOOKS[@]}"; do
    COUNT=$((COUNT + 1))
    echo "[INFO] ($COUNT/$TOTAL) Exec $NOTEBOOK"
    JUPYTER_NOTEBOOK_NAME="$NOTEBOOK" "$JUPYTER" execute "$NOTEBOOK"
done

echo "[INFO] All $TOTAL notebooks completed."
