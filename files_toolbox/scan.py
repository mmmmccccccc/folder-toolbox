"""One pass over a folder: what is in it, and when it was last touched."""

from __future__ import annotations

import os
from dataclasses import dataclass

RECORD_EXT = ".tbx"
VAULT_NAME = "_vault"


@dataclass(frozen=True)
class FileInfo:
    path: str          # full path
    rel: str           # path inside the folder, used in the list and in the record
    name: str
    ext: str           # lower-case, with the dot, or "" when there is none
    size: int
    mtime: float
    atime: float

    @property
    def days_since_used(self) -> float:
        return (_now() - max(self.mtime, self.atime)) / 86400


def _now() -> float:
    # kept as a function so the tests can freeze it
    import time
    return time.time()


def scan(folder: str, recursive: bool = False) -> list[FileInfo]:
    """Return the files of ``folder``.

    The toolbox's own records (``*.tbx``) and the vault are skipped: a record is not a
    file to clean up, and the vault is where deleted files wait.
    """
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        raise NotADirectoryError(folder)

    out: list[FileInfo] = []
    walker = os.walk(folder) if recursive else [(folder, [], os.listdir(folder))]
    for root, dirs, files in walker:
        dirs[:] = [x for x in dirs if x != VAULT_NAME]
        for name in files:
            if name.lower().endswith(RECORD_EXT):
                continue
            full = os.path.join(root, name)
            if not os.path.isfile(full):
                continue
            st = os.stat(full)
            out.append(FileInfo(
                path=full,
                rel=os.path.relpath(full, folder),
                name=name,
                ext=os.path.splitext(name)[1].lower(),
                size=st.st_size,
                mtime=st.st_mtime,
                atime=st.st_atime,
            ))
    out.sort(key=lambda f: f.rel.lower())
    return out


def vault_path(folder: str) -> str:
    return os.path.join(os.path.abspath(folder), VAULT_NAME)
