@echo off
setlocal

pushd "%~dp0.."
set "SCRIPT_DIR=%CD%"
popd
set "APP_NAME=RenPGMaker"
set "OUT_DIR=%SCRIPT_DIR%\dist\%APP_NAME%-windows"
set "ARCHIVE=%SCRIPT_DIR%\dist\%APP_NAME%-windows.zip"

echo [RenPG Maker] Building %APP_NAME%-windows...

rmdir /S /Q "%OUT_DIR%" 2>nul
if exist "%ARCHIVE%" del /Q "%ARCHIVE%" 2>nul
mkdir "%OUT_DIR%"

echo [RenPG Maker] Creating virtual environment...
python -m venv "%OUT_DIR%\.venv"

set "PYTHON=%OUT_DIR%\.venv\Scripts\python.exe"
set "PIP=%OUT_DIR%\.venv\Scripts\pip.exe"

echo [RenPG Maker] Installing dependencies...
"%PIP%" install --upgrade pip
"%PIP%" install customtkinter pillow

echo [RenPG Maker] Bundling Tcl/Tk...
for /f "usebackq tokens=*" %%a in (`"%PYTHON%" -c "import sys; print(sys.base_prefix)"`) do set "PYTHON_BASE=%%a"

if exist "%PYTHON_BASE%\tcl\tcl8.6\" (
    xcopy /E /I /Q "%PYTHON_BASE%\tcl\tcl8.6" "%OUT_DIR%\.venv\tcl\tcl8.6" >nul
)
if exist "%PYTHON_BASE%\tcl\tk8.6\" (
    xcopy /E /I /Q "%PYTHON_BASE%\tcl\tk8.6" "%OUT_DIR%\.venv\tcl\tk8.6" >nul
)

echo [RenPG Maker] Copying project...
xcopy /E /I /Q "%SCRIPT_DIR%\rpgm2vn" "%OUT_DIR%\rpgm2vn" >nul
xcopy /E /I /Q "%SCRIPT_DIR%\img" "%OUT_DIR%\img" >nul

echo [RenPG Maker] Creating launcher...
(
echo @echo off
echo setlocal
echo set "ROOT=%%~dp0"
echo cd /d "%%ROOT%%"
echo set "TCL_LIBRARY=%%ROOT%%.venv\tcl\tcl8.6"
echo set "TK_LIBRARY=%%ROOT%%.venv\tcl\tk8.6"
echo set "PYTHONPATH=%%ROOT%%"
echo start "" "%%ROOT%%.venv\Scripts\pythonw.exe" -m rpgm2vn.gui
) > "%OUT_DIR%\RenPGMaker.bat"

echo [RenPG Maker] Creating archive...
powershell -Command "Compress-Archive -Path '%OUT_DIR%' -DestinationPath '%ARCHIVE%' -Force"

echo [RenPG Maker] Windows bundle ready: %ARCHIVE%
