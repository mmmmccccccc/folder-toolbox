"""The delete program: stale and temporary files leave the folder, but they are not erased."""

from __future__ import annotations

import os
import shutil

from . import record, rules, scan, ui
from .settings import Settings
from .scan import FileInfo


def free_name(folder: str, name: str) -> str:
    """A name inside the vault that is not taken yet."""
    base, ext = os.path.splitext(name)
    target = os.path.join(folder, name)
    n = 2
    while os.path.exists(target):
        target = os.path.join(folder, f"{base}_{n}{ext}")
        n += 1
    return target


def prune_vault(folder: str, settings: Settings) -> int:
    """Remove vault files older than the retention the user set."""
    import time
    vault = scan.vault_path(folder)
    if not os.path.isdir(vault):
        return 0
    limit = time.time() - settings.vault_days * 86400
    gone = 0
    for root, _dirs, files in os.walk(vault):
        for name in files:
            full = os.path.join(root, name)
            if os.stat(full).st_mtime < limit:
                os.remove(full)
                gone += 1
    return gone


def plan(folder: str) -> list[tuple[FileInfo, rules.Action]]:
    return [(f, rules.decide_delete(f)) for f in scan.scan(folder)]


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

    vault = scan.vault_path(folder)
    os.makedirs(vault, exist_ok=True)
    entries = []
    for f, _a in changes:
        dest = free_name(vault, f.name)
        shutil.move(f.path, dest)
        os.utime(dest, None)      # the vault counts from the day of the deletion, not from the file
        entries.append(record.Entry("delete", f.rel, os.path.join(scan.VAULT_NAME, os.path.basename(dest))))

    path = record.write_record(folder, "delete", entries)
    _prune_records(folder, settings)
    prune_vault(folder, settings)
    out(f"done: {len(entries)} files moved to the vault, record {os.path.basename(path)}")
    return path


def _prune_records(folder: str, settings: Settings) -> None:
    for op in ("delete", "name", "move"):
        names = record.list_records(folder, op)
        for old in names[settings.records_per_type:]:
            try:
                os.remove(os.path.join(folder, old))
            except OSError:
                pass
