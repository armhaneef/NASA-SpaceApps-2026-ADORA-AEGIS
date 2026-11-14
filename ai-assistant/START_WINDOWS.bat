@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found in PATH.
    echo Install Python 3.11 or later from https://www.python.org/downloads/windows/
    echo Then re-run this script.
    exit /b 1
)

if not exist ".venv" (
    echo Creating Python virtual environment in .venv...
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Starting ADORA AEGIS AI assistant...
echo Local API: http://127.0.0.1:8001/docs
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
