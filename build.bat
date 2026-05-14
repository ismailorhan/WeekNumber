@echo off
setlocal

REM ----------------------------------------------------------------------
REM Build WeekNumber.exe with the requireAdministrator manifest baked in.
REM ----------------------------------------------------------------------

cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher 'py' not found. Install Python 3.10+ first.
    exit /b 1
)

echo.
echo === Installing build dependencies ===
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m pip install pyinstaller

echo.
echo === Cleaning previous build ===
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
if exist WeekNumber.spec del WeekNumber.spec

echo.
echo === Building WeekNumber.exe ===
py -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --name WeekNumber ^
    --icon=app_icon.ico ^
    --hidden-import=win32com ^
    --hidden-import=win32com.client ^
    --hidden-import=pywintypes ^
    week_number.py

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

echo.
echo Build OK -^> dist\WeekNumber.exe
endlocal
