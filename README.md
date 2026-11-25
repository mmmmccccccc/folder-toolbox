# folder-toolbox

A small toolbox for Windows folders. It sits on the right-click menu of a folder and
offers three programs — **delete**, **rename**, **move** — plus **restore** and
**settings**. Every program works on the folder the user picked, shows the changes it is
about to make, and waits for `y` before it touches a single file.

Coursework for *Intelligent Interactive Systems* (University of Birmingham, 2026/27).

## Why it exists

Deleting, renaming and moving files by hand is slow, and Windows Explorer keeps no
record of where a file went. This toolbox does one pass over a folder, writes down what
it did, and lets the user undo it later without a backup tool and without git.

## How it works

1. `scan` — one pass over the folder. Files ending in `.tbx` are skipped, because those
   are the toolbox's own records.
2. `list` — one line per file: what will happen, why, and how hard it is to undo.
3. `y / n` — the changes are shown before anything is touched. `n`, or an empty answer,
   leaves the folder exactly as it was.
4. `apply` — the change happens, and one line is written to a record file.
5. `restore` — reads the records, lists them newest first, and puts the old name or the
   old path back.

Records are plain text with a different extension: `delete_2026-11-25-1900.tbx`,
`name_2026-11-25-1901.tbx`, `move_2026-11-25-1902.tbx`. They can be opened in any text
editor and read without this tool.

Deleted files are not erased. They go to the vault, and `restore` brings them back to
the path recorded in the `.tbx` file.

## Install

```
python -m pip install -e .
```

or run it from the checkout:

```
python -m files_toolbox delete "C:\Users\me\Desktop\project"
```

## Use

```
python -m files_toolbox delete  DIR      # move stale files to the vault
python -m files_toolbox rename  DIR      # tidy names by type
python -m files_toolbox move    DIR      # file by type into subfolders
python -m files_toolbox restore DIR      # read the records and put things back
python -m files_toolbox settings         # vault days, records per type
```

Nothing is written until `y`. `--dry-run` prints the list and stops there.

## Layout

```
files_toolbox/
  scan.py       one pass over a folder
  rules.py      which file gets which action, and why
  ui.py         the change list and the y/n question
  record.py     read and write the .tbx files
  settings.py   vault days, records per type
  delete.py     delete to the vault
  rename.py     rename by type
  move.py       move by type
  restore.py    read the records, put things back
  cli.py        the entry point
tests/
  make_fixtures.py   builds a folder with known files and known timestamps
  test_*.py
```

## Tests

```
python tests/make_fixtures.py
python -m pytest -q
```

The fixture folder contains files of several types, names with spaces and non-ASCII
characters, and timestamps set by hand, so the rules can be checked against known input.

## Notes

- Windows only (the right-click menu is a Windows feature). The programs themselves are
  plain Python and run anywhere for testing.
- No network access, no telemetry, no API keys.
