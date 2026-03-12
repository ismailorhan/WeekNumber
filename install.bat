@echo off
echo WeekNumber Installer
echo ====================
echo.

REM Check for Python via the Python Launcher (py), which is installed by default
REM with the python.org installer and is more reliable than checking "python" in PATH.
py --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found on this machine.
    echo.
    echo Please install Python 3.x from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: On the installer's first screen, check the box that says
    echo   "Add Python to PATH" before clicking Install Now.
    echo.
    echo After installing Python, run this installer again.
    echo.
    pause
    exit /b 1
)

echo Python found:
py --version
echo.

REM Install dependencies
echo Installing dependencies...
py -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)
echo.

REM Write a small VBScript that launches run.bat silently (no console window)
set "VBS=%~dp0start_hidden.vbs"
(
    echo Set sh = CreateObject("WScript.Shell"^)
    echo sh.Run """" ^& WScript.Arguments(0^) ^& """", 0, False
) > "%VBS%"

REM Register in Windows Startup folder
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "STARTUP_VBS=%STARTUP%\WeekNumber.vbs"
set "RUN_BAT=%~dp0run.bat"

REM Write the startup launcher directly (hardcoded path to run.bat)
(
    echo Set sh = CreateObject("WScript.Shell"^)
    echo sh.Run """%RUN_BAT%""", 0, False
) > "%STARTUP_VBS%"

echo WeekNumber will now start automatically on every login.
echo.
echo Starting WeekNumber now...
wscript "%VBS%" "%RUN_BAT%"
echo.
echo Done! Look for the week number icon in your system tray.
pause
