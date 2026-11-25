"""The move program: files go into one subfolder per type."""

from __future__ import annotations

import os
import shutil

from . import record, rules, scan, ui
from .delete import _prune_records
from .rename import free_path
from .settings import Settings


def plan(folder: str) -> list[tuple[scan.FileInfo, rules.Action]]:
    return [(f, rules.decide_move(f)) for f in scan.scan(folder)]


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
        target_dir = os.path.join(folder, a.target)
        os.makedirs(target_dir, exist_ok=True)
        dest = free_path(os.path.join(target_dir, f.name))
        shutil.move(f.path, dest)
        entries.append(record.Entry("move", f.rel, os.path.join(a.target, os.path.basename(dest))))

    path = record.write_record(folder, "move", entries)
    _prune_records(folder, settings)
    out(f"done: {len(entries)} files moved, record {os.path.basename(path)}")
    return path
