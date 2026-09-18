"""The build scripts, checked as text.

Not a substitute for running them. But an installer that writes a shortcut
into the wrong person's Startup folder looks fine until somebody other than
an administrator installs it, and by then it is a support call rather than a
diff.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUILD = (REPO / "build.bat").read_text(encoding="utf-8")
ISS = (REPO / "installer.iss").read_text(encoding="utf-8")
WORKFLOW = (REPO / ".github" / "workflows" / "release.yml").read_text(
    encoding="utf-8")


def pyinstaller_flags(text):
    """The `--flags` handed to PyInstaller, whichever recipe this is.

    Both spell the same build in different syntaxes — carets in the batch
    file, YAML folding in the workflow — so the flags are compared and the
    punctuation is not.
    """
    start = text.index("PyInstaller")
    end = text.index("week_number.py", start)
    return {word for word in text[start:end].split() if word.startswith("--")}


def test_the_app_does_not_ask_for_administrator():
    """It reads the date and draws a calendar. Nothing it does needs elevation,
    and asking for it is not free: an admin-manifested exe in the Startup
    folder prompts at every logon on a standard account, which makes the
    auto-start this app ships with unusable."""
    for recipe in (BUILD, WORKFLOW):
        assert "--uac-admin" not in pyinstaller_flags(recipe)


def test_the_two_build_recipes_ask_for_the_same_build():
    """One is what runs on this machine and the other is what ships. A flag
    added to one and not the other produces a release that differs from
    everything it was tested as, and nothing says so."""
    assert pyinstaller_flags(BUILD) == pyinstaller_flags(WORKFLOW)


def test_the_installer_does_not_write_the_startup_shortcut():
    """It used to, and it runs as administrator. On a machine where a standard
    user starts the install and types an administrator's password, `userstartup`
    is the administrator's Startup folder — a person who never signs in. The
    app writes the shortcut itself, while running as whoever ticked it, which
    is the only context in which "the user's Startup folder" means anything.
    """
    assert "Tasks: autostart" not in ISS
    assert 'Name: "autostart"' not in ISS


def test_uninstalling_still_takes_the_shortcut_away():
    """The app writes it now, but the uninstaller is what is running when the
    app is gone, so removing it stays the installer's job."""
    assert "[UninstallDelete]" in ISS
    assert "Startup\\WeekNumber.lnk" in ISS


def test_the_installer_still_needs_administrator():
    # Not the same question as the app. It writes into Program Files.
    assert "PrivilegesRequired=admin" in ISS


def test_the_installer_clears_a_running_copy_before_replacing_it():
    """A tray app with no ordinary top-level window is invisible to the
    Restart Manager — measured on ShooApp, which registers 93 files and is
    told "no applications using one of our files". Something has to deal with
    the running copy, and here it is a taskkill in InitializeSetup."""
    assert "taskkill.exe" in ISS


def test_both_builds_stamp_a_version_resource():
    """Without it the exe has no version in its Properties at all, and
    `Get-Process` reports it blank."""
    for recipe in (BUILD, WORKFLOW):
        assert any(flag.startswith("--version-file=")
                   for flag in pyinstaller_flags(recipe))


def test_the_build_runs_the_tests_first():
    # A build that ships a broken app is worse than one that does not ship.
    assert "pytest" in BUILD
    assert "pytest" in WORKFLOW


def test_the_generated_files_are_not_committed():
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    for generated in ("installer-version.txt", "version_info.txt"):
        assert generated in gitignore
