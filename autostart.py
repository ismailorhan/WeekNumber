"""
Manage the WeekNumber auto-start shortcut in the user's Startup folder.
"""
import os
import sys

SHORTCUT_NAME = "WeekNumber.lnk"


def _startup_dir() -> str:
    return os.path.join(
        os.environ["APPDATA"],
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
    )


def _shortcut_path() -> str:
    return os.path.join(_startup_dir(), SHORTCUT_NAME)


def _target_exe() -> str:
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "WeekNumber.exe")


def is_enabled() -> bool:
    return os.path.exists(_shortcut_path())


def enable() -> None:
    target = _target_exe()
    if not os.path.exists(target):
        return

    os.makedirs(_startup_dir(), exist_ok=True)

    from win32com.client import Dispatch  # type: ignore

    shell = Dispatch("WScript.Shell")
    sc = shell.CreateShortCut(_shortcut_path())
    sc.TargetPath = target
    sc.WorkingDirectory = os.path.dirname(target)
    sc.IconLocation = target
    sc.Description = "WeekNumber — ISO week number in the system tray"
    sc.WindowStyle = 7
    sc.Save()


def disable() -> None:
    path = _shortcut_path()
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def apply(enabled: bool) -> None:
    if enabled:
        enable()
    else:
        disable()
