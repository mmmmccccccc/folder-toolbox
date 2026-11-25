"""Entry point: one subcommand per program, the same shape for all of them."""

from __future__ import annotations

import argparse
import sys

from . import delete, restore, scan, ui
from .settings import Settings


def _confirm(args):
    if args.yes:
        return lambda: True
    return ui.ask


def cmd_delete(args) -> int:
    folder = args.folder
    path = delete.run(folder, confirm=_confirm(args), dry_run=args.dry_run)
    return 0 if path or args.dry_run else 1


def cmd_restore(args) -> int:
    path = restore.run(args.folder, op=args.type, pick=args.number,
                       confirm=_confirm(args), dry_run=args.dry_run)
    return 0 if path or args.dry_run else 1


def cmd_settings(args) -> int:
    s = Settings.load()
    if args.vault_days is not None:
        s.vault_days = args.vault_days
    if args.records is not None:
        s.records_per_type = args.records
    where = s.save()
    print(f"vault keeps a file for {s.vault_days} days")
    print(f"{s.records_per_type} records of each operation stay in the folder")
    print(f"saved in {where}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="folder-toolbox", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("delete", help="move stale and temporary files to the vault")
    d.add_argument("folder")
    d.add_argument("--dry-run", action="store_true", help="show the changes and stop")
    d.add_argument("-y", "--yes", action="store_true", help="skip the question")
    d.set_defaults(func=cmd_delete)

    r = sub.add_parser("restore", help="read the records and put things back")
    r.add_argument("folder")
    r.add_argument("--type", choices=["delete", "name", "move", "restore"], default=None)
    r.add_argument("--number", type=int, default=0, help="which record, 1 is the newest")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("-y", "--yes", action="store_true")
    r.set_defaults(func=cmd_restore)

    s = sub.add_parser("settings", help="vault days and records per operation")
    s.add_argument("--vault-days", type=int, default=None)
    s.add_argument("--records", type=int, default=None)
    s.set_defaults(func=cmd_settings)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scan.scan(args.folder) if hasattr(args, "folder") else None
    except NotADirectoryError as e:
        print(f"not a folder: {e}")
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
