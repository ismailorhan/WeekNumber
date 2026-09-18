"""
WeekNumber - System tray app that shows the current ISO week number.
Left-click the icon to show/hide a mini calendar popup.
"""

import calendar
import ctypes
import ctypes.wintypes
import datetime
import threading
import time
import winreg
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageDraw, ImageFont
import pystray

import autostart
import config
import version
import i18n
from i18n import t


# ── Calendar colour palette (Catppuccin Mocha) ───────────────────────────────
_BG          = "#1e1e2e"
_BORDER_COL  = "#45475a"
_NORMAL_FG   = "#cdd6f4"
_MUTED_FG    = "#585b70"
_NAV_FG      = "#89b4fa"
_WEEKEND_FG  = "#f38ba8"
_WEEK_FG     = "#9399b2"
_CUR_WEEK_FG = "#a6e3a1"
_TODAY_BG    = "#89b4fa"
_TODAY_FG    = "#1e1e2e"
_SEP_COL     = "#313244"


# ── Tray icon helpers ─────────────────────────────────────────────────────────

def today() -> datetime.date:
    """What day it is. The one place anything asks, so a test can answer.

    Everything below goes through this rather than calling
    `datetime.date.today()` itself: the interesting cases are the days nobody
    can wait for -- the ones where the ISO week does not match the calendar
    year, and the midnight the app has to notice.
    """
    return datetime.date.today()


def get_week_number() -> int:
    return today().isocalendar()[1]


_THEME_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"


