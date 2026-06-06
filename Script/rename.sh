#!/bin/bash

set -e

TARGET_DIR="${1:-.}"

echo "[INFO] Start renaming files in: $TARGET_DIR"

find "$TARGET_DIR" -maxdepth 1 -name "*.ipynb" | while read -r filepath; do
    filename=$(basename "$filepath")
    newname=$(echo "$filename" | sed 's/ /_/g' | sed 's/__/_/g')

    if [ "$filename" != "$newname" ]; then
        mv "$filepath" "$TARGET_DIR/$newname"
        echo "[RENAMED] $filename -> $newname"
    fi
done

echo "[INFO] Rename Completed"