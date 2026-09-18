r"""Make the project importable, and keep every test off the real machine.

The app writes two things outside itself: `%APPDATA%\WeekNumber\config.json`
and a shortcut in the user's Startup folder. Both are redirected for every
test, without the tests asking, because a suite that can turn the user's
auto-start off by being run is worse than no suite.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def elsewhere(tmp_path, monkeypatch):
    """Point both of those somewhere disposable, for every test."""
    monkeypatch.setenv("APPDATA", str(tmp_path))

    import autostart
    startup = tmp_path / "Startup"
    monkeypatch.setattr(autostart, "_startup_dir", lambda: str(startup))
    return tmp_path
