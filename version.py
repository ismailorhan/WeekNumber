"""What build this is.

Two questions get asked about a tool running on somebody else's machine:
which version, and is it the one I think I installed. A release number alone
answers the first; it does not answer the second, because two builds of
"1.0.0" from different commits look identical. So the stamp carries the commit
and the build date too, written in by `stamp_version.py`.

Nothing here is computed at runtime: a frozen app has no git repository to
ask.

Ported from ShooApp, which learned it from Service Officer. The lesson worth
carrying is the one in `declared_versions`: before this, `installer.iss` was
the only place a version was written, so it was never compared to anything.
"""

from __future__ import annotations

import sys

#: Bumped by hand for a release, and matched by installer.iss. `tests/
#: test_version.py` fails if the two ever disagree, and so does the release
#: build — a version that contradicts itself is worse than none, because it
#: makes "which build is this" unanswerable exactly when somebody is asking.
VERSION = "1.1.0"

#: Which build this is, counted by `stamp_version.py` and restarted when
#: VERSION changes. Zero means this *is* the release; anything else is an
#: internal build and shows as 1.1.0.3 — three parts for what people get, a
#: fourth for what we build in between.
BUILD = 0
#: Filled in by `stamp_version.py`: short commit, and "-dirty" if the tree had
#: edits when it was built.
COMMIT = "dev"
#: Filled in by `stamp_version.py`, the date and time of the build.
BUILT = ""


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def short() -> str:
    """`1.1.0` for the release itself, `1.1.0.7` for an internal build."""
    return VERSION if not BUILD else f"{VERSION}.{BUILD}"


def full() -> str:
    """Everything, for the tray menu and for a support request.

    The commit lives here rather than in the version, because it answers a
    different question: which code, not which build number. And a checkout
    says so — "the installed copy misbehaves" and "your working tree
    misbehaves" are different problems that get confused constantly.
    """
    parts = [f"Version {short()}"]
    if COMMIT not in ("", "dev"):
        parts.append(f"commit {COMMIT}")
    if BUILT:
        parts.append(BUILT)
    if not is_frozen():
        parts.append("running from source")
    return "  ·  ".join(parts)
