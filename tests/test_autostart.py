"""The Startup-folder shortcut.

Every test here runs against a temporary Startup directory — see
`conftest.elsewhere`. Nothing in this file may touch the real one: turning the
user's auto-start off by running the suite is exactly the accident the
redirection exists to prevent.
"""

from pathlib import Path

import autostart


def a_target(tmp_path):
    """A stand-in for the built exe. `enable` refuses to write a shortcut to
    something that is not there, so the tests need a file to point at."""
    exe = tmp_path / "WeekNumber.exe"
    exe.write_bytes(b"MZ")
    return exe


def test_nothing_is_enabled_to_begin_with():
    assert autostart.is_enabled() is False


def test_enabling_writes_a_shortcut(tmp_path, monkeypatch):
    monkeypatch.setattr(autostart, "_target_exe", lambda: str(a_target(tmp_path)))

    autostart.enable()

    assert autostart.is_enabled() is True
    assert Path(autostart._shortcut_path()).name == "WeekNumber.lnk"


def test_disabling_takes_it_away(tmp_path, monkeypatch):
    monkeypatch.setattr(autostart, "_target_exe", lambda: str(a_target(tmp_path)))
    autostart.enable()

    autostart.disable()

    assert autostart.is_enabled() is False


def test_disabling_what_is_not_there_is_not_an_error():
    autostart.disable()
    assert autostart.is_enabled() is False


def test_apply_goes_both_ways(tmp_path, monkeypatch):
    monkeypatch.setattr(autostart, "_target_exe", lambda: str(a_target(tmp_path)))

    autostart.apply(True)
    assert autostart.is_enabled() is True

    autostart.apply(False)
    assert autostart.is_enabled() is False


def test_a_missing_target_writes_nothing(tmp_path, monkeypatch):
    """Running from source with no exe built yet. A shortcut to a file that
    does not exist is worse than no shortcut: it survives, it is silent, and
    it fails at logon."""
    monkeypatch.setattr(autostart, "_target_exe",
                        lambda: str(tmp_path / "not-built-yet.exe"))

    autostart.enable()

    assert autostart.is_enabled() is False


def test_the_shortcut_points_at_the_exe(tmp_path, monkeypatch):
    exe = a_target(tmp_path)
    monkeypatch.setattr(autostart, "_target_exe", lambda: str(exe))
    autostart.enable()

    from win32com.client import Dispatch
    shortcut = Dispatch("WScript.Shell").CreateShortCut(autostart._shortcut_path())

    assert Path(shortcut.TargetPath) == exe
    # Minimised: this is a tray app, and a console window flashing up at every
    # logon is what WindowStyle is for.
    assert shortcut.WindowStyle == 7
