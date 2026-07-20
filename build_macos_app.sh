#!/usr/bin/env bash
# build_macos_app.sh
# Package SilkModHub into a macOS .app
#
# Usage:
#   chmod +x build_macos_app.sh
#   ./build_macos_app.sh
#
# Requirements:
#   - Must run on macOS (PyInstaller only builds for the current OS)
#   - Python 3.9+ installed (brew install python, or the official installer)
#   - If you've already compiled silk_backend*.so via build.sh, it will be
#     bundled automatically for the high-performance backend. Otherwise the
#     app falls back to the pure-Python implementation (same features,
#     slightly slower).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
APP_NAME="SilkModHub"

# Initialize up front so `set -u` never complains in any branch
ICNS_PATH=""
NATIVE_MODULE=""

echo "==> [1/5] Setting up virtualenv"
cd "$PROJECT_ROOT"
if [ ! -d ".venv_macbuild" ]; then
    python3 -m venv .venv_macbuild
fi
# shellcheck disable=SC1091
source .venv_macbuild/bin/activate

echo "==> [2/5] Installing dependencies (PyQt6, requests, pyinstaller)"
pip install --upgrade pip >/dev/null
pip install -r "$FRONTEND_DIR/requirements.txt"
pip install pyinstaller pillow

echo "==> [3/5] Converting icon.png to .icns"
ICON_PNG="$FRONTEND_DIR/assets/icon.png"
mkdir -p "$PROJECT_ROOT/build_macos_assets"

if [ -f "$ICON_PNG" ]; then
    ICONSET_DIR="$PROJECT_ROOT/build_macos_assets/icon.iconset"
    rm -rf "$ICONSET_DIR"
    mkdir -p "$ICONSET_DIR"
    for size in 16 32 128 256 512; do
        sips -z "$size" "$size" "$ICON_PNG" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null
        double=$((size * 2))
        sips -z "$double" "$double" "$ICON_PNG" --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" >/dev/null
    done
    iconutil -c icns "$ICONSET_DIR" -o "$PROJECT_ROOT/build_macos_assets/icon.icns"
    ICNS_PATH="$PROJECT_ROOT/build_macos_assets/icon.icns"
    printf '    Icon generated: %s\n' "$ICNS_PATH"
else
    printf '    icon.png not found at %s, using PyInstaller default icon\n' "$ICON_PNG"
fi

echo "==> [4/5] Looking for compiled C++ backend module (optional)"
FOUND_SO="$(find "$FRONTEND_DIR" -maxdepth 1 -name "silk_backend*.so" 2>/dev/null | head -n 1)"
if [ -n "$FOUND_SO" ]; then
    NATIVE_MODULE="$FOUND_SO"
    printf '    Found native module: %s (will bundle for high-performance backend)\n' "$NATIVE_MODULE"
else
    echo "    No silk_backend*.so found, will fall back to pure Python implementation"
    echo "    (To enable the C++ backend, run ./build.sh first, then re-run this script)"
fi

echo "==> [5/5] Packaging .app with PyInstaller"
rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist"

PYINSTALLER_ARGS=(
    --name "$APP_NAME"
    --windowed
    --noconfirm
    --clean
    --add-data "$FRONTEND_DIR/themes:themes"
    --add-data "$FRONTEND_DIR/assets:assets"
    --paths "$FRONTEND_DIR"
)

if [ -n "$ICNS_PATH" ] && [ -f "$ICNS_PATH" ]; then
    PYINSTALLER_ARGS+=(--icon "$ICNS_PATH")
fi

if [ -n "$NATIVE_MODULE" ]; then
    PYINSTALLER_ARGS+=(--add-binary "$NATIVE_MODULE:.")
fi

pyinstaller "${PYINSTALLER_ARGS[@]}" "$FRONTEND_DIR/main.py"

echo ""
echo "=================================================="
echo " Done!"
echo " .app location: $PROJECT_ROOT/dist/$APP_NAME.app"
echo "=================================================="
echo ""
echo "Drag dist/$APP_NAME.app into /Applications, or double-click to test."
echo ""
echo "If macOS says it 'cannot verify the developer':"
echo "  Right-click the .app -> Open -> confirm Open again."
echo "  (This is expected since the app isn't code-signed/notarized.)"
