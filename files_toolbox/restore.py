"""The restore program: read the records, show them newest first, put things back."""

from __future__ import annotations

import os
import shutil

from . import record, scan, ui


def records(folder: str, op: str | None = None) -> list[tuple[str, list[record.Entry]]]:
    out = []
    for name in record.list_records(folder, op):
        out.append((name, record.read_record(os.path.join(folder, name))))
    return out


def describe(name: str, entries: list[record.Entry]) -> str:
    kinds = {}
    for e in entries:
        kinds[e.action] = kinds.get(e.action, 0) + 1
    parts = ", ".join(f"{n} {k}" for k, n in sorted(kinds.items()))
    stamp = name.rsplit(".", 1)[0].replace("_", " ", 1)
    return f"{stamp:<28} {parts or 'empty'}"


def menu(items: list[tuple[str, list[record.Entry]]]) -> str:
    lines = ["records, newest first:", ""]
    for i, (name, entries) in enumerate(items, 1):
        lines.append(f"  {i}. {describe(name, entries)}")
    return "\n".join(lines)


def undo(folder: str, entries: list[record.Entry], out=print) -> int:
    """Put every line of the record back. A file that no longer exists is reported, not fatal."""
    done = 0
    for e in reversed(entries):
        src = os.path.join(folder, e.new.replace("/", os.sep))
        dst = os.path.join(folder, e.old.replace("/", os.sep))
        if not os.path.exists(src):
            out(f"  missing, skipped: {e.new}")
            continue
        os.makedirs(os.path.dirname(dst) or folder, exist_ok=True)
        if os.path.exists(dst):
            base, ext = os.path.splitext(dst)
            n = 2
            while os.path.exists(f"{base}_{n}{ext}"):
                n += 1
            dst = f"{base}_{n}{ext}"
        shutil.move(src, dst)
        done += 1
    return done


def run(folder: str, op: str | None = None, pick=0, confirm=ui.ask, dry_run: bool = False, out=print) -> str | None:
    items = records(folder, op)
    if not items:
        out("no records in this folder.")
        return None
    out(menu(items))
    if dry_run:
        return None
    if pick:
        index = pick
    else:
        try:
            index = int(input("number to restore (0 to stop): ").strip() or 0)
        except (ValueError, EOFError, KeyboardInterrupt):
            out("stopped: nothing was changed.")
            return None
    if not 1 <= index <= len(items):
        out("stopped: nothing was changed.")
        return None

    name, entries = items[index - 1]
    out("")
    for e in entries:
        out(f"  {e.action:<8} {e.new}  ->  {e.old}")
    out("")
    if not confirm():
        out("stopped: nothing was changed.")
        return None

    done = undo(folder, entries, out)
    path = record.write_record(folder, "restore", entries)
    out(f"done: {done} of {len(entries)} back, record {os.path.basename(path)}")
    return path