def taskbar_is_light() -> bool:
    """Whether the notification area is on a light background.

    `SystemUsesLightTheme`, not `AppsUseLightTheme`: Windows lets the two
    differ, and the one this icon sits on is the system one.

    Dark when it cannot be read. Windows 11 ships dark, and a white number on
    a light bar is easier to lose than a dark number on a dark one — both are
    wrong, but not equally.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _THEME_KEY) as key:
            return bool(winreg.QueryValueEx(key, "SystemUsesLightTheme")[0])
    except OSError:
        return False


def create_icon_image(week: int) -> Image.Image:
    """The number, as large as it will go, on nothing.

    Two things this does not do any more. It does not paint its own
    background: Windows shows the icon at 16px on the taskbar, and an opaque
    square is a dark blob on a light taskbar and a light one on a dark
    taskbar. And it does not leave a margin — the digits used to get about
    twelve of those sixteen pixels and the rest was box, and nothing reads the
    box.
    """
    size = 64
    margin = 2                 # enough that antialiasing is not clipped
    text = str(week)
    fill = (32, 32, 32, 255) if taskbar_is_light() else (255, 255, 255, 255)

    # Drawn big, cropped to the ink, then scaled to fit. The obvious way is to
    # search for the font size whose `textbbox` fits the square, and it was
    # what this did — but `textbbox` is the font's box, not the ink: it
    # includes each glyph's side bearings, so "11", which is mostly bearing,
    # came out 54px wide in a 60px space while "44" came out 58. Cropping to
    # what was actually drawn is the only way every number gets the same room.
    big = size * 4
    canvas = Image.new("RGBA", (big * 2, big * 2), (0, 0, 0, 0))
    ImageDraw.Draw(canvas).text((big // 2, big // 2), text, fill=fill,
                                font=_icon_font(big // 2), anchor="lt")

    ink = canvas.crop(canvas.getchannel("A").getbbox())
    room = size - margin * 2
    scale = min(room / ink.width, room / ink.height)
    ink = ink.resize((max(1, round(ink.width * scale)),
                      max(1, round(ink.height * scale))), Image.LANCZOS)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.paste(ink, ((size - ink.width) // 2, (size - ink.height) // 2), ink)
    return img


def _icon_font(points: int):
    """The heaviest of the three faces that is actually installed.

    Bold, because the icon ends up 16px on the taskbar and a regular weight
    loses its thin strokes to the downscale.
    """
    for path in ("C:/Windows/Fonts/arialbd.ttf",
                 "C:/Windows/Fonts/calibrib.ttf",
                 "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(path, points)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def build_tooltip() -> str:
    day = today()
    iso = day.isocalendar()
    day_of_year = day.timetuple().tm_yday
    return "\n".join((
        f"{day.day:02d}/{day.month:02d}/{day.year}",
        t("Day {n} of year", n=day_of_year),
        t("Week {n} of year", n=iso[1]),
    ))


def info_line() -> str:
    """The date the right-click menu shows.

    A function rather than a string, and that is the whole point: it used to
    be computed once in `main` and handed to pystray as a fixed label. The
    icon and the tooltip were refreshed when the day changed and this was not,
    so a machine left on overnight opened its menu on yesterday -- which is
    the one thing this app is for.
    """
    day = today()
    return t("Week {week} of {year}  |  {weekday}, {date}",
             week=day.isocalendar()[1], year=day.year,
             weekday=weekday_long(day), date=spell(day, with_year=True))


#: Month and weekday names as this app spells them. Not `strftime`: that
#: answers in the machine's locale, which is a different question from the
#: language somebody chose in the menu -- and on this machine the two differ.
#: English here because the English word is the translation key; see `i18n`.
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")
MONTHS_SHORT = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday")
#: Two letters, because the calendar's columns are three characters wide.
WEEKDAYS_SHORT = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")


def month_short(day: datetime.date) -> str:
    return t(MONTHS_SHORT[day.month - 1])


def month_long(month: int) -> str:
    return t(MONTHS[month - 1])


def weekday_long(day: datetime.date) -> str:
    return t(WEEKDAYS[day.weekday()])


def week_range(day: datetime.date) -> tuple[datetime.date, datetime.date]:
    """The Monday and Sunday of the ISO week that `day` falls in.

    Computed from the weekday, not from the calendar grid the popup happens
    to be showing. Week 1 of 2026 starts on 29 December 2025, and a range
    clamped to the visible month gets exactly the week people ask about wrong.
    """
    monday = day - datetime.timedelta(days=day.weekday())
    return monday, monday + datetime.timedelta(days=6)


def spell(day: datetime.date, with_year: bool) -> str:
    """`3 May`, or `3 May 2026`. No leading zero — this is prose, not a field.

    Day before month in both languages this ships in, so the order itself is
    not translated; only the month name is.
    """
    return f"{day.day} {month_short(day)}" + (f" {day.year}" if with_year else "")


def summary_line(day: datetime.date) -> str:
    """What the calendar's footer says about the day that is selected.

    The three questions somebody with a week-number habit actually has, in
    one line: what is this date, where is it in the year, and which week is
    it -- plus the week's own dates, because "week 16" is only useful to
    somebody who can also say when week 16 is.
    """
    monday, sunday = week_range(day)
    if monday.year != sunday.year:
        span = f"{spell(monday, True)} – {spell(sunday, True)}"
    elif monday.month != sunday.month:
        span = f"{spell(monday, False)} – {spell(sunday, False)}"
    else:
        # A tight dash when both ends are bare numbers, a spaced one when they
        # carry a month or a year. Anything else reads as a subtraction.
        span = f"{monday.day}–{sunday.day} {month_short(sunday)}"
    return t("{date}  ·  Day {doy}  ·  Week {week}  ·  {span}",
             date=spell(day, True), doy=day.timetuple().tm_yday,
             week=day.isocalendar()[1], span=span)


def update_loop(icon: pystray.Icon) -> None:
    """Refresh icon and tooltip only when the day changes.

    The menu is not touched here: its date line is a callable, which pystray
    asks for each time the menu is opened, so it is never stale and never
    needs pushing.
    """
    while not icon.visible:
        time.sleep(1)
    last_day = today()
    while icon.visible:
        time.sleep(60)
        day = today()
        if day != last_day:
            last_day = day
            icon.icon = create_icon_image(get_week_number())
            icon.title = build_tooltip()


# ── Calendar popup ────────────────────────────────────────────────────────────

def _work_area() -> ctypes.wintypes.RECT:
    """Return the working area of the primary monitor (screen minus taskbar)."""
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
    return rect


def _reposition(win: tk.Toplevel) -> None:
    """Snap the popup to the bottom-right corner, flush against the taskbar."""
    win.update_idletasks()
    work = _work_area()
    ww   = win.winfo_reqwidth()
    wh   = win.winfo_reqheight()
    margin = 8
    x = work.right  - ww - margin
    y = work.bottom - wh - margin
    win.geometry(f"+{x}+{y}")


def _close(state: dict) -> None:
    w = state.get("win")
    if w:
        try:
            w.destroy()
        except tk.TclError:
            pass
        state["win"] = None


def _check_focus(win: tk.Toplevel, state: dict) -> None:
    """Close only when focus has moved outside the calendar window tree."""
    try:
        if not win.winfo_exists():
            state["win"] = None
            return
        focused = win.focus_get()
        if focused is None or not str(focused).startswith(str(win)):
            _close(state)
    except tk.TclError:
        state["win"] = None


def _render(win: tk.Toplevel, state: dict, day: datetime.date) -> None:
    """(Re-)draw calendar contents into win."""
    for w in win.winfo_children():
        w.destroy()

    year  = state["year"]
    month = state["month"]
    # Which day the footer is describing. Today until somebody clicks another.
    selected = state.setdefault("selected", day)

    def pick(picked: datetime.date) -> None:
        """Clicking a day moves the footer to it, and follows it out of the
        month when the click lands on one of the greyed-out neighbours."""
        state["selected"] = picked
        state["year"], state["month"] = picked.year, picked.month
        _render(win, state, day)
        _reposition(win)

    # Border frame
    border_f = tk.Frame(win, bg=_BORDER_COL, padx=1, pady=1)
    border_f.pack(fill="both", expand=True)

    # Content frame
    content = tk.Frame(border_f, bg=_BG, padx=14, pady=12)
    content.pack(fill="both", expand=True)

    # ── Header: ‹  Month Year  › ─────────────────────────────────────────────
    hdr = tk.Frame(content, bg=_BG)
    hdr.pack(fill="x", pady=(0, 8))

    def go_prev():
        m, y = state["month"] - 1, state["year"]
        if m < 1:
            m, y = 12, y - 1
        state["month"], state["year"] = m, y
        _render(win, state, day)
        _reposition(win)

    def go_next():
        m, y = state["month"] + 1, state["year"]
        if m > 12:
            m, y = 1, y + 1
        state["month"], state["year"] = m, y
        _render(win, state, day)
        _reposition(win)

    def go_today():
        state["year"], state["month"] = day.year, day.month
        state["selected"] = day
        _render(win, state, day)
        _reposition(win)

    btn_kw = dict(
        bg=_BG, fg=_NAV_FG,
        activebackground=_SEP_COL, activeforeground=_NAV_FG,
        bd=0, font=("Segoe UI", 13, "bold"),
        cursor="hand2", highlightthickness=0, relief="flat",
    )
    tk.Button(hdr, text="‹", command=go_prev, **btn_kw).pack(side="left")

    month_lbl = tk.Label(
        hdr,
        text=f"{month_long(month)}  {year}",
        bg=_BG, fg=_NORMAL_FG,
        font=("Segoe UI", 10, "bold"),
        cursor="hand2",
    )
    month_lbl.pack(side="left", expand=True)
    month_lbl.bind("<Button-1>", lambda e: go_today())   # click label → jump to today

    tk.Button(hdr, text="›", command=go_next, **btn_kw).pack(side="right")

    # ── Day grid ─────────────────────────────────────────────────────────────
    grid_f = tk.Frame(content, bg=_BG)
    grid_f.pack()

    # Column headers  (col 1 is reserved for the vertical separator)
    for c, txt in enumerate((t("Wk"),) + tuple(t(d) for d in WEEKDAYS_SHORT)):
        if c == 0:
            fg = _WEEK_FG
        elif c in (6, 7):
            fg = _WEEKEND_FG
        else:
            fg = _MUTED_FG
        col = c if c == 0 else c + 1   # skip col 1
        tk.Label(
            grid_f, text=txt, bg=_BG, fg=fg,
            font=("Segoe UI", 8), width=3, anchor="center",
        ).grid(row=0, column=col, padx=2, pady=(0, 4))

    today_iso = day.isocalendar()
    cal   = calendar.Calendar(firstweekday=0)   # Monday first
    weeks = cal.monthdatescalendar(year, month)

    # 1px vertical separator between Wk and Mo columns
    tk.Frame(grid_f, bg=_SEP_COL, width=1).grid(
        row=0, column=1, rowspan=len(weeks) + 1, sticky="ns", padx=(4, 4),
    )

    for r, week in enumerate(weeks, 1):
        wn    = week[0].isocalendar()[1]
        wn_yr = week[0].isocalendar()[0]
        is_cur_wk = (wn == today_iso[1] and wn_yr == today_iso[0])

        tk.Label(
            grid_f, text=str(wn), bg=_BG,
            fg=_CUR_WEEK_FG if is_cur_wk else _WEEK_FG,
            font=("Segoe UI", 8, "bold" if is_cur_wk else "normal"),
            width=3, anchor="center",
        ).grid(row=r, column=0, padx=2, pady=2)

        for c, cell in enumerate(week, 1):
            is_today  = (cell == day)
            in_month  = (cell.month == month)
            is_wknd   = (c >= 6)

            if is_today:
                bg, fg, w = _TODAY_BG, _TODAY_FG, "bold"
            elif not in_month:
                bg, fg, w = _BG, _MUTED_FG, "normal"
            elif is_wknd:
                bg, fg, w = _BG, _WEEKEND_FG, "normal"
            else:
                bg, fg, w = _BG, _NORMAL_FG, "normal"

            if cell == selected and cell != day:
                # Picked, but not today: an outline rather than the solid fill,
                # so "where I am looking" and "what day it is" stay distinct.
                bg, fg, w = _SEP_COL, _NORMAL_FG, "bold"

            cell_lbl = tk.Label(
                grid_f, text=str(cell.day),
                bg=bg, fg=fg, font=("Segoe UI", 9, w),
                width=3, anchor="center", cursor="hand2",
            )
            cell_lbl.grid(row=r, column=c + 1, padx=2, pady=2)  # skip separator
            cell_lbl.bind("<Button-1>", lambda e, picked=cell: pick(picked))

    # ── Footer ───────────────────────────────────────────────────────────────
    tk.Frame(content, bg=_SEP_COL, height=1).pack(fill="x", pady=(10, 6))

    footer = tk.Label(
        content, text=summary_line(selected),
        bg=_BG, fg=_NORMAL_FG, font=("Segoe UI", 9), cursor="hand2",
    )
    footer.pack()

    def copy(_event=None):
        """Put the line on the clipboard, exactly as it reads.

        What you see is what you get: the alternative is to copy some tidier
        canonical form, and then what lands in the paste is not what was on
        screen, which is its own small betrayal.
        """
        try:
            win.clipboard_clear()
            win.clipboard_append(footer["text"])
        except tk.TclError:
            return                      # the clipboard can be held by anything
        footer.configure(text=t("Copied"), fg=_CUR_WEEK_FG)
        # Back to the line after a moment. Without the guard this raises when
        # the popup is closed inside the second.
        win.after(900, lambda: footer.winfo_exists() and footer.configure(
            text=summary_line(state["selected"]), fg=_NORMAL_FG))

    footer.bind("<Button-1>", copy)


def show_calendar(root: tk.Tk, state: dict) -> None:
    """Toggle the calendar popup."""
    w = state.get("win")
    if w:
        try:
            if w.winfo_exists():
                _close(state)
                return
        except tk.TclError:
            pass
        state["win"] = None

    day = today()
    # Every open starts on today, whatever was being looked at last time.
    state.update(year=day.year, month=day.month, selected=day)

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.configure(bg=_BORDER_COL)
    win.attributes("-topmost", True)
    state["win"] = win

    _render(win, state, day)
    _reposition(win)

    win.bind("<Escape>", lambda e: _close(state))
    win.bind("<FocusOut>", lambda e: win.after(150, lambda: _check_focus(win, state)))
    win.focus_force()


# ── Menu ──────────────────────────────────────────────────────────────────────

def build_language_menu(on_language) -> pystray.Menu:
    """One radio-ish entry per language, ticked on the current one.

    `radio=True` rather than two independent ticks: they are alternatives, and
    a menu that lets you tick both is lying about what it will do.
    """
    return pystray.Menu(*[
        pystray.MenuItem(
            name,
            lambda item, code=code: on_language(code),
            checked=lambda item, code=code: i18n.current() == code,
            radio=True,
        )
        for code, name in i18n.LANGUAGES
    ])


def build_menu(on_calendar, on_autostart, on_quit, on_language=None) -> pystray.Menu:
    """The right-click menu, built from what it should do rather than from
    what is in scope where it happens to be created — so it can be built in a
    test without a tray, an icon or an event loop."""
    return pystray.Menu(
        pystray.MenuItem(lambda item: t("Show Calendar"), on_calendar,
                         default=True),
        # Callable, not a string: see `info_line`.
        pystray.MenuItem(lambda item: info_line(), None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda item: t("Start when Windows starts"),
            on_autostart,
            checked=lambda item: config.load_auto_start(),
        ),
        pystray.MenuItem(lambda item: t("Language"),
                         build_language_menu(on_language or (lambda code: None))),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(version.full(), None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(lambda item: t("Quit"), on_quit),
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    # Before anything builds a string. Reads the setting and applies it.
    config.load_language()

    # Hidden tkinter root lives in the main thread
    root = tk.Tk()
    root.withdraw()

    cal_state: dict = {"win": None, "year": None, "month": None}

    week  = get_week_number()
    image = create_icon_image(week)
    icon  = pystray.Icon(name="WeekNumber", icon=image, title=build_tooltip())

    def toggle_calendar(icon_arg=None, item=None):
        root.after(0, lambda: show_calendar(root, cal_state))

    def quit_app(icon_arg=None, item=None):
        icon.stop()
        # The popup is a window of its own and outlives the tray icon if
        # nobody closes it, leaving a calendar on screen with nothing behind
        # it and a process that will not end.
        root.after(0, lambda: _close(cal_state))
        root.after(0, root.quit)

    def toggle_autostart(icon_arg=None, item=None):
        new_state = not config.load_auto_start()
        config.save_auto_start(new_state)
        try:
            autostart.apply(new_state)
        except Exception as exc:
            messagebox.showwarning(
                "WeekNumber",
                t("Auto-start could not be applied:\n{reason}", reason=exc),
            )

    def choose_language(code, item=None):
        config.save_language(i18n.use(code))
        # Everything the language touches, refreshed at once. The menu labels
        # are callables and come back translated on their own; the tooltip and
        # an open calendar do not, so they are pushed.
        icon.title = build_tooltip()
        icon.update_menu()
        if cal_state.get("win"):
            root.after(0, lambda: (_close(cal_state),
                                   show_calendar(root, cal_state)))

    icon.menu = build_menu(toggle_calendar, toggle_autostart, quit_app,
                           choose_language)

    # pystray in background thread
    threading.Thread(target=icon.run, daemon=True).start()
    # Day-change refresh in background thread
    threading.Thread(target=update_loop, args=(icon,), daemon=True).start()

    root.protocol("WM_DELETE_WINDOW", quit_app)
    root.mainloop()


if __name__ == "__main__":
    main()
