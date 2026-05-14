# WeekNumber

A minimal Windows system tray app that shows the current ISO week number as the tray icon.

## What it does

- Sits in the system tray and displays the current **week number** directly as the icon (e.g. `11`)
- Hover tooltip shows full date info:
  ```
  13/03/2026
  Day 72 of year
  Week 11 of year
  ```
- **Right-click** → see the full date and quit
- Icon updates automatically at midnight when the day changes

## Requirements

- Windows 10 / 11

## Install (end users)

Run `dist\WeekNumberSetup.exe`. The wizard offers an optional
"start automatically when Windows starts" task (checked by default) and a
desktop-shortcut task (off by default). Auto-start can be toggled later from
the tray icon's right-click menu (**Windows başladığında başlat**).

## Run (from source — dev)

```bash
pip install -r requirements.txt
pythonw week_number.py
```

## Build EXE

```bat
build.bat
```

Produces `dist\WeekNumber.exe` via PyInstaller with the admin manifest
embedded (`--uac-admin`).

## Build Installer

1. Run `build.bat` to produce `dist\WeekNumber.exe`.
2. Open `installer.iss` in Inno Setup Compiler (or run `iscc installer.iss`).
3. Output: `dist\WeekNumberSetup.exe`.

## Configuration

The auto-start preference is stored at
`%APPDATA%\WeekNumber\config.json`.
