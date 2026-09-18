@echo off
setlocal

REM ----------------------------------------------------------------------
REM Build WeekNumber.exe.
REM
REM No administrator manifest: this app reads the date and draws a calendar.
REM It used to ask for one, and that was not free -- an admin-manifested exe
REM in the Startup folder prompts at every logon on a standard account, which
REM makes the auto-start it ships with unusable.
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
py -m pip install -r requirements-dev.txt

echo.
echo === Running tests ===
REM A build that ships a broken app is worse than one that does not ship.
py -m pytest tests -q
if errorlevel 1 (
    echo [ERROR] Tests failed. Not building.
    exit /b 1
)

echo.
echo === Cleaning previous build ===
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
if exist WeekNumber.spec del WeekNumber.spec

echo.
echo === Stamping the build ===
REM Bakes the commit and the build date into version.py, writes the version
REM resource for the exe, and refuses to go on if version.py and installer.iss
REM disagree about the release.
py stamp_version.py
if errorlevel 1 (
    echo [ERROR] Version check failed. Not building.
    exit /b 1
)

echo.
echo === Building WeekNumber.exe ===
py -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --windowed ^
    --name WeekNumber ^
    --icon=app_icon.ico ^
    --version-file=version_info.txt ^
    --hidden-import=win32com ^
    --hidden-import=win32com.client ^
    --hidden-import=pywintypes ^
    --collect-submodules translations ^
    week_number.py

set BUILD_FAILED=
if errorlevel 1 set BUILD_FAILED=1

REM Always, and before anything can exit: the stamp is baked into the exe by
REM now, and a build that failed must not leave the working tree edited either.
py stamp_version.py --restore

if defined BUILD_FAILED (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

echo.
echo Build OK -^> dist\WeekNumber\WeekNumber.exe
endlocal
