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
- **Right-click** → the date, the auto-start toggle, the **Language** submenu
  (English / Türkçe), the build it is, and Quit. The date line is asked for
  each time the menu opens, so a machine left on overnight does not open it
  on yesterday
- **Left-click** → a calendar with the week numbers down the side. Click any
  day and the footer says what week it is, where it falls in the year, and
  which dates that week covers; click the footer to copy the line
- Icon updates automatically at midnight when the day changes

The icon carries no background of its own. Windows draws it at 16px on the
taskbar, and an opaque square is a dark blob on a light taskbar and a light
one on a dark taskbar — so the number is drawn on nothing, in whichever colour
`SystemUsesLightTheme` calls for, filling the square rather than sitting in a
box inside it.

## Languages

English and Türkçe, from the tray menu, remembered between sessions. The
English sentence is the translation key (`t("Quit")`, not `t("menu.quit")`),
so a sentence with no entry falls back to the English rather than showing a
key to a person — and `tests/test_language.py` reads every `t(...)` out of the
source and fails if the Turkish catalogue has missed one or kept one the code
no longer says.

Month and weekday names come from a table, not `strftime`: `strftime` answers
in the machine's locale, which is a different question from the language
somebody picked in the menu.

## Requirements

- Windows 10 / 11

## Install (end users)

Run `dist\WeekNumberSetup.exe`. The wizard offers one optional task —
**Create a desktop shortcut**, off by default.

**Auto-start is set from the app**, not the installer: the tray icon's
right-click menu has **Windows başladığında başlat**. It used to be an
installer task, and that was wrong — the installer runs as administrator, so
on a machine where a standard user starts the install and types an
administrator's password, the shortcut landed in a Startup folder that person
never signs into. The app writes it while running as whoever ticked it, which
is the only context in which "the user's Startup folder" means anything.

## Run (from source — dev)

```bash
pip install -r requirements.txt
pythonw week_number.py
```

## Build EXE

```bat
build.bat
```

Produces `dist\WeekNumber\WeekNumber.exe` via PyInstaller. It runs the tests
first and refuses to build if they fail, then stamps the build.

**One-dir, not one-file.** Measured: the one-file bootloader spent 864–1119 ms
unpacking 19 MB to a temp directory before Python even started — at every
launch, and this app starts at every logon. Inno Setup packages the whole
directory anyway.

**No administrator manifest.** The app reads the date and draws a calendar;
nothing it does needs elevation, and asking for it was not free — an
admin-manifested exe in the Startup folder prompts at every logon on a
standard account, which makes the auto-start it ships with unusable. The
*installer* still needs administrator, because it writes into Program Files.
That is a different question.

## Build Installer

1. Run `build.bat` to produce `dist\WeekNumber\` (a directory build).
2. Open `installer.iss` in Inno Setup Compiler (or run `iscc installer.iss`).
3. Output: `dist\WeekNumberSetup.exe`.

## Tests

```bash
python -m pytest
```

80 of them, and they never touch the real machine: `tests/conftest.py`
redirects `%APPDATA%` and the Startup folder for every test, because a suite
that can turn the user's own auto-start off by being run is worse than no
suite.

## Versions

The release number is typed in exactly two places — `version.py` and
`installer.iss` — and `stamp_version.py` fails the build if they disagree, or
if either disagrees with the git tag on a release build. Before this existed,
`installer.iss` was the only copy and said `1.0.0` from the first commit to
the last.

A build also bakes in the commit, the date and a build counter, so two builds
of one release can be told apart; a build from a tree with edits says
`-dirty`. The tray menu shows all of it, and the same numbers go into the
exe's own version resource, so the Details tab of its Properties and
`Get-Process` agree with the menu.

Pushing a `v*` tag builds the exe and the installer and publishes a GitHub
Release. Running the workflow by hand does everything except publish, which
makes a manual run a check that the build is healthy.

## Configuration

The auto-start preference and the chosen language are stored at
`%APPDATA%\WeekNumber\config.json`. Every read of it falls back and every
write is allowed to fail: a roaming profile is somewhere a JSON file genuinely
turns up half-written, and a tray app that cannot read its settings still has
to start.
