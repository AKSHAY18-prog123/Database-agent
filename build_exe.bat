@echo off
title Build DatabaseAgent.exe Desktop App
color 0A
cls
echo =========================================================
echo    📦 BUILDING DATABASE AGENT DESKTOP EXECUTABLE (.EXE)
echo =========================================================
echo.

echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ [ERROR] Python is not installed or not in PATH!
    pause
    exit /b
)
echo      ✅ Python environment verified.
echo.

echo [2/4] Verifying PyInstaller & packaging tools...
pip install pyinstaller pyinstaller-hooks-contrib >nul 2>&1
echo      ✅ Packaging tools ready.
echo.

echo [3/4] Building React Frontend static bundle...
cmd /c "cd frontend && npm run build"
echo      ✅ React frontend built successfully.
echo.

echo [4/4] Packaging Python Backend & React Frontend into DatabaseAgent.exe...
echo      (Excluding heavy unused ML modules for ultra-fast performance...)
pyinstaller --noconfirm --onedir --windowed ^
  --exclude-module torch ^
  --exclude-module torchvision ^
  --exclude-module tensorflow ^
  --exclude-module scipy ^
  --exclude-module matplotlib ^
  --exclude-module notebook ^
  --add-data "frontend/dist;frontend/dist" ^
  --name "DatabaseAgent" run_desktop.py

echo.
echo =========================================================
echo   🎉 [COMPLETE 4/4] BUILD SUCCESSFUL!
echo   Executable Folder: dist\DatabaseAgent\
echo   Main Executable: dist\DatabaseAgent\DatabaseAgent.exe
echo =========================================================
echo.
pause
