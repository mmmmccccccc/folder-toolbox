"""Build a folder of test files with known names, types and timestamps.

The point is to have input the rules can be checked against: junk extensions, files
that are years old, copy markers in names, non-ASCII names, and every type the move
rule knows about.
"""

from __future__ import annotations

import os
import shutil
import time

DEMO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo", "project")

DAYS = 86400.0


def years_ago(y: float) -> float:
    return time.time() - y * 365 * DAYS


def days_ago(d: float) -> float:
    return time.time() - d * DAYS


# (name, size in bytes, mtime, atime)
FILES = [
    # stale: older than a year
    ("holiday-photo.jpg", 120_000, years_ago(3), years_ago(2.5)),
    ("invoice-03.pdf", 40_000, years_ago(2), years_ago(2)),
    ("old.zip", 2_000_000, years_ago(4), years_ago(1)),
    # junk extension, only a month old
    ("setup.tmp", 1_000, days_ago(2), days_ago(2)),
    ("report.bak", 3_000, days_ago(40), days_ago(40)),
    # names the rename rule should tidy
    ("meeting notes (1).docx", 8_000, days_ago(10), days_ago(10)),
    ("  draft  copy.docx", 8_000, days_ago(10), days_ago(10)),
    ("screen shot 2025.png", 90_000, days_ago(5), days_ago(5)),
    # types the move rule knows
    ("clip.mp4", 5_000_000, days_ago(20), days_ago(20)),
    ("archive.7z", 700_000, days_ago(30), days_ago(30)),
    ("notes.txt", 500, days_ago(3), days_ago(3)),
    # names and encodings worth keeping
    ("reading-notes.md", 700, days_ago(9), days_ago(9)),
    ("naïve café.txt", 400, days_ago(9), days_ago(9)),
    ("no-extension", 120, days_ago(60), days_ago(60)),
    ("UPPER.TXT", 200, days_ago(60), days_ago(60)),
    # already where the move rule wants it
    ("Photos/already-here.jpg", 50_000, days_ago(15), days_ago(15)),
]


def build(target: str = DEMO, wipe: bool = True) -> str:
    if wipe and os.path.isdir(target):
        shutil.rmtree(target)
    os.makedirs(target, exist_ok=True)
    for name, size, mtime, atime in FILES:
        path = os.path.join(target, *name.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(b"x" * size)
        os.utime(path, (atime, mtime))
    return target


if __name__ == "__main__":
    where = build()
    print("built", where, "with", len(FILES), "files")
