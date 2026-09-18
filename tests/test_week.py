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


# ---------------------------------------------------------------------------
# How much of the icon the number gets, and what colour it is
# ---------------------------------------------------------------------------

def ink_bounds(image):
    """The box the drawn number occupies, in pixels."""
    return image.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()


@pytest.mark.parametrize("week", [1, 9, 11, 53])
def test_the_number_is_drawn_as_large_as_it_will_go(week):
    """It used to sit inside an opaque square with a margin, so at the 16px
    Windows actually shows, the digits got about twelve of those pixels and
    the rest was box. Nothing reads the box.

    Measured against the larger dimension only, because the two cannot both
    be filled: one digit is tall and narrow, two digits are wide and short,
    and whichever way round it is, the other axis is whatever the glyph
    shape leaves.
    """
    image = wn.create_icon_image(week)
    left, top, right, bottom = ink_bounds(image)
    longest = max(right - left, bottom - top)

    assert longest >= image.width * 0.85, f"{longest}px of {image.width}"


def test_the_number_is_centred():
    image = wn.create_icon_image(9)
    left, top, right, bottom = ink_bounds(image)
    # Equal margins to within a pixel or two, on both axes.
    assert abs(left - (image.width - right)) <= 3
    assert abs(top - (image.height - bottom)) <= 3


def test_the_icon_has_no_opaque_background():
    """The taskbar shows through. A painted-on background is a dark blob on a
    light taskbar and a light one on a dark taskbar — whichever it picks is
    wrong half the time."""
    image = wn.create_icon_image(11)
    corners = [image.getpixel(p) for p in
               ((0, 0), (image.width - 1, 0), (0, image.height - 1),
                (image.width - 1, image.height - 1))]
    assert all(pixel[3] == 0 for pixel in corners), corners


def test_the_number_is_light_on_a_dark_taskbar(monkeypatch):
    monkeypatch.setattr(wn, "taskbar_is_light", lambda: False)
    image = wn.create_icon_image(11)
    assert any(colour[:3] == (255, 255, 255)
               for _count, colour in image.getcolors(maxcolors=4096))


def test_the_number_is_dark_on_a_light_taskbar(monkeypatch):
    """Measured on this machine: SystemUsesLightTheme is 0, so this is the
    case nobody here would ever see go wrong."""
    monkeypatch.setattr(wn, "taskbar_is_light", lambda: True)
    image = wn.create_icon_image(11)
    assert any(sum(colour[:3]) < 200
               for _count, colour in image.getcolors(maxcolors=4096))


def test_a_taskbar_theme_that_cannot_be_read_assumes_dark(monkeypatch):
    """Windows 11 ships dark, and a white number on a dark bar is the safer
    guess than the other way round."""
    def no_registry(*args, **kwargs):
        raise OSError("no such key")

    monkeypatch.setattr(wn.winreg, "OpenKey", no_registry)
    assert wn.taskbar_is_light() is False


# ---------------------------------------------------------------------------
# The calendar as a tool: pick a day, read its week, copy the line
# ---------------------------------------------------------------------------

def test_a_week_runs_monday_to_sunday():
    monday, sunday = wn.week_range(datetime.date(2026, 4, 15))   # a Wednesday
    assert monday == datetime.date(2026, 4, 13)
    assert sunday == datetime.date(2026, 4, 19)


def test_a_week_that_straddles_new_year_still_runs_monday_to_sunday():
    """Week 1 of 2026 starts in December 2025. A range computed by clamping to
    the month — which is what a calendar grid tempts you into — gets this
    wrong, and this is the week people actually ask about."""
    monday, sunday = wn.week_range(datetime.date(2025, 12, 31))
    assert monday == datetime.date(2025, 12, 29)
    assert sunday == datetime.date(2026, 1, 4)


def test_the_summary_says_the_date_the_day_of_year_the_week_and_its_range():
    line = wn.summary_line(datetime.date(2026, 4, 15))
    assert line == "15 Apr 2026  ·  Day 105  ·  Week 16  ·  13–19 Apr"


def test_a_summary_whose_week_crosses_a_month_says_both_months():
    line = wn.summary_line(datetime.date(2026, 4, 30))
    assert "27 Apr – 3 May" in line


def test_a_summary_whose_week_crosses_a_year_says_both_years():
    """The one case where leaving the year off would be actively misleading."""
    line = wn.summary_line(datetime.date(2025, 12, 31))
    assert "29 Dec 2025 – 4 Jan 2026" in line
