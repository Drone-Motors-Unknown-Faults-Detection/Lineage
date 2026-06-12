#!/bin/bash

# 參考指令
# albert@aero01:~/Ancestor$ source venv/bin/activate
# ((venv) ) albert@aero01:~/Ancestor$ jupyter execute Step3_Model_1.ipynb

set -e

clear

VENV_DIR="venv"
JUPYTER="$VENV_DIR/bin/jupyter"

NOTEBOOKS=(
    # 基礎版本（Model 1 ~ 9）
    Step3_Model_01.ipynb
    Step3_Model_02.ipynb
    Step3_Model_03.ipynb
    Step3_Model_04.ipynb
    Step3_Model_05.ipynb
    Step3_Model_06.ipynb
    Step3_Model_07.ipynb
    Step3_Model_08.ipynb
    Step3_Model_09.ipynb
    # OneStage 遷移學習（Model 10 ~ 27）
    Step3_Model_10_OneStage.ipynb
    Step3_Model_11_OneStage.ipynb
    Step3_Model_12_OneStage.ipynb
    Step3_Model_13_OneStage.ipynb
    Step3_Model_14_OneStage.ipynb
    Step3_Model_15_OneStage.ipynb
    Step3_Model_16_OneStage.ipynb
    Step3_Model_17_OneStage.ipynb
    Step3_Model_18_OneStage.ipynb
    Step3_Model_19_OneStage.ipynb
    Step3_Model_20_OneStage.ipynb
    Step3_Model_21_OneStage.ipynb
    Step3_Model_22_OneStage.ipynb
    Step3_Model_23_OneStage.ipynb
    Step3_Model_24_OneStage.ipynb
    Step3_Model_25_OneStage.ipynb
    Step3_Model_26_OneStage.ipynb
    Step3_Model_27_OneStage.ipynb
    # TwoStage 遷移學習（Model 10 ~ 27）
    Step3_Model_10_TwoStage.ipynb
    Step3_Model_11_TwoStage.ipynb
    Step3_Model_12_TwoStage.ipynb
    Step3_Model_13_TwoStage.ipynb
    Step3_Model_14_TwoStage.ipynb
    Step3_Model_15_TwoStage.ipynb
    Step3_Model_16_TwoStage.ipynb
    Step3_Model_17_TwoStage.ipynb
    Step3_Model_18_TwoStage.ipynb
    Step3_Model_19_TwoStage.ipynb
    Step3_Model_20_TwoStage.ipynb
    Step3_Model_21_TwoStage.ipynb
    Step3_Model_22_TwoStage.ipynb
    Step3_Model_23_TwoStage.ipynb
    Step3_Model_24_TwoStage.ipynb
    Step3_Model_25_TwoStage.ipynb
    Step3_Model_26_TwoStage.ipynb
    Step3_Model_27_TwoStage.ipynb
)

TOTAL=${#NOTEBOOKS[@]}
COUNT=0

for NOTEBOOK in "${NOTEBOOKS[@]}"; do
    COUNT=$((COUNT + 1))
    echo "[INFO] ($COUNT/$TOTAL) Exec $NOTEBOOK"
    JUPYTER_NOTEBOOK_NAME="$NOTEBOOK" "$JUPYTER" execute "$NOTEBOOK"
done

echo "[INFO] All $TOTAL notebooks completed."
