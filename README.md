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

## Run (from source)

```bash
pip install -r requirements.txt
pythonw week_number.py
```

## Build EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name WeekNumber --icon=app_icon.ico week_number.py
```

Output: `dist\WeekNumber.exe` — no installation needed, runs standalone.
