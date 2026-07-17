#!/usr/bin/env bash
# Crea un bundle Linux portatile autocontenuto per RenPG Maker
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="RenPGMaker"
OUT_DIR="$SCRIPT_DIR/dist/${APP_NAME}-linux"
ARCHIVE="$SCRIPT_DIR/dist/${APP_NAME}-linux.tar.gz"

echo "[RenPG Maker] Building ${APP_NAME}-linux..."

rm -rf "$OUT_DIR" "$ARCHIVE"
mkdir -p "$OUT_DIR"

# Crea venv dentro il bundle
echo "[RenPG Maker] Creating virtual environment..."
python3 -m venv "$OUT_DIR/.venv"

PYTHON="$OUT_DIR/.venv/bin/python"
PIP="$OUT_DIR/.venv/bin/pip"

echo "[RenPG Maker] Installing dependencies..."
"$PIP" install --upgrade pip
"$PIP" install "customtkinter>=5.2" "pillow>=10.0"

# Copia tcl/tk per renderlo autocontenuto
PYTHON_BASE=$("$PYTHON" -c "import sys; print(sys.base_prefix)")

copy_tcltk() {
    local name="$1"
    local src dst
    dst="$OUT_DIR/.venv/lib/${name}"
    for src in \
        "$PYTHON_BASE/lib/${name}" \
        "$PYTHON_BASE/share/${name}" \
        "/usr/share/tcltk/${name}" \
        "/usr/lib/${name}" \
        "/usr/local/lib/${name}"
    do
        if [ -d "$src" ]; then
            cp -R "$src" "$dst"
            echo "[RenPG Maker] Copied $name from $src"
            return 0
        fi
    done
    echo "[RenPG Maker] Warning: $name not found; bundle may need system Tcl/Tk."
    return 1
}

copy_tcltk "tcl8.6" || true
copy_tcltk "tk8.6" || true

# Copia progetto
echo "[RenPG Maker] Copying project..."
cp -R "$SCRIPT_DIR/rpgm2vn" "$OUT_DIR/rpgm2vn"
cp -R "$SCRIPT_DIR/img" "$OUT_DIR/img"

# Launcher
cat > "$OUT_DIR/RenPGMaker" <<'LAUNCHER'
#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PYTHON="$ROOT/.venv/bin/python"
[ -d "$ROOT/.venv/lib/tcl8.6" ] && export TCL_LIBRARY="$ROOT/.venv/lib/tcl8.6"
[ -d "$ROOT/.venv/lib/tk8.6" ] && export TK_LIBRARY="$ROOT/.venv/lib/tk8.6"

export PYTHONPATH="$ROOT"
exec "$PYTHON" -m rpgm2vn.gui
LAUNCHER
chmod +x "$OUT_DIR/RenPGMaker"

# Archivio
echo "[RenPG Maker] Creating archive..."
tar -czf "$ARCHIVE" -C "$SCRIPT_DIR/dist" "${APP_NAME}-linux"

echo "[RenPG Maker] Linux bundle ready: $ARCHIVE"
