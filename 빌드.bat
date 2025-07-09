@echo off
chcp 65001 > nul
title 협력사 매입대사 시스템 - 빌드

echo =====================================
echo   실행 파일(.exe) 생성
echo =====================================
echo.

:: 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo 🔄 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

:: PyInstaller 설치 확인
python -c "import PyInstaller" > nul 2>&1
if errorlevel 1 (
    echo ⚠️ PyInstaller가 설치되어 있지 않습니다.
    echo 설치를 진행합니다...
    pip install pyinstaller
)

echo.
echo 🔨 실행 파일 빌드 중... (시간이 걸립니다)
echo =====================================

:: 빌드 실행
python build\build_exe.py

if errorlevel 1 (
    echo.
    echo ❌ 빌드 실패
    pause
    exit /b 1
)

echo.
echo =====================================
echo ✅ 빌드 완료!
echo.
echo 생성된 파일: dist\SubConSystem.exe
echo =====================================
echo.

:: 결과 폴더 열기
echo 결과 폴더를 여시겠습니까? (Y/N)
choice /c YN /n
if errorlevel 1 (
    start dist
)

pause
