@echo off
chcp 65001 > nul
title 협력사 매입대사 시스템 - 설치

echo =====================================
echo   협력사 매입대사 시스템 설치
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
python --version
echo.

:: 가상환경 생성 옵션
echo 가상환경을 생성하시겠습니까? (권장)
echo 1. 예 - 가상환경 생성 및 패키지 설치
echo 2. 아니오 - 전역 환경에 패키지 설치
echo.
choice /c 12 /n /m "선택하세요 (1 또는 2): "

if errorlevel 2 goto :global_install
if errorlevel 1 goto :venv_install

:venv_install
echo.
echo 🔧 가상환경 생성 중...
python -m venv venv
if errorlevel 1 (
    echo ❌ 가상환경 생성 실패
    pause
    exit /b 1
)

echo 🔄 가상환경 활성화 중...
call venv\Scripts\activate.bat

:global_install
echo.
echo 📦 필요한 패키지 설치 중...
echo =====================================
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ 패키지 설치 실패
    pause
    exit /b 1
)

echo.
echo =====================================
echo ✅ 설치가 완료되었습니다!
echo.
echo 프로그램을 실행하려면 "매입대사시스템.bat"을 실행하세요.
echo =====================================
echo.
pause
