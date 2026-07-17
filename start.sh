#!/usr/bin/env bash
# RenPG Maker - macOS/Linux Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
OS_NAME="$(uname -s)"

echo "[RenPG Maker] Detected OS: $OS_NAME"

if ! command -v uv &>/dev/null; then
    echo "[RenPG Maker] uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv &>/dev/null; then
    echo "[RenPG Maker] ERROR: uv installation failed." >&2
    read -p "Press Enter to exit..."
    exit 1
fi

cd "$SCRIPT_DIR"
export UV_LINK_MODE=copy

if [ ! -d "$VENV_DIR" ]; then
    echo "[RenPG Maker] Creating virtual environment..."
    uv venv "$VENV_DIR"
fi

echo "[RenPG Maker] Installing dependencies..."
uv pip install --python "$VENV_DIR/bin/python" -e "$SCRIPT_DIR"

echo "[RenPG Maker] Configuring Tcl/Tk..."
PYTHON_BASE=$("$VENV_DIR/bin/python" -c "import sys; print(sys.base_prefix)")
if [ -d "$PYTHON_BASE/lib/tcl8.6" ]; then
    export TCL_LIBRARY="$PYTHON_BASE/lib/tcl8.6"
fi
if [ -d "$PYTHON_BASE/lib/tk8.6" ]; then
    export TK_LIBRARY="$PYTHON_BASE/lib/tk8.6"
fi

echo "[RenPG Maker] Starting GUI..."
"$VENV_DIR/bin/python" -m rpgm2vn.gui
