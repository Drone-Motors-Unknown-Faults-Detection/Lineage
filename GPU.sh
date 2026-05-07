#!/bin/bash

set -e

clear

echo "[INFO] Watch GPU Usage"
while true; do
    clear
    echo "[TIME] $(date +%Y-%m-%d\ %H:%M:%S)"
    echo ""
    nvidia-smi
    sleep 1
done