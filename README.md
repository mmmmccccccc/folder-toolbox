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

## A real run

`docs/real-run.txt` holds one run of the four programs on the fixture folder, copied as it
was printed:

```
$ python -m files_toolbox delete demo/project
5 changes, 10 files left alone:

  delete    holiday-photo.jpg  ->  vault    not opened for 2.5 years   (high risk)
  delete    invoice-03.pdf  ->  vault       not opened for 2.0 years   (high risk)
  delete    old.zip  ->  vault              not opened for 1.0 years   (high risk)
  delete    report.bak  ->  vault           temporary file, 40 days old   (high risk)
  delete    setup.tmp  ->  vault            temporary file, 2 days old   (high risk)

done: 5 files moved to the vault, record delete_2026-11-25-2051.tbx
```

rename then tidied 4 names, move filed 9 files into Video, Documents, Photos and Archives,
and `restore --find invoice --number 1` put `invoice-03.pdf` back and wrote
`restore_2026-11-25-2051.tbx`. The records themselves are in `demo/project/`.

## The right-click menu

`python -m files_toolbox install-menu` writes four entries under
`HKEY_CURRENT_USER\Software\Classes\Directory\shell\folder-toolbox`, one per program,
each running it on the folder that was right-clicked. `--remove` takes them out again, and
`--dry-run` prints the four keys without writing anything. Nothing outside the current
user's account is touched and no administrator is needed. On an account that refuses the
write the command says so and the four programs still run from the command line, for
example `python -m files_toolbox delete DIR`.

## Who wrote what

The test cases and the code were generated with AI. The design, the running of the
tests, the documentation and the report are mine.

Two places where the generated code was wrong and the fix is mine:

1. The first delete moved a file into the vault and kept its old timestamp, so a file three
   years old was past the retention on the day it arrived and was erased at the next run.
   The file is now touched on the way in, and
   `test_delete_in_the_vault_starts_its_clock_at_the_deletion` holds that.
2. The first rename overwrote a file that already had the tidy name. It now steps to `_2`
   instead, and `test_rename_does_not_overwrite` holds that.
