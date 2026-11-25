"""Put the four programs on the right-click menu of a folder.

The entries are written under HKEY_CURRENT_USER, so nothing outside this user's account is
touched and nothing needs an administrator. Each entry runs one program on the folder that
was right-clicked (%1). ``install(dry_run=True)`` returns the entries without writing them.
"""

from __future__ import annotations

import os
import shutil
import sys

PROGRAMS = [
    ("delete", "Delete stale files to the vault", "delete"),
    ("rename", "Tidy names that carry copy markers", "rename"),
    ("move", "File by type into subfolders", "move"),
    ("restore", "Restore from a record", "restore"),
]

ROOT = r"Software\Classes\Directory\shell\folder-toolbox"


def _pythonw() -> str:
    exe = sys.executable or "python"
    guess = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return guess if os.path.exists(guess) else exe


def entries() -> list[tuple[str, str, str]]:
    """(key, label, command) for the parent entry and the four programs."""
    exe = _pythonw()
    out = [(ROOT, "folder-toolbox", "")]
    for name, label, program in PROGRAMS:
        out.append((ROOT + "\\shell\\" + name, label, f'"{exe}" -m files_toolbox {program} "%1"'))
    return out


def _pkg_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def install(dry_run: bool = False, out=print) -> int:
    import winreg

    rows = entries()
    if dry_run:
        for key, label, command in rows:
            out(f"{key}  |  {label}  |  {command}")
        return len(rows)

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, ROOT) as key:
        winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "folder-toolbox")
        winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "imageres.dll,-5302")
    for key, label, command in rows[1:]:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as sub:
            winreg.SetValueEx(sub, "MUIVerb", 0, winreg.REG_SZ, label)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key + "\\command") as cmd:
            winreg.SetValueEx(cmd, "", 0, winreg.REG_SZ, command)
    out(f"installed: right-click a folder, then folder-toolbox ({len(rows) - 1} entries)")
    return len(rows)


def remove(dry_run: bool = False, out=print) -> int:
    import winreg

    if dry_run:
        out(f"would delete HKEY_CURRENT_USER\\{ROOT}")
        return 1

    def drop(path: str) -> None:
        for name, _label, _command in PROGRAMS:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path + "\\shell\\" + name + "\\command")
            except OSError:
                pass
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path + "\\shell\\" + name)
            except OSError:
                pass
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        except OSError:
            pass

    drop(ROOT)
    out("removed from the right-click menu")
    return 0
