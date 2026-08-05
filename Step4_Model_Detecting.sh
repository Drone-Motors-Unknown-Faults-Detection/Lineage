#!/bin/bash

# 參考指令
# albert@aero01:~/Ancestor$ source venv/bin/activate
# ((venv) ) albert@aero01:~/Ancestor$ jupyter execute Step4_Model_1_Detecting.ipynb

set -e

# clear 在無 TTY 時（nohup / cron / CI）會回傳 1，配上 set -e 會讓整支腳本靜默中止
if [ -t 1 ]; then clear 2>/dev/null || true; fi

VENV_DIR="venv"
JUPYTER="$VENV_DIR/bin/jupyter"

NOTEBOOKS=(
    Step4_Model_01_Detecting.ipynb
    Step4_Model_02_Detecting.ipynb
    Step4_Model_03_Detecting.ipynb
    Step4_Model_04_Detecting.ipynb
    Step4_Model_05_Detecting.ipynb
    Step4_Model_06_Detecting.ipynb
    Step4_Model_07_Detecting.ipynb
    Step4_Model_08_Detecting.ipynb
    Step4_Model_09_Detecting.ipynb
    Step4_Model_10_Detecting.ipynb
    Step4_Model_11_Detecting.ipynb
    Step4_Model_12_Detecting.ipynb
    Step4_Model_13_Detecting.ipynb
    Step4_Model_14_Detecting.ipynb
    Step4_Model_15_Detecting.ipynb
    Step4_Model_16_Detecting.ipynb
    Step4_Model_17_Detecting.ipynb
    Step4_Model_18_Detecting.ipynb
    Step4_Model_19_Detecting.ipynb
    Step4_Model_20_Detecting.ipynb
    Step4_Model_21_Detecting.ipynb
    Step4_Model_22_Detecting.ipynb
    Step4_Model_23_Detecting.ipynb
    Step4_Model_24_Detecting.ipynb
    Step4_Model_25_Detecting.ipynb
    Step4_Model_26_Detecting.ipynb
    Step4_Model_27_Detecting.ipynb
)

TOTAL=${#NOTEBOOKS[@]}
COUNT=0

for NOTEBOOK in "${NOTEBOOKS[@]}"; do
    COUNT=$((COUNT + 1))
    echo "[INFO] ($COUNT/$TOTAL) Exec $NOTEBOOK"
    JUPYTER_NOTEBOOK_NAME="$NOTEBOOK" "$JUPYTER" execute "$NOTEBOOK"
done

echo "[INFO] All $TOTAL notebooks completed."
