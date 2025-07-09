@echo off
chcp 65001 > nul
title 협력사 매입대사 시스템 (Anaconda)

echo =====================================
echo   협력사 매입대사 시스템 실행
echo   (Anaconda/Miniconda 사용자용)
echo =====================================
echo.

:: Anaconda 환경 활성화 시도
set CONDA_FOUND=0

:: conda 명령어 확인
where conda >nul 2>&1
if %errorlevel%==0 (
    set CONDA_FOUND=1
    echo ✅ Conda 환경 감지됨
    call conda activate base
    goto :run_program
)

:: Anaconda 경로 직접 확인
if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    set CONDA_FOUND=1
    echo ✅ Anaconda3 발견
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat"
    goto :run_program
)

if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    set CONDA_FOUND=1
    echo ✅ Miniconda3 발견
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
    goto :run_program
)

if %CONDA_FOUND%==0 (
    echo ❌ Anaconda/Miniconda를 찾을 수 없습니다.
    echo.
    echo Anaconda Prompt에서 이 파일을 실행하거나
    echo 일반 Python용 "매입대사시스템.bat"을 사용하세요.
    pause
    exit /b 1
)

:run_program
echo.
echo Python 버전:
python --version
echo.
echo 🚀 프로그램을 시작합니다...
echo =====================================
echo.

python run.py

if errorlevel 1 (
    echo.
    echo ❌ 프로그램 실행 중 오류가 발생했습니다.
    pause
)
