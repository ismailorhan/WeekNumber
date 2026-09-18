"""Reading it in Turkish, and the catalogue keeping up with the code."""

import ast
import datetime
from pathlib import Path

import pytest

import config
import i18n
import week_number as wn

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def back_to_english():
    """Whatever a test switches to, the next one starts in English."""
    yield
    i18n.use(i18n.DEFAULT)


def test_english_is_what_it_reads_by_default():
    assert i18n.current() == "en"
    assert i18n.t("Quit") == "Quit"


def test_turkish_is_read_when_it_is_chosen():
    i18n.use("tr")
    assert i18n.t("Quit") == "Çıkış"


def test_a_language_nobody_ships_falls_back_rather_than_raising():
    """A config edited by hand, or written by a newer build. The app still
    has to start."""
    assert i18n.use("kl") == "en"
    assert i18n.t("Quit") == "Quit"


def test_an_untranslated_sentence_comes_back_in_english():
    i18n.use("tr")
    assert i18n.t("Something nobody has translated") == \
        "Something nobody has translated"


def test_the_placeholders_survive_translation():
    i18n.use("tr")
    assert i18n.t("Day {n} of year", n=72) == "Yılın 72. günü"


def test_a_translation_with_the_wrong_placeholders_falls_back(monkeypatch):
    """A catalogue is editable text. One that says {gun} where the code says
    {n} must not take the app down mid-menu."""
    monkeypatch.setitem(i18n._catalogue, "Day {n} of year", "Yılın {gun}. günü")
    assert i18n.t("Day {n} of year", n=72) == "Day 72 of year"


# ---------------------------------------------------------------------------
# What the app actually says
# ---------------------------------------------------------------------------

def test_the_menu_is_turkish_throughout(monkeypatch):
    """It used to be half and half: Show Calendar and Quit in English beside
    Windows başladığında başlat in Turkish, which is neither language."""
    monkeypatch.setattr(wn, "today", lambda: datetime.date(2026, 3, 13))
    i18n.use("tr")
    menu = wn.build_menu(lambda *a: None, lambda *a: None, lambda *a: None)
    labels = [str(item.text) for item in menu if item.text]

    assert "Takvimi göster" in labels
    assert "Windows başladığında başlat" in labels
    assert "Çıkış" in labels
    assert "Show Calendar" not in labels


def test_the_dates_are_turkish_too(monkeypatch):
    """`strftime` answers in the machine's locale, which is a different
    question from the language somebody chose in the menu."""
    monkeypatch.setattr(wn, "today", lambda: datetime.date(2026, 3, 13))
    i18n.use("tr")

    assert wn.info_line() == "2026 yılının 11. haftası  |  Cuma, 13 Mar 2026"
    assert wn.summary_line(datetime.date(2026, 4, 15)) == \
        "15 Nis 2026  ·  105. gün  ·  16. hafta  ·  13–19 Nis"


def test_the_tooltip_is_turkish_too(monkeypatch):
    monkeypatch.setattr(wn, "today", lambda: datetime.date(2026, 3, 13))
    i18n.use("tr")
    assert wn.build_tooltip() == "13/03/2026\nYılın 72. günü\nYılın 11. haftası"


def test_the_language_menu_ticks_the_one_in_use():
    i18n.use("tr")
    menu = wn.build_language_menu(lambda code: None)
    ticked = [str(item.text) for item in menu if item.checked]
    assert ticked == ["Türkçe"]


def test_choosing_a_language_is_remembered():
    config.save_language("tr")
    assert config.load_language() == "tr"
    assert i18n.current() == "tr"


def test_a_settings_file_naming_a_language_nobody_ships_still_starts():
    config.save_language("kl")
    assert config.load_language() == "en"


# ---------------------------------------------------------------------------
# The catalogue against the code
# ---------------------------------------------------------------------------

def sentences_in_the_code():
    """Every literal handed to `t(...)`, read out of the source.

    Static rather than by running the app: a sentence behind a branch nobody
    took in a test would otherwise never be checked, and those are exactly
    the ones that stay untranslated.
    """
    found = set()
    for path in REPO.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name) and node.func.id == "t"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                found.add(node.args[0].value)
    # The name tables are looked up through t() by index, so no literal of
    # theirs appears at a call site.
    found |= set(wn.MONTHS) | set(wn.MONTHS_SHORT)
    found |= set(wn.WEEKDAYS) | set(wn.WEEKDAYS_SHORT)
    return found


def test_every_sentence_has_a_turkish_entry():
    """Editing an English sentence orphans its translation, and nothing else
    would notice — the fallback is silent and correct-looking."""
    assert i18n.missing("tr", sentences_in_the_code()) == []


def test_the_catalogue_has_nothing_the_code_no_longer_says():
    from translations import tr
    stale = sorted(set(tr.WORDS) - sentences_in_the_code())
    assert stale == [], f"dead entries: {stale}"
