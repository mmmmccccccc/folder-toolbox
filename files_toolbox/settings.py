"""Two numbers the user can change: how long the vault keeps files, and how many records stay."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict

DEFAULTS = {"vault_days": 7, "records_per_type": 10}


def settings_path() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "folder-toolbox", "settings.json")


@dataclass
class Settings:
    vault_days: int = DEFAULTS["vault_days"]
    records_per_type: int = DEFAULTS["records_per_type"]

    @classmethod
    def load(cls) -> "Settings":
        path = settings_path()
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            return cls()
        known = {k: data[k] for k in DEFAULTS if isinstance(data.get(k), int)}
        return cls(**known)

    def save(self) -> str:
        path = settings_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)
        return path
