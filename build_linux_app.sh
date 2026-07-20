#!/usr/bin/env bash
# build_linux_app.sh
# Package SilkModHub into a standalone Linux executable (+ optional .desktop entry)
#
# Usage:
#   chmod +x build_linux_app.sh
#   ./build_linux_app.sh
#
# Requirements:
#   - Must run on Linux (PyInstaller only builds for the current OS)
#   - Python 3.9+ installed (python3, python3-venv, python3-pip)
#   - PyQt6 needs some system libraries present on most desktop distros
#     already; if the built binary fails to start with library errors,
#     install your distro's Qt6/X11 runtime packages
#     (e.g. Debian/Ubuntu: sudo apt install libgl1 libxkbcommon0 libegl1)
#   - If you've already compiled silk_backend*.so via build.sh, it will be
#     bundled automatically for the high-performance backend. Otherwise
#     the app falls back to the pure-Python implementation (same
#     features, slightly slower).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
APP_NAME="SilkModHub"

NATIVE_MODULE=""

echo "==> [1/5] Setting up virtualenv"
cd "$PROJECT_ROOT"
if [ ! -d ".venv_linuxbuild" ]; then
    python3 -m venv .venv_linuxbuild
fi
# shellcheck disable=SC1091
source .venv_linuxbuild/bin/activate

echo "==> [2/5] Installing dependencies (PyQt6, requests, pyinstaller)"
pip install --upgrade pip >/dev/null
pip install -r "$FRONTEND_DIR/requirements.txt"
pip install pyinstaller

echo "==> [3/5] Looking for compiled C++ backend module (optional)"
FOUND_SO="$(find "$FRONTEND_DIR" -maxdepth 1 -name "silk_backend*.so" 2>/dev/null | head -n 1)"
if [ -n "$FOUND_SO" ]; then
    NATIVE_MODULE="$FOUND_SO"
    printf '    Found native module: %s (will bundle for high-performance backend)\n' "$NATIVE_MODULE"
else
    echo "    No silk_backend*.so found, will fall back to pure Python implementation"
    echo "    (To enable the C++ backend, run ./build.sh first, then re-run this script)"
fi

echo "==> [4/5] Packaging with PyInstaller"
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

if [ -f "$FRONTEND_DIR/assets/icon.png" ]; then
    PYINSTALLER_ARGS+=(--icon "$FRONTEND_DIR/assets/icon.png")
fi

if [ -n "$NATIVE_MODULE" ]; then
    PYINSTALLER_ARGS+=(--add-binary "$NATIVE_MODULE:.")
fi

pyinstaller "${PYINSTALLER_ARGS[@]}" "$FRONTEND_DIR/main.py"

echo "==> [5/5] Writing a .desktop launcher next to the build"
DESKTOP_FILE="$PROJECT_ROOT/dist/$APP_NAME.desktop"
cat > "$DESKTOP_FILE" << DESKTOP_ENTRY
[Desktop Entry]
Type=Application
Name=$APP_NAME
Comment=Hollow Knight Silksong mod manager
Exec=$PROJECT_ROOT/dist/$APP_NAME/$APP_NAME
Icon=$FRONTEND_DIR/assets/icon.png
Terminal=false
Categories=Game;Utility;
DESKTOP_ENTRY
chmod +x "$DESKTOP_FILE"

echo ""
echo "=================================================="
echo " Done!"
echo " Executable: $PROJECT_ROOT/dist/$APP_NAME/$APP_NAME"
echo " Desktop entry (edit paths if you move the folder): $DESKTOP_FILE"
echo "=================================================="
echo ""
echo "To run: $PROJECT_ROOT/dist/$APP_NAME/$APP_NAME"
echo ""
echo "To install the launcher for your user (optional):"
echo "  cp \"$DESKTOP_FILE\" ~/.local/share/applications/"
echo ""
echo "To distribute: zip the whole dist/$APP_NAME/ folder (it's self-contained"
echo "aside from normal system libraries). For a single portable file, look"
echo "into building an AppImage from this same dist/$APP_NAME/ output using"
echo "appimagetool (https://github.com/AppImage/AppImageKit) -- optional,"
echo "not required for local use."
