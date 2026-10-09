#!/usr/bin/env bash
set -euo pipefail
# macOS 共用正式安裝流程；只有明示 legacy 才加入非正式 extras。
ARGS=()
for ARG in "$@"; do
    if [ "$ARG" = "--legacy" ]; then ARGS+=(--legacy-mac); else ARGS+=("$ARG"); fi
done
exec bash "$(dirname -- "$0")/build_uv.sh" "${ARGS[@]}"
