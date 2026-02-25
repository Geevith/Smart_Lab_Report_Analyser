@echo off
echo Starting Smart Lab Report Analyser...
echo.

:: Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

:: Run the application
echo.
echo Server running at http://localhost:8000
echo Press Ctrl+C to stop.
echo.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
pause
