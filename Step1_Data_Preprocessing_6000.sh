#!/bin/bash

set -e

clear

VENV_DIR="venv"
PYTHON="$VENV_DIR/bin/python"

SCRIPTS=(
    Step1_Data_Preprocessing_figure_6000_1.py
    Step1_Data_Preprocessing_figure_6000_2.py
    Step1_Data_Preprocessing_save_6000_1.py
    Step1_Data_Preprocessing_save_6000_2.py
    Step1_Data_Preprocessing_save_6000_3.py
)

TOTAL=${#SCRIPTS[@]}
COUNT=0

for SCRIPT in "${SCRIPTS[@]}"; do
    COUNT=$((COUNT + 1))
    echo "[INFO] ($COUNT/$TOTAL) Exec $SCRIPT"
    "$PYTHON" "$SCRIPT"
done

echo "[INFO] All $TOTAL scripts completed."
