"""The version, and the two places that have to agree about it."""

import re

import pytest

import stamp_version
import version


def test_the_version_is_spelled_the_same_everywhere():
    """`version.py` and `installer.iss`, and on a release build the git tag.

    This is the test the project did not have. `installer.iss` said 1.0.0 from
    the first commit to the last, because it was the only copy and nothing
    compared it to anything.
    """
    declared = stamp_version.declared_versions()
    assert len(set(declared.values())) == 1, declared


def test_the_version_is_three_numbers():
    assert re.fullmatch(r"\d+\.\d+\.\d+", version.VERSION)


def test_a_release_is_its_version_and_nothing_else(monkeypatch):
    monkeypatch.setattr(version, "BUILD", 0)
    assert version.short() == version.VERSION


def test_an_internal_build_says_which_one_it_is(monkeypatch):
    monkeypatch.setattr(version, "BUILD", 7)
    assert version.short() == f"{version.VERSION}.7"


def test_the_full_line_owns_up_to_running_from_source(monkeypatch):
    monkeypatch.setattr(version, "is_frozen", lambda: False)
    assert "running from source" in version.full()


def test_the_full_line_leaves_out_a_commit_nobody_stamped(monkeypatch):
    monkeypatch.setattr(version, "COMMIT", "dev")
    assert "commit" not in version.full()


def test_the_full_line_carries_the_commit_once_it_is_stamped(monkeypatch):
    monkeypatch.setattr(version, "COMMIT", "abc1234")
    assert "commit abc1234" in version.full()


# ---------------------------------------------------------------------------
# The build counter
# ---------------------------------------------------------------------------

def test_the_build_number_restarts_when_the_release_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(stamp_version, "COUNTER", tmp_path / ".build-number")
    assert stamp_version.next_build("1.1.0", release=False) == 1
    assert stamp_version.next_build("1.1.0", release=False) == 2
    # A new release starts again, so 1.2.0's builds do not carry on from
    # 1.1.0's.
    assert stamp_version.next_build("1.2.0", release=False) == 1


def test_a_tagged_release_has_no_build_number(tmp_path, monkeypatch):
    monkeypatch.setattr(stamp_version, "COUNTER", tmp_path / ".build-number")
    assert stamp_version.next_build("1.1.0", release=True) == 0


def test_an_unreadable_counter_starts_again_rather_than_raising(
        tmp_path, monkeypatch):
    counter = tmp_path / ".build-number"
    counter.write_text("this is not a count", encoding="utf-8")
    monkeypatch.setattr(stamp_version, "COUNTER", counter)
    assert stamp_version.next_build("1.1.0", release=False) == 1


# ---------------------------------------------------------------------------
# The version resource Windows itself reads
# ---------------------------------------------------------------------------

def test_the_resource_carries_the_release_in_both_shapes():
    text = stamp_version.version_resource("1.1.0", build=0)
    assert "filevers=(1, 1, 0, 0)" in text
    assert "StringStruct('FileVersion', '1.1.0')" in text


def test_an_internal_build_says_so_in_the_resource():
    text = stamp_version.version_resource("1.1.0", build=7)
    assert "filevers=(1, 1, 0, 7)" in text
    assert "StringStruct('FileVersion', '1.1.0.7')" in text


def test_the_resource_names_the_file_it_will_be_stamped_into():
    text = stamp_version.version_resource("1.1.0", build=0)
    assert "StringStruct('OriginalFilename', 'WeekNumber.exe')" in text


def test_a_version_that_is_not_three_numbers_does_not_produce_a_resource():
    with pytest.raises(ValueError):
        stamp_version.version_resource("nightly", build=0)


def test_the_resource_is_valid_python():
    # PyInstaller eval's it, so a missing comma is a build failure rather than
    # a mis-stamped exe. Checked here instead of there.
    compile(stamp_version.version_resource("1.1.0", build=2),
            "version_info.txt", "exec")
