#!/bin/bash

set -e

# clear 在無 TTY 時（nohup / cron / CI）會回傳 1，配上 set -e 會讓整支腳本靜默中止
if [ -t 1 ]; then clear 2>/dev/null || true; fi

echo "[INFO] Watch GPU Usage"
while true; do
    if [ -t 1 ]; then clear 2>/dev/null || true; fi
    echo "[TIME] $(date +%Y-%m-%d\ %H:%M:%S)"
    echo ""
    nvidia-smi
    sleep 0.5
done