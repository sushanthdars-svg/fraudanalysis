@echo off
REM Dashboard startup script for Windows

setlocal enabledelayedexpansion

echo.
echo === Fraud Detection Dashboard ===
echo.

REM Check if .env.dashboard exists
if not exist .env.dashboard (
    echo Warning: .env.dashboard not found
    echo Creating from template...
    copy .env.dashboard.template .env.dashboard
    echo Created .env.dashboard - please edit with your settings
    echo.
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Check if Streamlit is installed
python -m pip list | findstr /i streamlit >nul
if errorlevel 1 (
    echo Error: Dependencies not installed
    echo Run: pip install -r requirements-dashboard.txt
    exit /b 1
)

echo Dependencies installed
echo.

REM Check backend connectivity (optional, using PowerShell)
echo Checking backend connectivity...
for /f "tokens=*" %%i in (.env.dashboard) do (
    if "%%i:~0,15%"=="API_BASE_URL=" (
        set "API_URL=%%i:~15%"
    )
)

echo Starting dashboard...
echo Dashboard will be available at: http://localhost:8501
echo.
echo To stop the dashboard, press Ctrl+C
echo.

REM Start Streamlit
streamlit run dashboard/app.py --logger.level=info

endlocal
