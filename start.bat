@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   Ops Digital Employee - Startup Script
echo ============================================
echo.

REM --- Get project root ---
set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%venv"

REM --- Check Python ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python detected

REM --- Create/activate venv ---
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [STEP] Creating virtual environment...
    python -m venv "%VENV_DIR%"
)
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate venv
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM --- Check Ollama ---
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Ollama not found in PATH. Please make sure it is installed and running.
    echo       Download: https://ollama.com/download
)

echo [STEP] Checking Ollama service...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo [STEP] Starting Ollama service...
    start "Ollama" ollama serve
    echo [WAIT] Waiting for Ollama to be ready...
    timeout /t 5 /nobreak >nul
)
echo [OK] Ollama service running

REM --- Pull models (idempotent: skips if already downloaded) ---
echo [STEP] Pulling qwen2.5:7b (~4.5GB, first time only)...
ollama pull qwen2.5:7b

echo [STEP] Pulling nomic-embed-text (~274MB)...
ollama pull nomic-embed-text

echo [OK] Models ready

REM --- Install dependencies ---
echo [STEP] Installing Python dependencies...
cd /d "%PROJECT_DIR%backend"
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM --- Start backend ---
echo.
echo ============================================
echo   Starting backend server...
echo   API docs:  http://localhost:8000/docs
echo   Frontend:  http://localhost:8000
echo   Login:     admin / Admin@123456
echo ============================================
echo.

start "Backend" cmd /c "call ""%VENV_DIR%\Scripts\activate.bat"" && python main.py"
timeout /t 3 /nobreak >nul

echo.
echo [Optional] Start frontend dev server:
echo   cd frontend
echo   npm install
echo   npm run dev
echo   http://localhost:5173
echo.
echo ============================================
echo   Done! Press any key to exit...
echo ============================================
pause
