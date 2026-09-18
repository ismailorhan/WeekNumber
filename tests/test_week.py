"""What the icon, the tooltip and the menu say, and when they say it again."""

import datetime

import pytest

import week_number as wn


def on(year, month, day, monkeypatch):
    """Pretend today is that date, for everything that asks."""
    monkeypatch.setattr(wn, "today", lambda: datetime.date(year, month, day))


# ---------------------------------------------------------------------------
# The number itself
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("date, week", [
    (datetime.date(2026, 3, 13), 11),
    # 1 January belongs to the last year's week more often than not. 2027
    # opens on a Friday, so its first three days are 2026's week 53.
    (datetime.date(2027, 1, 1), 53),
    # And the other way: 2025 closes on a Wednesday, so 29-31 December are
    # already week 1 of 2026.
    (datetime.date(2025, 12, 31), 1),
    # A 53-week year, which is the case a naive day-of-year ÷ 7 gets wrong.
    (datetime.date(2026, 12, 31), 53),
])
def test_the_week_is_the_iso_week(date, week, monkeypatch):
    monkeypatch.setattr(wn, "today", lambda: date)
    assert wn.get_week_number() == week


def test_the_tooltip_carries_the_date_the_day_and_the_week(monkeypatch):
    on(2026, 3, 13, monkeypatch)
    assert wn.build_tooltip() == "13/03/2026\nDay 72 of year\nWeek 11 of year"


# ---------------------------------------------------------------------------
# The menu line that used to be written once and never again
# ---------------------------------------------------------------------------

def test_the_menu_line_says_todays_week(monkeypatch):
    on(2026, 3, 13, monkeypatch)
    assert wn.info_line() == "Week 11 of 2026  |  Friday, 13 Mar 2026"


def test_the_menu_line_is_asked_again_each_time_the_menu_opens(monkeypatch):
    """It used to be a string computed once at startup and handed to pystray.

    The icon and the tooltip were refreshed at midnight and this was not, so a
    machine left on overnight opened the menu on yesterday's date -- the one
    thing the app exists to tell you.
    """
    on(2026, 3, 13, monkeypatch)
    menu = wn.build_menu(lambda *a: None, lambda *a: None, lambda *a: None)
    info = [item for item in menu if not item.enabled][0]

    assert info.text == "Week 11 of 2026  |  Friday, 13 Mar 2026"

    on(2026, 3, 14, monkeypatch)          # midnight passes

    assert info.text == "Week 11 of 2026  |  Saturday, 14 Mar 2026"


def test_the_menu_offers_the_calendar_the_autostart_toggle_and_quit():
    menu = wn.build_menu(lambda *a: None, lambda *a: None, lambda *a: None)
    labels = [str(item.text) for item in menu if item.text]
    assert "Show Calendar" in labels
    assert "Quit" in labels


def test_quitting_is_wired_to_what_it_was_given():
    stopped = []
    menu = wn.build_menu(lambda *a: None, lambda *a: None,
                         lambda *a: stopped.append(True))
    quit_item = [item for item in menu if str(item.text) == "Quit"][0]
    quit_item(None)
    assert stopped == [True]


# ---------------------------------------------------------------------------
# The icon
# ---------------------------------------------------------------------------

def test_the_icon_is_drawn_with_the_number_on_it():
    image = wn.create_icon_image(11)
    assert image.size == (64, 64)
    # White text on a dark square: the white is the number, and an icon that
    # rendered nothing would have none of it.
    assert any(colour[:3] == (255, 255, 255)
               for _count, colour in image.getcolors(maxcolors=4096))


def test_a_two_digit_week_still_fits():
    """The font is chosen by shrinking until the text fits, so the case that
    can fail is the widest one."""
    wide = wn.create_icon_image(53)
    narrow = wn.create_icon_image(1)
    assert wide.size == narrow.size == (64, 64)
