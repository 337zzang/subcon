@echo off
REM 매입대사 시스템 실행 스크립트
cd /d "%~dp0"
echo 매입대사 시스템을 시작합니다...
cd src
python main.py
pause
