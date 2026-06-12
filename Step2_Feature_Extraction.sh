#!/bin/bash

set -e

clear

VENV_DIR="venv"
PYTHON="$VENV_DIR/bin/python"

SCRIPTS=(
    Step2_Feature_Extraction_6000_1.py
    Step2_Feature_Extraction_6000_2.py
    Step2_Feature_Extraction_6000_3.py
    Step2_Feature_Extraction_8000_1.py
    Step2_Feature_Extraction_8000_2.py
    Step2_Feature_Extraction_8000_3.py
    Step2_Feature_Extraction_11000_1.py
    Step2_Feature_Extraction_11000_2.py
    Step2_Feature_Extraction_11000_3.py
)

TOTAL=${#SCRIPTS[@]}
COUNT=0

for SCRIPT in "${SCRIPTS[@]}"; do
    COUNT=$((COUNT + 1))
    echo "[INFO] ($COUNT/$TOTAL) Exec $SCRIPT"
    "$PYTHON" "$SCRIPT"
done

echo "[INFO] All $TOTAL scripts completed."
