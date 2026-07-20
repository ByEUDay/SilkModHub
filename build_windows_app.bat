@echo off
REM build_windows_app.bat
REM Package SilkModHub into a Windows .exe
REM
REM Usage: double-click this file, or run it from cmd/PowerShell:
REM   build_windows_app.bat
REM
REM Requirements:
REM   - Must run on Windows (PyInstaller only builds for the current OS)
REM   - Python 3.9+ installed and on PATH (check "Add python.exe to PATH"
REM     during install from python.org)
REM   - If you've already compiled silk_backend*.pyd via CMake, it will be
REM     bundled automatically for the high-performance backend. Otherwise
REM     the app falls back to the pure-Python implementation (same
REM     features, slightly slower).

setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "APP_NAME=SilkModHub"

echo ==^> [1/4] Setting up virtualenv
cd /d "%PROJECT_ROOT%"
if not exist ".venv_winbuild" (
    python -m venv .venv_winbuild
    if errorlevel 1 (
        echo Failed to create virtualenv. Is Python installed and on PATH?
        goto :end
    )
)
call ".venv_winbuild\Scripts\activate.bat"

echo ==^> [2/4] Installing dependencies (PyQt6, requests, pyinstaller, pillow)
python -m pip install --upgrade pip >nul
pip install -r "%FRONTEND_DIR%\requirements.txt"
pip install pyinstaller pillow

echo ==^> [3/4] Converting icon.png to .ico
set "ICON_PNG=%FRONTEND_DIR%\assets\icon.png"
set "ICO_PATH="
if exist "%ICON_PNG%" (
    mkdir "%PROJECT_ROOT%build_windows_assets" 2>nul
    set "ICO_PATH=%PROJECT_ROOT%build_windows_assets\icon.ico"
    python -c "from PIL import Image; im = Image.open(r'%ICON_PNG%'); im.save(r'!ICO_PATH!', sizes=[(16,16),(32,32),(48,48),(256,256)])"
    echo     Icon generated: !ICO_PATH!
) else (
    echo     icon.png not found at %ICON_PNG%, using PyInstaller default icon
)

echo ==^> [4/4] Looking for compiled C++ backend module (optional)
set "NATIVE_MODULE="
for %%f in ("%FRONTEND_DIR%\silk_backend*.pyd") do (
    set "NATIVE_MODULE=%%f"
)
if defined NATIVE_MODULE (
    echo     Found native module: !NATIVE_MODULE! (will bundle for high-performance backend)
) else (
    echo     No silk_backend*.pyd found, will fall back to pure Python implementation
    echo     ^(To enable the C++ backend, build the CMake project first with the
    echo     matching Python version, then re-run this script^)
)

echo ==^> Packaging .exe with PyInstaller
if exist "%PROJECT_ROOT%build" rmdir /s /q "%PROJECT_ROOT%build"
if exist "%PROJECT_ROOT%dist" rmdir /s /q "%PROJECT_ROOT%dist"

set "PYI_ARGS=--name %APP_NAME% --windowed --noconfirm --clean"
set "PYI_ARGS=%PYI_ARGS% --add-data "%FRONTEND_DIR%\themes;themes""
set "PYI_ARGS=%PYI_ARGS% --add-data "%FRONTEND_DIR%\assets;assets""
set "PYI_ARGS=%PYI_ARGS% --paths "%FRONTEND_DIR%""

if defined ICO_PATH (
    if exist "%ICO_PATH%" (
        set "PYI_ARGS=%PYI_ARGS% --icon "%ICO_PATH%""
    )
)

if defined NATIVE_MODULE (
    set "PYI_ARGS=%PYI_ARGS% --add-binary "!NATIVE_MODULE!;.""
)

pyinstaller %PYI_ARGS% "%FRONTEND_DIR%\main.py"

echo.
echo ==================================================
echo  Done!
echo  .exe location: %PROJECT_ROOT%dist\%APP_NAME%\%APP_NAME%.exe
echo ==================================================
echo.
echo You can zip the whole dist\%APP_NAME%\ folder to distribute it,
echo or double-click %APP_NAME%.exe inside it to test.
echo.
echo If Windows SmartScreen blocks it: click "More info" -^> "Run anyway".
echo (Expected, since the exe isn't code-signed.)

:end
endlocal
pause
