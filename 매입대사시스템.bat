@echo off
chcp 65001 > nul
title 협력사 매입대사 시스템

echo =====================================
echo   협력사 매입대사 시스템 실행
echo =====================================
echo.

:: Python 설치 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo Python을 먼저 설치해주세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python 확인 완료
echo.

:: 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo 🔄 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ℹ️ 가상환경이 없습니다. 전역 Python을 사용합니다.
)

:: 필요한 패키지 확인
echo 📦 필요한 패키지 확인 중...
python -c "import PyQt6" > nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️ 필요한 패키지가 설치되어 있지 않습니다.
    echo 설치를 진행하시겠습니까? (Y/N)
    choice /c YN /n
    if errorlevel 2 goto :skip_install
    if errorlevel 1 goto :install_packages
)

goto :run_program

:install_packages
echo.
echo 📥 패키지 설치 중... (시간이 걸릴 수 있습니다)
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 패키지 설치 실패
    pause
    exit /b 1
)

:skip_install
:run_program
echo.
echo 🚀 프로그램을 시작합니다...
echo =====================================
echo.

:: 프로그램 실행
python run.py

:: 오류 발생 시 일시정지
if errorlevel 1 (
    echo.
    echo ❌ 프로그램 실행 중 오류가 발생했습니다.
    pause
)
