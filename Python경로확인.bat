@echo off
chcp 65001 > nul
title Python 경로 확인 도우미

echo =====================================
echo   Python 설치 경로 확인
echo =====================================
echo.

echo 🔍 Python 찾기 시도 중...
echo.

:: 다양한 방법으로 Python 찾기
echo [python 명령어 확인]
where python 2>nul
if %errorlevel%==0 (
    echo ✅ python 명령어 사용 가능
    python --version
) else (
    echo ❌ python 명령어 없음
)
echo.

echo [python3 명령어 확인]
where python3 2>nul
if %errorlevel%==0 (
    echo ✅ python3 명령어 사용 가능
    python3 --version
) else (
    echo ❌ python3 명령어 없음
)
echo.

echo [py 런처 확인]
where py 2>nul
if %errorlevel%==0 (
    echo ✅ py 런처 사용 가능
    py --version
) else (
    echo ❌ py 런처 없음
)
echo.

echo [일반적인 설치 경로 확인]
if exist "C:\Python312\python.exe" echo ✅ C:\Python312\python.exe 발견
if exist "C:\Python311\python.exe" echo ✅ C:\Python311\python.exe 발견
if exist "C:\Python310\python.exe" echo ✅ C:\Python310\python.exe 발견
if exist "C:\Python39\python.exe" echo ✅ C:\Python39\python.exe 발견
if exist "%ProgramFiles%\Python312\python.exe" echo ✅ %ProgramFiles%\Python312\python.exe 발견
if exist "%ProgramFiles%\Python311\python.exe" echo ✅ %ProgramFiles%\Python311\python.exe 발견
echo.

echo [Anaconda/Miniconda 확인]
if exist "%USERPROFILE%\anaconda3\python.exe" echo ✅ %USERPROFILE%\anaconda3\python.exe 발견
if exist "%USERPROFILE%\miniconda3\python.exe" echo ✅ %USERPROFILE%\miniconda3\python.exe 발견
if exist "%ProgramData%\Anaconda3\python.exe" echo ✅ %ProgramData%\Anaconda3\python.exe 발견
if exist "%ProgramData%\Miniconda3\python.exe" echo ✅ %ProgramData%\Miniconda3\python.exe 발견
echo.

echo [환경 변수 PATH 확인]
echo %PATH%
echo.

echo =====================================
echo 위에서 발견된 Python 경로가 있다면,
echo 해당 경로를 사용하여 프로그램을 실행할 수 있습니다.
echo =====================================
echo.
pause
