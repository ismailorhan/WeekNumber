"""The settings file, which lives on a roaming profile and must not be trusted.

A tray app that cannot read its settings still has to start. Every read here
falls back; losing a preference is acceptable, refusing to run is not.
"""

import json

import config


def test_nothing_saved_falls_back_to_the_startup_folder(monkeypatch):
    """With no file yet, the shortcut on disk is the answer — the installer or
    a previous run has already decided, and the tick has to agree with the
    disk rather than with a default nobody chose."""
    monkeypatch.setattr(config.autostart, "is_enabled", lambda: False)
    assert config.load_auto_start() is False

    monkeypatch.setattr(config.autostart, "is_enabled", lambda: True)
    assert config.load_auto_start() is True


def test_a_saved_preference_is_read_back():
    config.save_auto_start(False)
    assert config.load_auto_start() is False

    config.save_auto_start(True)
    assert config.load_auto_start() is True


def test_a_half_written_file_is_ignored_rather_than_fatal(monkeypatch):
    monkeypatch.setattr(config.autostart, "is_enabled", lambda: True)
    path = config.config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not json", encoding="utf-8")

    assert config.load_auto_start() is True


def test_a_file_holding_something_that_is_not_an_object_is_ignored(monkeypatch):
    # A list or a number parses fine and then breaks every caller that
    # expects to index it.
    monkeypatch.setattr(config.autostart, "is_enabled", lambda: True)
    path = config.config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[1, 2, 3]", encoding="utf-8")

    assert config.load_auto_start() is True


def test_a_startup_folder_that_cannot_be_read_still_gives_an_answer(monkeypatch):
    def raise_it():
        raise OSError("the profile share is gone")

    monkeypatch.setattr(config.autostart, "is_enabled", raise_it)
    assert config.load_auto_start() is config.AUTO_START_DEFAULT


def test_settings_that_cannot_be_written_do_not_bring_the_app_down(monkeypatch):
    def refuse(*args, **kwargs):
        raise OSError("read-only profile")

    monkeypatch.setattr(config, "_save_raw", refuse)
    # The point is that this returns rather than raising into the menu handler.
    config.save_auto_start(True)


def test_the_file_goes_where_appdata_says(elsewhere):
    config.save_auto_start(True)
    written = elsewhere / "WeekNumber" / "config.json"
    assert json.loads(written.read_text(encoding="utf-8")) == {"auto_start": True}
