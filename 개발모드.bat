@echo off
chcp 65001 > nul
title 협력사 매입대사 시스템 - 개발 모드

echo =====================================
echo   개발 모드 실행 (콘솔 표시)
echo =====================================
echo.

:: 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: 환경 정보 표시
echo Python 버전:
python --version
echo.
echo 설치된 패키지:
pip list | findstr /i "pyqt6 pandas openpyxl"
echo.

:: 프로그램 실행 (콘솔 유지)
echo 🚀 프로그램 시작...
echo =====================================
echo.
python src/main.py

echo.
echo 프로그램이 종료되었습니다.
pause
