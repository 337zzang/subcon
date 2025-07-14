@echo off
chcp 65001 > nul
echo.
echo ========================================
echo    매입대사 시스템 v2.0
echo ========================================
echo.

:: Python 실행
python run.py

if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행 중 오류가 발생했습니다.
    echo.
    echo Python이 설치되어 있는지 확인해주세요.
    echo 필요한 패키지 설치: pip install -r requirements.txt
    echo.
    pause
) else (
    echo.
    echo 프로그램이 정상적으로 종료되었습니다.
    timeout /t 3 > nul
)
