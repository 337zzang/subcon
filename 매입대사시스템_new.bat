@echo off
chcp 65001 > nul
title 협력사 매입대사 시스템

echo =====================================
echo   협력사 매입대사 시스템 실행
echo =====================================

REM Python 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo Python을 먼저 설치해주세요.
    pause
    exit /b 1
)

echo ✅ Python 확인 완료

REM 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    echo 📦 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ℹ️ 가상환경이 없습니다. 전역 Python을 사용합니다.
)

REM 필요한 패키지 확인
echo 📦 필요한 패키지 확인 중...
python -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 필요한 패키지가 설치되어 있지 않습니다.
    echo.
    echo 다음 명령어로 설치하세요:
    echo pip install -r requirements.txt
    echo.
    echo 또는 install_packages.bat를 실행하세요.
    pause
    exit /b 1
)

echo ✅ 모든 패키지가 설치되어 있습니다.
echo.
echo 🚀 프로그램을 시작합니다...
echo =====================================
echo.

REM 프로그램 실행
python run.py

REM 실행 완료
echo.
echo =====================================
echo   프로그램이 종료되었습니다.
echo =====================================
pause
