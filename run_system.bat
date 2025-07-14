@echo off
chcp 65001 > nul
echo ========================================
echo   Purchase Reconciliation System v2.0
echo ========================================
echo.

REM Python path configuration
set PYTHON_PATH=

REM Check Miniconda path
if exist "C:\Users\Administrator\miniconda3\python.exe" (
    set PYTHON_PATH=C:\Users\Administrator\miniconda3\python.exe
    echo [OK] Miniconda Python found
    goto :run_app
)

REM Check Anaconda path
if exist "C:\Users\Administrator\anaconda3\python.exe" (
    set PYTHON_PATH=C:\Users\Administrator\anaconda3\python.exe
    echo [OK] Anaconda Python found
    goto :run_app
)

REM Check system Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_PATH=python
    echo [OK] System Python found
    goto :run_app
)

REM Python not found
echo [ERROR] Python not found.
echo Please install Python or configure PATH environment.
pause
exit /b 1

:run_app
echo.
echo Python path: %PYTHON_PATH%
echo.
echo Starting application...
echo.

REM Execute Python
"%PYTHON_PATH%" run_app.py

if errorlevel 1 (
    echo.
    echo [ERROR] An error occurred while running the program.
    echo.
    echo Please install required packages with:
    echo "%PYTHON_PATH%" -m pip install -r requirements.txt
    echo.
    pause
) else (
    echo.
    echo Program terminated successfully.
    timeout /t 3
)