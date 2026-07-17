#!/bin/bash
# RenPG Maker - local release builder
# Creates a distributable zip under dist/

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

VERSION=$(grep -E '^version\s*=\s*"' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
PROJECT_NAME="RenPGMaker"
RELEASE_NAME="${PROJECT_NAME}-v${VERSION}"
OUT_DIR="dist/${RELEASE_NAME}"
ZIP_FILE="dist/${RELEASE_NAME}.zip"

echo "[build] Building release ${RELEASE_NAME}..."

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

cp -r \
    pyproject.toml \
    requirements.txt \
    README.md \
    README_IT.md \
    start.sh \
    start.bat \
    rpgm2vn \
    img \
    "$OUT_DIR/"

chmod +x "$OUT_DIR/start.sh"

# Rimuove file superflui dal pacchetto
find "$OUT_DIR" -type d -name '__pycache__' -exec rm -rf {} +
find "$OUT_DIR" -type f \( -name '*.pyc' -o -name '.DS_Store' -o -name '*.bak*' -o -name 'Icon?' \) -delete

rm -f "$ZIP_FILE"
(cd dist && zip -r "${RELEASE_NAME}.zip" "${RELEASE_NAME}")

echo "[build] Release ready: $ZIP_FILE"
