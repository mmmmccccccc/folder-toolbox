"""The scan pass, the rules and the record files."""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from files_toolbox import record, rules, scan
from tests import make_fixtures


@pytest.fixture()
def demo(tmp_path):
    return make_fixtures.build(str(tmp_path / "project"))


def test_scan_skips_records_and_vault(demo):
    open(os.path.join(demo, "delete_2026-11-25-1900.tbx"), "w").close()
    os.makedirs(os.path.join(demo, "_vault"), exist_ok=True)
    open(os.path.join(demo, "_vault", "gone.jpg"), "wb").close()

    names = [f.rel for f in scan.scan(demo)]
    assert "delete_2026-11-25-1900.tbx" not in names
    assert not any(n.startswith("_vault") for n in names)
    assert "invoice-03.pdf" in names


def test_scan_is_not_recursive_by_default(demo):
    names = [f.rel for f in scan.scan(demo)]
    assert "already-here.jpg" not in names
    deep = [f.rel for f in scan.scan(demo, recursive=True)]
    assert any(n.endswith("already-here.jpg") for n in deep)


def test_delete_rule_takes_junk_and_stale(demo):
    by_name = {f.name: f for f in scan.scan(demo)}
    assert rules.decide_delete(by_name["setup.tmp"]).action == "delete"
    assert rules.decide_delete(by_name["old.zip"]).action == "delete"
    assert rules.decide_delete(by_name["notes.txt"]).action == "keep"
    assert "years" in rules.decide_delete(by_name["old.zip"]).reason


def test_rename_rule_tidies_copy_markers(demo):
    by_name = {f.name: f for f in scan.scan(demo)}
    assert rules.decide_rename(by_name["meeting notes (1).docx"]).target == "meeting-notes.docx"
    assert rules.decide_rename(by_name["  draft  copy.docx"]).target == "draft.docx"
    assert rules.decide_rename(by_name["notes.txt"]).action == "keep"


def test_move_rule_sorts_by_type(demo):
    by_name = {f.name: f for f in scan.scan(demo)}
    assert rules.decide_move(by_name["clip.mp4"]).target == "Video"
    assert rules.decide_move(by_name["notes.txt"]).target == "Documents"
    assert rules.decide_move(by_name["no-extension"]).action == "keep"


def test_record_roundtrip(demo):
    when = time.strptime("2026-11-25 19:00", "%Y-%m-%d %H:%M")
    entries = [record.Entry("delete", "old.zip", "_vault/old.zip")]
    path = record.write_record(demo, "delete", entries, when)
    assert os.path.basename(path) == "delete_2026-11-25-1900.tbx"
    assert record.read_record(path) == entries
    assert record.list_records(demo) == ["delete_2026-11-25-1900.tbx"]


def test_second_record_same_minute_gets_a_number(demo):
    when = time.strptime("2026-11-25 19:00", "%Y-%m-%d %H:%M")
    first = record.write_record(demo, "move", [], when)
    second = record.write_record(demo, "move", [], when)
    assert first != second
    assert os.path.basename(second).endswith("_2.tbx")
