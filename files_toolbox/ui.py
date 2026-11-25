"""What the user sees before anything is touched: the changes, then one question."""

from __future__ import annotations

from .scan import FileInfo
from .rules import Action


def line_for(f: FileInfo, a: Action) -> str:
    if a.action == "keep":
        return ""
    if a.action == "delete":
        what = f"delete    {f.rel}  ->  vault"
    elif a.action == "rename":
        what = f"rename    {f.rel}  ->  {a.target}"
    elif a.action == "move":
        what = f"move      {f.rel}  ->  {a.target}/"
    else:
        what = f"{a.action}  {f.rel}"
    return f"{what:<58} {a.reason}   ({a.risk} risk)"


def render(rows: list[tuple[FileInfo, Action]], folder: str) -> str:
    changes = [(f, a) for f, a in rows if a.action != "keep"]
    kept = len(rows) - len(changes)
    out = [f"folder: {folder}", ""]
    if not changes:
        out.append("nothing to change in this folder.")
        return "\n".join(out)
    out.append(f"{len(changes)} changes, {kept} files left alone:")
    out.append("")
    for f, a in changes:
        out.append("  " + line_for(f, a))
    out.append("")
    out.append("risk = how hard the change is to undo.")
    return "\n".join(out)


def ask(prompt: str = "type y to go ahead, n to stop: ") -> bool:
    """Only an explicit y goes ahead. An empty answer, a closed stdin or ^C stops."""
    try:
        answer = input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer.strip().lower() in {"y", "yes"}
