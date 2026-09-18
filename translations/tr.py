"""Türkçe.

The key is the English sentence — see `i18n`. A key that no longer appears in
the code is dead weight and a sentence with no key here falls back to English;
`tests/test_language.py` checks both directions.
"""

WORDS = {
    # -- the tray menu ------------------------------------------------------
    "Show Calendar": "Takvimi göster",
    "Start when Windows starts": "Windows başladığında başlat",
    "Language": "Dil",
    "Quit": "Çıkış",

    # -- the tooltip --------------------------------------------------------
    "Day {n} of year": "Yılın {n}. günü",
    "Week {n} of year": "Yılın {n}. haftası",

    # -- the line in the menu, and the one under the calendar ---------------
    "Week {week} of {year}  |  {weekday}, {date}":
        "{year} yılının {week}. haftası  |  {weekday}, {date}",
    "{date}  ·  Day {doy}  ·  Week {week}  ·  {span}":
        "{date}  ·  {doy}. gün  ·  {week}. hafta  ·  {span}",
    "Copied": "Kopyalandı",

    # -- the calendar -------------------------------------------------------
    # "Wk" is the week-number column, two letters wide.
    "Wk": "Hf",
    "Mo": "Pt",
    "Tu": "Sa",
    "We": "Ça",
    "Th": "Pe",
    "Fr": "Cu",
    "Sa": "Ct",
    "Su": "Pa",

    "Monday": "Pazartesi",
    "Tuesday": "Salı",
    "Wednesday": "Çarşamba",
    "Thursday": "Perşembe",
    "Friday": "Cuma",
    "Saturday": "Cumartesi",
    "Sunday": "Pazar",

    "January": "Ocak",
    "February": "Şubat",
    "March": "Mart",
    "April": "Nisan",
    "May": "Mayıs",
    "June": "Haziran",
    "July": "Temmuz",
    "August": "Ağustos",
    "September": "Eylül",
    "October": "Ekim",
    "November": "Kasım",
    "December": "Aralık",

    "Jan": "Oca",
    "Feb": "Şub",
    "Mar": "Mar",
    "Apr": "Nis",
    # The short form of Mayıs is the whole word; Turkish does not abbreviate
    # it, and "May" would read as the English month.
    "May": "May",
    "Jun": "Haz",
    "Jul": "Tem",
    "Aug": "Ağu",
    "Sep": "Eyl",
    "Oct": "Eki",
    "Nov": "Kas",
    "Dec": "Ara",

    # -- what goes wrong ----------------------------------------------------
    "Auto-start could not be applied:\n{reason}":
        "Otomatik başlatma uygulanamadı:\n{reason}",
}
