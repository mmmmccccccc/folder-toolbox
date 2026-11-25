"""The three programs and the restore, run against the fixture folder."""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from files_toolbox import delete, move, record, rename, restore, rules, scan, ui
from files_toolbox.settings import Settings
from tests import make_fixtures


@pytest.fixture()
def demo(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("APPDATA", str(home))
    return make_fixtures.build(str(tmp_path / "project"))


def yes():
    return True


def no():
    return False


quiet = (lambda *a, **k: None)


# ---------------------------------------------------------------- delete
def test_delete_moves_to_vault_and_writes_a_record(demo):
    before = {f.rel for f in scan.scan(demo)}
    path = delete.run(demo, confirm=yes, out=quiet)
    after = {f.rel for f in scan.scan(demo)}

    assert os.path.basename(path).startswith("delete_")
    assert "old.zip" in before and "old.zip" not in after
    assert os.path.exists(os.path.join(demo, "_vault", "old.zip"))
    entries = record.read_record(path)
    assert ("delete", "old.zip", os.path.join("_vault", "old.zip")) in [(e.action, e.old, e.new) for e in entries]


def test_delete_rechecks_nothing_when_the_answer_is_n(demo):
    before = sorted(os.listdir(demo))
    assert delete.run(demo, confirm=no, out=quiet) is None
    assert sorted(os.listdir(demo)) == before


def test_delete_in_the_vault_starts_its_clock_at_the_deletion(demo):
    delete.run(demo, confirm=yes, out=quiet)
    vaulted = os.path.join(demo, "_vault", "old.zip")
    assert time.time() - os.stat(vaulted).st_mtime < 60


def test_dry_run_changes_nothing(demo):
    before = sorted(os.listdir(demo))
    delete.run(demo, confirm=yes, dry_run=True, out=quiet)
    assert sorted(os.listdir(demo)) == before


def test_vault_is_pruned_by_the_setting(demo, monkeypatch):
    monkeypatch.setenv("APPDATA", os.path.join(demo, "..", "home2"))
    Settings(vault_days=7, records_per_type=10).save()
    delete.run(demo, confirm=yes, out=quiet)
    vault = os.path.join(demo, "_vault")
    old = os.path.join(vault, "ancient.jpg")
    open(old, "wb").write(b"x")
    os.utime(old, (time.time() - 30 * 86400,) * 2)

    delete.run(demo, confirm=yes, out=quiet)
    assert not os.path.exists(old)


# ---------------------------------------------------------------- rename
def test_rename_tidies_names_and_keeps_the_old_one_in_the_record(demo):
    path = rename.run(demo, confirm=yes, out=quiet)
    names = os.listdir(demo)
    assert "meeting-notes.docx" in names
    assert os.path.basename(path).startswith("name_")
    entries = record.read_record(path)
    assert ("rename", "meeting notes (1).docx", "meeting-notes.docx") in [(e.action, e.old, e.new) for e in entries]


def test_rename_does_not_overwrite(demo):
    open(os.path.join(demo, "draft.docx"), "wb").write(b"already here")
    rename.run(demo, confirm=yes, out=quiet)
    assert "draft.docx" in os.listdir(demo)
    assert "draft_2.docx" in os.listdir(demo)


# ---------------------------------------------------------------- move
def test_move_files_by_type_and_back(demo):
    path = move.run(demo, confirm=yes, out=quiet)
    assert os.path.exists(os.path.join(demo, "Video", "clip.mp4"))
    assert os.path.exists(os.path.join(demo, "Documents", "notes.txt"))
    assert os.path.basename(path).startswith("move_")

    moved = len(record.read_record(path))
    assert restore.undo(demo, record.read_record(path), quiet) == moved
    assert os.path.exists(os.path.join(demo, "clip.mp4"))
    assert not os.path.exists(os.path.join(demo, "Video", "clip.mp4"))


def test_a_file_already_in_its_folder_is_left_alone(demo):
    # the folder of a run is the top level, so a photo inside Photos/ is not in the plan at
    # all; when the same file is offered to the rule, the rule keeps it where it is
    assert "Photos/already-here.jpg" not in dict((f.rel, a) for f, a in move.plan(demo))
    deep = [f for f in scan.scan(demo, recursive=True) if f.rel.endswith("already-here.jpg")]
    assert deep, "the fixture should hold a photo inside Photos/"
    assert rules.decide_move(deep[0]).action == "keep"


# ---------------------------------------------------------------- restore
def test_restore_puts_a_deleted_file_back(demo):
    delete.run(demo, confirm=yes, out=quiet)
    restore.run(demo, op="delete", pick=1, confirm=yes, out=quiet)
    assert os.path.exists(os.path.join(demo, "old.zip"))
    assert not os.path.exists(os.path.join(demo, "_vault", "old.zip"))


def test_restore_stops_on_n(demo):
    delete.run(demo, confirm=yes, out=quiet)
    restore.run(demo, op="delete", pick=1, confirm=no, out=quiet)
    assert os.path.exists(os.path.join(demo, "_vault", "old.zip"))
    assert not os.path.exists(os.path.join(demo, "old.zip"))


def test_restore_lists_newest_first(demo):
    delete.run(demo, confirm=yes, out=quiet)
    move.run(demo, confirm=yes, out=quiet)
    items = restore.records(demo)
    assert items[0][0].startswith("move_")


# ---------------------------------------------------------------- the question
def test_only_y_goes_ahead(monkeypatch):
    for answer, expected in [("y", True), ("Y", True), ("yes", True),
                             ("n", False), ("", False), ("  ", False), ("ok", False)]:
        monkeypatch.setattr("builtins.input", lambda _p=None, a=answer: a)
        assert ui.ask() is expected, answer


def test_closed_input_stops(monkeypatch):
    def boom(_p=None):
        raise EOFError
    monkeypatch.setattr("builtins.input", boom)
    assert ui.ask() is False
