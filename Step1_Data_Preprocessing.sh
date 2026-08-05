#!/bin/bash

set -e

# clear 在無 TTY 時（nohup / cron / CI）會回傳 1，配上 set -e 會讓整支腳本靜默中止
if [ -t 1 ]; then clear 2>/dev/null || true; fi

VENV_DIR="venv"
PYTHON="$VENV_DIR/bin/python"

SCRIPTS=(
    Step1_Data_Preprocessing_figure_6000.py
    Step1_Data_Preprocessing_figure_8000.py
    Step1_Data_Preprocessing_figure_11000.py
    Step1_Data_Preprocessing_save_6000_1.py
    Step1_Data_Preprocessing_save_6000_2.py
    Step1_Data_Preprocessing_save_6000_3.py
    Step1_Data_Preprocessing_save_8000_1.py
    Step1_Data_Preprocessing_save_8000_2.py
    Step1_Data_Preprocessing_save_8000_3.py
    Step1_Data_Preprocessing_save_11000_1.py
    Step1_Data_Preprocessing_save_11000_2.py
    Step1_Data_Preprocessing_save_11000_3.py
)

TOTAL=${#SCRIPTS[@]}
COUNT=0

for SCRIPT in "${SCRIPTS[@]}"; do
    COUNT=$((COUNT + 1))
    echo "[INFO] ($COUNT/$TOTAL) Exec $SCRIPT"
    "$PYTHON" "$SCRIPT"
done

echo "[INFO] All $TOTAL scripts completed."
