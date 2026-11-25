"""The records: one plain-text file per run, named after the operation and the time."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from .scan import RECORD_EXT


@dataclass(frozen=True)
class Entry:
    action: str        # delete | rename | move | restore
    old: str           # path inside the folder before the run
    new: str           # new path, or the vault path for a delete
    note: str = ""


def record_name(folder: str, op: str, when: time.struct_time | None = None) -> str:
    when = when or time.localtime()
    stamp = time.strftime("%Y-%m-%d-%H%M", when)
    name = f"{op}_{stamp}{RECORD_EXT}"
    path = os.path.join(folder, name)
    n = 2
    while os.path.exists(path):
        path = os.path.join(folder, f"{op}_{stamp}_{n}{RECORD_EXT}")
        n += 1
    return path


def write_record(folder: str, op: str, entries: list[Entry], when: time.struct_time | None = None) -> str:
    when = when or time.localtime()
    path = record_name(folder, op, when)
    lines = [
        f"# {op} {time.strftime('%Y-%m-%d %H:%M', when)}",
        "# every line: action, path before, path after",
    ]
    for e in entries:
        line = f"{e.action}\t{e.old}\t{e.new}"
        if e.note:
            line += f"\t{e.note}"
        lines.append(line)
    tmp = path + ".writing"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    os.replace(tmp, path)          # a half-written record never appears
    return path


def read_record(path: str) -> list[Entry]:
    out: list[Entry] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            out.append(Entry(parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else ""))
    return out


def list_records(folder: str, op: str | None = None) -> list[str]:
    """Records newest first, filtered by operation when ``op`` is given."""
    names = [n for n in os.listdir(folder) if n.lower().endswith(RECORD_EXT)]
    if op:
        names = [n for n in names if n.startswith(op + "_")]
    return sorted(names, reverse=True)
