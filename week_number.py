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
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont
import pystray


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

def get_week_number() -> int:
    return datetime.date.today().isocalendar()[1]


def create_icon_image(week: int) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size - 1, size - 1], fill=(20, 20, 20, 230))

    text = str(week)
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    font = None
    for target_size in range(56, 8, -1):
        for path in font_paths:
            try:
                candidate = ImageFont.truetype(path, target_size)
            except (IOError, OSError):
                continue
            bbox = draw.textbbox((0, 0), text, font=candidate)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w <= size - 4 and h <= size - 4:
                font = candidate
                break
        if font is not None:
            break

    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) / 2 - bbox[0]
    y = (size - text_h) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    return img


def build_tooltip() -> str:
    today = datetime.date.today()
    iso = today.isocalendar()
    day_of_year = today.timetuple().tm_yday
    return (
        f"{today.strftime('%d/%m/%Y')}\n"
        f"Day {day_of_year} of year\n"
        f"Week {iso[1]} of year"
    )


def update_loop(icon: pystray.Icon) -> None:
    """Refresh icon and tooltip only when the day changes."""
    while not icon.visible:
        time.sleep(1)
    last_day = datetime.date.today()
    while icon.visible:
        time.sleep(60)
        today = datetime.date.today()
        if today != last_day:
            last_day = today
            week = get_week_number()
            icon.icon = create_icon_image(week)
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


def _render(win: tk.Toplevel, state: dict, today: datetime.date) -> None:
    """(Re-)draw calendar contents into win."""
    for w in win.winfo_children():
        w.destroy()

    year  = state["year"]
    month = state["month"]

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
        _render(win, state, today)
        _reposition(win)

    def go_next():
        m, y = state["month"] + 1, state["year"]
        if m > 12:
            m, y = 1, y + 1
        state["month"], state["year"] = m, y
        _render(win, state, today)
        _reposition(win)

    def go_today():
        state["year"], state["month"] = today.year, today.month
        _render(win, state, today)
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
        text=datetime.date(year, month, 1).strftime("%B  %Y"),
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
    for c, txt in enumerate(["Wk", "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
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

    today_iso = today.isocalendar()
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

        for c, day in enumerate(week, 1):
            is_today  = (day == today)
            in_month  = (day.month == month)
            is_wknd   = (c >= 6)

            if is_today:
                bg, fg, w = _TODAY_BG, _TODAY_FG, "bold"
            elif not in_month:
                bg, fg, w = _BG, _MUTED_FG, "normal"
            elif is_wknd:
                bg, fg, w = _BG, _WEEKEND_FG, "normal"
            else:
                bg, fg, w = _BG, _NORMAL_FG, "normal"

            tk.Label(
                grid_f, text=str(day.day),
                bg=bg, fg=fg, font=("Segoe UI", 9, w),
                width=3, anchor="center",
            ).grid(row=r, column=c + 1, padx=2, pady=2)  # +1 to skip separator col

    # ── Footer ───────────────────────────────────────────────────────────────
    tk.Frame(content, bg=_SEP_COL, height=1).pack(fill="x", pady=(10, 6))

    doy = today.timetuple().tm_yday
    iso = today.isocalendar()
    tk.Label(
        content,
        text=f"{today.strftime('%d %b %Y')}  ·  Day {doy}  ·  Week {iso[1]}",
        bg=_BG, fg=_NORMAL_FG, font=("Segoe UI", 9),
    ).pack()


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

    today = datetime.date.today()
    state.update(year=today.year, month=today.month)

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.configure(bg=_BORDER_COL)
    win.attributes("-topmost", True)
    state["win"] = win

    _render(win, state, today)
    _reposition(win)

    win.bind("<Escape>", lambda e: _close(state))
    win.bind("<FocusOut>", lambda e: win.after(150, lambda: _check_focus(win, state)))
    win.focus_force()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
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
        root.after(0, root.quit)

    today     = datetime.date.today()
    week_n    = today.isocalendar()[1]
    info_text = f"Week {week_n} of {today.year}  |  {today.strftime('%A, %d %b %Y')}"

    icon.menu = pystray.Menu(
        pystray.MenuItem("Show Calendar", toggle_calendar, default=True),
        pystray.MenuItem(info_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )

    # pystray in background thread
    threading.Thread(target=icon.run, daemon=True).start()
    # Day-change refresh in background thread
    threading.Thread(target=update_loop, args=(icon,), daemon=True).start()

    root.protocol("WM_DELETE_WINDOW", quit_app)
    root.mainloop()


if __name__ == "__main__":
    main()
