@echo off
chcp 65001 > nul
title 협력사 매입대사 시스템

echo =====================================
echo   협력사 매입대사 시스템 실행
echo =====================================
echo.

:: Python 실행 파일 찾기
set PYTHON_CMD=
set PYTHON_FOUND=0

:: 1. python 명령어 확인
where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=1
    goto :python_found
)

:: 2. python3 명령어 확인
where python3 >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3
    set PYTHON_FOUND=1
    goto :python_found
)

:: 3. py 런처 확인
where py >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    set PYTHON_FOUND=1
    goto :python_found
)

:: 4. 일반적인 Python 설치 경로 확인
if exist "C:\Python312\python.exe" (
    set PYTHON_CMD="C:\Python312\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

if exist "C:\Python311\python.exe" (
    set PYTHON_CMD="C:\Python311\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

if exist "C:\Python310\python.exe" (
    set PYTHON_CMD="C:\Python310\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

if exist "C:\Python39\python.exe" (
    set PYTHON_CMD="C:\Python39\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

:: 5. Program Files 경로 확인
if exist "%ProgramFiles%\Python312\python.exe" (
    set PYTHON_CMD="%ProgramFiles%\Python312\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

if exist "%ProgramFiles%\Python311\python.exe" (
    set PYTHON_CMD="%ProgramFiles%\Python311\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

:: 6. Anaconda/Miniconda 확인
if exist "%USERPROFILE%\anaconda3\python.exe" (
    set PYTHON_CMD="%USERPROFILE%\anaconda3\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

if exist "%USERPROFILE%\miniconda3\python.exe" (
    set PYTHON_CMD="%USERPROFILE%\miniconda3\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

if exist "%ProgramData%\Anaconda3\python.exe" (
    set PYTHON_CMD="%ProgramData%\Anaconda3\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

if exist "%ProgramData%\Miniconda3\python.exe" (
    set PYTHON_CMD="%ProgramData%\Miniconda3\python.exe"
    set PYTHON_FOUND=1
    goto :python_found
)

:: Python을 찾지 못한 경우
if %PYTHON_FOUND%==0 (
    echo ❌ Python을 찾을 수 없습니다.
    echo.
    echo Python이 설치되어 있다면 다음 중 하나를 시도해보세요:
    echo.
    echo 1. Windows 명령 프롬프트에서 다음 명령어 실행:
    echo    python --version
    echo    또는
    echo    python3 --version
    echo    또는
    echo    py --version
    echo.
    echo 2. 위 명령어 중 작동하는 것이 있다면,
    echo    이 배치 파일을 메모장으로 열어서
    echo    "set PYTHON_CMD=python" 부분을
    echo    작동하는 명령어로 수정하세요.
    echo.
    echo 3. Python이 설치되어 있지 않다면:
    echo    https://www.python.org/downloads/
    echo.
    echo 4. Anaconda를 사용 중이라면:
    echo    Anaconda Prompt에서 이 배치 파일을 실행하세요.
    echo.
    pause
    exit /b 1
)

:python_found
echo ✅ Python 확인 완료
echo    사용 중인 Python: %PYTHON_CMD%
%PYTHON_CMD% --version
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
%PYTHON_CMD% -c "import PyQt6" >nul 2>&1
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
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 패키지 설치 실패
    echo pip가 설치되어 있지 않을 수 있습니다.
    echo 다음 명령어를 시도합니다:
    %PYTHON_CMD% -m ensurepip --default-pip
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo 여전히 실패했습니다. 수동으로 설치해주세요.
        pause
        exit /b 1
    )
)

:skip_install
:run_program
echo.
echo 🚀 프로그램을 시작합니다...
echo =====================================
echo.

:: 프로그램 실행
%PYTHON_CMD% run.py

:: 오류 발생 시 일시정지
if errorlevel 1 (
    echo.
    echo ❌ 프로그램 실행 중 오류가 발생했습니다.
    echo.
    echo 다음을 확인해주세요:
    echo 1. data 폴더에 필요한 엑셀 파일이 있는지
    echo 2. 필요한 패키지가 모두 설치되어 있는지
    echo.
    echo 자세한 오류 내용은 위를 확인하세요.
    pause
)
