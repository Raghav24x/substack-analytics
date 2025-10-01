@echo off
echo Installing Substack Analytics Dashboard...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM Install requirements
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo.
echo To run the dashboard:
echo 1. Open Command Prompt or PowerShell
echo 2. Navigate to this directory: cd %~dp0
echo 3. Run: python main.py
echo 4. Open your browser and go to: http://localhost:5000
echo.
pause
