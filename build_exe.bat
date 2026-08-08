@echo off
title Build DatabaseAgent.exe Desktop App
color 0A
echo =========================================================
echo    📦 BUILDING DATABASE AGENT DESKTOP EXECUTABLE (.EXE)
echo =========================================================
echo.

echo [1/3] Installing PyInstaller...
pip install pyinstaller pyinstaller-hooks-contrib

echo [2/3] Building React Frontend static bundle...
cmd /c "cd frontend && npm run build"

echo [3/3] Packaging Python Backend & React Frontend into DatabaseAgent.exe...
pyinstaller --noconfirm --onedir --windowed --add-data "frontend/dist;frontend/dist" --name "DatabaseAgent" run_desktop.py

echo.
echo =========================================================
echo   ✅ BUILD COMPLETE! 
echo   Executable Folder: dist\DatabaseAgent\
echo   Main Executable: dist\DatabaseAgent\DatabaseAgent.exe
echo =========================================================
echo.
pause
