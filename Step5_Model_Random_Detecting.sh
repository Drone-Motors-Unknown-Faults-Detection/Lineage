#!/bin/bash

# 參考指令
# albert@aero01:~/Ancestor$ source venv/bin/activate
# ((venv) ) albert@aero01:~/Ancestor$ jupyter execute Step5_Model_1_Random_Detecting.ipynb

set -e

clear

VENV_DIR="venv"
JUPYTER="$VENV_DIR/bin/jupyter"

NOTEBOOKS=(
    Step5_Model_01_Random_Detecting.ipynb
    Step5_Model_02_Random_Detecting.ipynb
    Step5_Model_03_Random_Detecting.ipynb
    Step5_Model_04_Random_Detecting.ipynb
    Step5_Model_05_Random_Detecting.ipynb
    Step5_Model_06_Random_Detecting.ipynb
    Step5_Model_07_Random_Detecting.ipynb
    Step5_Model_08_Random_Detecting.ipynb
    Step5_Model_09_Random_Detecting.ipynb
    Step5_Model_10_Random_Detecting.ipynb
    Step5_Model_11_Random_Detecting.ipynb
    Step5_Model_12_Random_Detecting.ipynb
    Step5_Model_13_Random_Detecting.ipynb
    Step5_Model_14_Random_Detecting.ipynb
    Step5_Model_15_Random_Detecting.ipynb
    Step5_Model_16_Random_Detecting.ipynb
    Step5_Model_17_Random_Detecting.ipynb
    Step5_Model_18_Random_Detecting.ipynb
    Step5_Model_19_Random_Detecting.ipynb
    Step5_Model_20_Random_Detecting.ipynb
    Step5_Model_21_Random_Detecting.ipynb
    Step5_Model_22_Random_Detecting.ipynb
    Step5_Model_23_Random_Detecting.ipynb
    Step5_Model_24_Random_Detecting.ipynb
    Step5_Model_25_Random_Detecting.ipynb
    Step5_Model_26_Random_Detecting.ipynb
    Step5_Model_27_Random_Detecting.ipynb
)

TOTAL=${#NOTEBOOKS[@]}
COUNT=0

for NOTEBOOK in "${NOTEBOOKS[@]}"; do
    COUNT=$((COUNT + 1))
    echo "[INFO] ($COUNT/$TOTAL) Exec $NOTEBOOK"
    JUPYTER_NOTEBOOK_NAME="$NOTEBOOK" "$JUPYTER" execute "$NOTEBOOK"
done

echo "[INFO] All $TOTAL notebooks completed."
