@echo off
echo ========================================
echo   매입대사 시스템 v2.0 실행
echo ========================================
echo.

REM Python 실행
python src/main.py

if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행 중 문제가 발생했습니다.
    echo 다음 사항을 확인해주세요:
    echo 1. Python이 설치되어 있는지
    echo 2. 필요한 패키지가 설치되어 있는지 (pip install -r requirements.txt)
    echo.
    pause
) else (
    echo.
    echo 프로그램이 정상적으로 종료되었습니다.
    timeout /t 3
)
