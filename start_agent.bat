@echo off
title Database AI Agent Launcher
color 0A
echo =========================================================
echo       🚀 UNIVERSAL DATABASE AI AGENT LAUNCHER
echo =========================================================
echo.
echo [1/3] Checking Python & Node environments...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.10+ from https://python.org
    pause
    exit /b
)

echo [2/3] Installing Python & Node dependencies (if needed)...
pip install -r requirements.txt
cmd /c "cd frontend && npm install"

echo.
echo [3/3] Starting Backend API (Port 8000) & Frontend Web App (Port 5173)...
echo.
start /B python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
start /B cmd /c "cd frontend && npm run dev"

echo =========================================================
echo   ✅ Universal Database AI Agent is now Running!
echo   🌐 Web Interface: http://localhost:5173
echo   (Keep this terminal window open while using the app)
echo =========================================================
echo.
timeout /t 3 >nul
start http://localhost:5173
echo Press Ctrl+C or close this window to stop the agent.
cmd /k
