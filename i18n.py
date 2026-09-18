"""What the app says, in the language somebody reads.

Ported from ShooApp. The rule that matters:

**The English sentence is the key.** `t("Quit")` rather than `t("menu.quit")`.
Three reasons: the code stays readable, because a file full of invented keys
cannot be reviewed without the catalogue open beside it; nothing has to be
named, and a badly named key outlives the sentence it named; and a missing
translation falls back to the English, which is the right failure — the other
way round shows `menu.quit` to a person.

The cost is that editing an English sentence orphans its translation. That is
what `missing()` is for, and a test uses it.

The menu here used to be half and half: *Show Calendar* and *Quit* in English
beside *Windows başladığında başlat* in Turkish, which is neither language.
"""

from __future__ import annotations

#: The languages there are. The code is what the config holds and what a
#: catalogue module is named after.
LANGUAGES = (("en", "English"), ("tr", "Türkçe"))
DEFAULT = "en"

_current = DEFAULT
_catalogue: dict[str, str] = {}


def use(code: str) -> str:
    """Read everything in this language from now on. Returns the code used.

    An unknown code is English rather than an error: a config edited by hand,
    or written by a newer build, must not stop the app from starting.
    """
    global _current, _catalogue
    code = (code or DEFAULT).strip().lower()
    if code not in dict(LANGUAGES):
        code = DEFAULT
    _current = code
    _catalogue = _load(code)
    return code


def current() -> str:
    return _current


def _load(code: str) -> dict[str, str]:
    """That language's catalogue; {} for English and for anything unreadable."""
    if code == DEFAULT:
        return {}
    try:
        module = __import__(f"translations.{code}", fromlist=["WORDS"])
        return dict(getattr(module, "WORDS", {}) or {})
    except Exception:
        return {}


def t(text: str, **fields) -> str:
    """This sentence, in the current language.

    `fields` are substituted after the lookup, so a template is translated as
    a whole sentence — word order differs between languages, and a sentence
    assembled from pieces cannot be reordered.
    """
    said = _catalogue.get(text, text)
    if not fields:
        return said
    try:
        return said.format(**fields)
    except (KeyError, IndexError, ValueError):
        try:
            return text.format(**fields)
        except Exception:
            return text


def missing(code: str, texts) -> list[str]:
    """Which of these sentences that language has no entry for."""
    words = _load(code)
    return sorted({s for s in texts if s and s not in words})


use(DEFAULT)
