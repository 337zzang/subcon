@echo off
chcp 65001 > nul
echo ========================================
echo   매입대사 시스템 v2.0 실행
echo ========================================
echo.

REM Python 경로 설정
set PYTHON_PATH=

REM Miniconda 경로 확인
if exist "C:\Users\Administrator\miniconda3\python.exe" (
    set PYTHON_PATH=C:\Users\Administrator\miniconda3\python.exe
    echo ✓ Miniconda Python 발견
    goto :run_app
)

REM Anaconda 경로 확인
if exist "C:\Users\Administrator\anaconda3\python.exe" (
    set PYTHON_PATH=C:\Users\Administrator\anaconda3\python.exe
    echo ✓ Anaconda Python 발견
    goto :run_app
)

REM 일반 Python 경로 확인
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_PATH=python
    echo ✓ 시스템 Python 발견
    goto :run_app
)

REM Python을 찾을 수 없음
echo [오류] Python을 찾을 수 없습니다.
echo Python을 설치하거나 PATH를 설정해주세요.
pause
exit /b 1

:run_app
echo.
echo Python 경로: %PYTHON_PATH%
echo.
echo 프로그램을 시작합니다...
echo.

REM Python 실행
"%PYTHON_PATH%" run_app.py

if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행 중 문제가 발생했습니다.
    echo.
    echo 다음 명령으로 필요한 패키지를 설치해주세요:
    echo "%PYTHON_PATH%" -m pip install -r requirements.txt
    echo.
    pause
) else (
    echo.
    echo 프로그램이 정상적으로 종료되었습니다.
    timeout /t 3
)