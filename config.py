import json
import os

APP_DATA_DIR = os.path.join(os.environ["APPDATA"], "WeekNumber")
CONFIG_PATH = os.path.join(APP_DATA_DIR, "config.json")

AUTO_START_DEFAULT = True


def _load_raw() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_raw(data: dict) -> None:
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_auto_start() -> bool:
    data = _load_raw()
    if "auto_start" in data:
        return bool(data["auto_start"])
    try:
        import autostart
        return autostart.is_enabled()
    except Exception:
        return AUTO_START_DEFAULT


def save_auto_start(enabled: bool) -> None:
    data = _load_raw()
    data["auto_start"] = bool(enabled)
    _save_raw(data)
