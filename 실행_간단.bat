@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo 협력사 매입대사 시스템 실행 중...
echo.

:: 다양한 Python 명령어 시도
python run.py 2>nul || python3 run.py 2>nul || py run.py 2>nul || (
    echo Python을 찾을 수 없습니다.
    echo.
    echo 다음 방법을 시도해보세요:
    echo 1. Python경로확인.bat 실행
    echo 2. 명령 프롬프트에서 직접 실행:
    echo    python run.py
    pause
)
