@echo off
echo Starting Subcontract Reconciliation System...
echo.

cd /d "%~dp0"

REM Run the application
"C:\Users\Administrator\miniconda3\python.exe" launch_app.py

if errorlevel 1 (
    echo.
    echo [ERROR] An error occurred while running the program.
    pause
)
