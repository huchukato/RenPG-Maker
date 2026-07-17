@echo off
:: RenPG Maker - Windows Launcher
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "OS_NAME=Windows"

echo [RenPG Maker] Detected OS: %OS_NAME%

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [RenPG Maker] uv not found. Installing...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.cargo\bin;%LOCALAPPDATA%\Programs\uv;%PATH%"
)

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [RenPG Maker] ERROR: uv installation failed.
    pause
    exit /b 1
)

cd /d "%SCRIPT_DIR%"
set UV_LINK_MODE=copy

if not exist "%VENV_DIR%" (
    echo [RenPG Maker] Creating virtual environment...
    uv venv "%VENV_DIR%"
)

echo [RenPG Maker] Installing dependencies...
uv pip install --python "%VENV_DIR%\Scripts\python.exe" -e "%SCRIPT_DIR%"

echo [RenPG Maker] Configuring Tcl/Tk...
for /f "usebackq tokens=*" %%a in (`"%VENV_DIR%\Scripts\python.exe" -c "import sys; print(sys.base_prefix)"`) do set "PYTHON_BASE=%%a"
if exist "%PYTHON_BASE%\lib\tcl8.6" (
    set "TCL_LIBRARY=%PYTHON_BASE%\lib\tcl8.6"
    set "TK_LIBRARY=%PYTHON_BASE%\lib\tk8.6"
)

echo [RenPG Maker] Starting GUI...
"%VENV_DIR%\Scripts\python.exe" -m rpgm2vn.gui

pause
