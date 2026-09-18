r"""The one setting, kept in `%APPDATA%\WeekNumber\config.json`.

The care here is not about the setting — it is about the file. A roaming
profile is somewhere a JSON file genuinely turns up half-written, unreadable,
or on a share that has gone away, and a tray app that cannot read its settings
still has to start.

So every read falls back and every write is allowed to fail quietly. Losing a
preference is acceptable; refusing to run is not.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import autostart

AUTO_START_DEFAULT = True


def app_data_dir() -> Path:
    r"""`%APPDATA%\WeekNumber` — read each time, so a test can move it.

    These used to be module constants computed at import. That is one line
    shorter and makes the settings path a thing no test can redirect, which
    means the suite writes into the real profile and can turn the user's
    auto-start off by being run.
    """
    return Path(os.environ["APPDATA"]) / "WeekNumber"


def config_path() -> Path:
    return app_data_dir() / "config.json"


def _load_raw() -> dict:
    """The whole settings file, or an empty one if it cannot be used."""
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    # A file holding a list, a number or `null` parses fine and then breaks
    # every caller that expects to index it.
    return data if isinstance(data, dict) else {}


def _save_raw(data: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_auto_start() -> bool:
    data = _load_raw()
    if "auto_start" in data:
        return bool(data["auto_start"])

    # Nothing saved yet, so the Startup folder itself is the answer: the
    # installer or an earlier run has already put a shortcut there or not, and
    # the menu's tick has to agree with the disk rather than with a default
    # nobody chose.
    try:
        return autostart.is_enabled()
    except OSError:
        return AUTO_START_DEFAULT


def save_auto_start(enabled: bool) -> None:
    # Read-modify-write rather than a fresh file: there may be more settings
    # than this one, and rewriting from scratch is how the next gets dropped.
    data = _load_raw()
    data["auto_start"] = bool(enabled)
    try:
        _save_raw(data)
    except OSError:
        pass                      # a read-only profile still runs
