#!/usr/bin/env bash
# Crea un bundle .app macOS autocontenuto per RenPG Maker
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="RenPGMaker"
BUNDLE_DIR="$SCRIPT_DIR/dist/${APP_NAME}.app"
PROJECT_DIR="$BUNDLE_DIR/Contents/Resources/project"
ICNS_SRC="$SCRIPT_DIR/img/logo.png"
ICONSET_DIR="$SCRIPT_DIR/img/icon.iconset"

echo "[RenPG Maker] Building ${APP_NAME}.app..."

rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR/Contents/MacOS"
mkdir -p "$PROJECT_DIR"

# Copia dentro il bundle i file necessari a far girare la GUI
echo "[RenPG Maker] Copying project into bundle..."
cp -R "$SCRIPT_DIR/.venv" "$PROJECT_DIR/.venv"
cp -R "$SCRIPT_DIR/rpgm2vn" "$PROJECT_DIR/rpgm2vn"
cp -R "$SCRIPT_DIR/img" "$PROJECT_DIR/img"

# Crea o copia l'icona .icns
ICNS_FILE="$BUNDLE_DIR/Contents/Resources/${APP_NAME}.icns"
if command -v iconutil &>/dev/null && [ -d "$ICONSET_DIR" ]; then
    if iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE" 2>/dev/null; then
        echo "[RenPG Maker] Generated icns from icon.iconset."
    else
        cp "$ICNS_SRC" "$ICNS_FILE"
        echo "[RenPG Maker] iconutil failed, using img/logo.png as icns."
    fi
else
    cp "$ICNS_SRC" "$ICNS_FILE"
    echo "[RenPG Maker] iconutil not found, using img/logo.png as icns."
fi

# Info.plist
cat > "$BUNDLE_DIR/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleDisplayName</key>
    <string>RenPG Maker</string>
    <key>CFBundleExecutable</key>
    <string>RenPGMaker</string>
    <key>CFBundleIconFile</key>
    <string>RenPGMaker</string>
    <key>CFBundleIdentifier</key>
    <string>com.huchukato.renpgmaker</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>RenPG Maker</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# Script di lancio autocontenuto
cat > "$BUNDLE_DIR/Contents/MacOS/RenPGMaker" <<'LAUNCHER'
#!/usr/bin/env bash
# Launcher autocontenuto per RenPG Maker.app

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$APP_DIR/../Resources/project"
cd "$PROJECT"

PYTHON="$PROJECT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    osascript -e 'display dialog "Python virtualenv not found inside the app bundle." buttons {"OK"} default button 1' &
    exit 1
fi

PYTHON_BASE=$("$PYTHON" -c "import sys; print(sys.base_prefix)")
if [ -d "$PYTHON_BASE/lib/tcl8.6" ]; then
    export TCL_LIBRARY="$PYTHON_BASE/lib/tcl8.6"
fi
if [ -d "$PYTHON_BASE/lib/tk8.6" ]; then
    export TK_LIBRARY="$PYTHON_BASE/lib/tk8.6"
fi

export PYTHONPATH="$PROJECT"
exec "$PYTHON" -m rpgm2vn.gui
LAUNCHER

chmod +x "$BUNDLE_DIR/Contents/MacOS/RenPGMaker"

echo "[RenPG Maker] Bundle ready: $BUNDLE_DIR"
