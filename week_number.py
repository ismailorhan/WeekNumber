"""
WeekNumber - System tray app that shows the current ISO week number.
"""

import datetime
import threading
import time

from PIL import Image, ImageDraw, ImageFont
import pystray


def get_week_number() -> int:
    return datetime.date.today().isocalendar()[1]


def create_icon_image(week: int) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Solid dark background — stays readable at any tray scaling
    draw.rectangle([0, 0, size - 1, size - 1], fill=(20, 20, 20, 230))

    text = str(week)

    # Grow the font until the text nearly fills the canvas width
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


def build_menu(icon: pystray.Icon) -> pystray.Menu:
    today = datetime.date.today()
    week = today.isocalendar()[1]
    year = today.year
    label = f"Week {week} of {year}  |  {today.strftime('%A, %d %b %Y')}"
    return pystray.Menu(
        pystray.MenuItem(label, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", lambda: icon.stop()),
    )


def update_loop(icon: pystray.Icon) -> None:
    """Refresh icon, tooltip and menu only when the day changes."""
    # icon.visible is False until icon.run() shows the tray icon;
    # wait here so the loop doesn't exit immediately.
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
            icon.menu = build_menu(icon)


def main() -> None:
    week = get_week_number()
    image = create_icon_image(week)

    icon = pystray.Icon(
        name="WeekNumber",
        icon=image,
        title=build_tooltip(),
    )
    icon.menu = build_menu(icon)

    # Start background refresh thread
    thread = threading.Thread(target=update_loop, args=(icon,), daemon=True)
    thread.start()

    icon.run()


if __name__ == "__main__":
    main()
