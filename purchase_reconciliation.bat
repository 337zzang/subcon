@echo off
chcp 65001 > nul
echo.
echo ========================================
echo    Purchase Reconciliation System v2.0
echo ========================================
echo.

:: Execute Python
python run.py

if errorlevel 1 (
    echo.
    echo [ERROR] An error occurred while running the program.
    echo.
    echo Please check if Python is installed.
    echo Install required packages: pip install -r requirements.txt
    echo.
    pause
) else (
    echo.
    echo Program terminated successfully.
    timeout /t 3 > nul
)