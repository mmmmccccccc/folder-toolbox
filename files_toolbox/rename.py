"""The rename program: names that carry copy markers or double spaces get tidied."""

from __future__ import annotations

import os

from . import record, rules, scan, ui
from .delete import _prune_records
from .settings import Settings


def plan(folder: str) -> list[tuple[scan.FileInfo, rules.Action]]:
    return [(f, rules.decide_rename(f)) for f in scan.scan(folder)]


def free_path(path: str) -> str:
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(f"{base}_{n}{ext}"):
        n += 1
    return f"{base}_{n}{ext}"


def run(folder: str, confirm=ui.ask, dry_run: bool = False, out=print) -> str | None:
    settings = Settings.load()
    rows = plan(folder)
    out(ui.render(rows, folder))
    changes = [(f, a) for f, a in rows if a.action != "keep"]
    if not changes:
        return None
    if dry_run:
        out("dry run: nothing was changed.")
        return None
    if not confirm():
        out("stopped: nothing was changed.")
        return None

    entries = []
    for f, a in changes:
        dest = free_path(os.path.join(os.path.dirname(f.path), a.target))
        os.rename(f.path, dest)
        entries.append(record.Entry("rename", f.rel, os.path.basename(dest)))

    path = record.write_record(folder, "name", entries)
    _prune_records(folder, settings)
    out(f"done: {len(entries)} files renamed, record {os.path.basename(path)}")
    return path
