"""Which file gets which action, and the reason shown in the list."""

from __future__ import annotations

from dataclasses import dataclass

from .scan import FileInfo

JUNK_EXT = {".tmp", ".bak", ".crdownload", ".part"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".gif", ".psd", ".raw"}
DOC_EXT = {".docx", ".doc", ".pdf", ".txt", ".md", ".pptx", ".xlsx"}
ARCHIVE_EXT = {".zip", ".7z", ".rar", ".tar", ".gz"}

OLD_DAYS = 365
JUNK_DAYS = 30


@dataclass(frozen=True)
class Action:
    action: str        # "delete" | "rename" | "move" | "keep"
    target: str        # new name, or the subfolder, or "" for keep
    reason: str
    risk: str          # how hard the change is to undo: "none" | "low" | "high"


KEEP = Action("keep", "", "", "none")


def _age_days(f: FileInfo) -> float:
    return f.days_since_used


# ---------------------------------------------------------------- delete
def decide_delete(f: FileInfo) -> Action:
    age = _age_days(f)
    if f.ext in JUNK_EXT:
        return Action("delete", "", f"temporary file, {age:.0f} days old", "high")
    if age >= OLD_DAYS:
        return Action("delete", "", f"not opened for {age / 365:.1f} years", "high")
    return KEEP


# ---------------------------------------------------------------- rename
def clean_name(name: str) -> str:
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    stem = stem.strip().replace("  ", " ")
    for junk in ("(1)", "(2)", " copy", " - Copy"):
        stem = stem.replace(junk, "")
    stem = stem.strip().replace(" ", "-")
    stem = "".join(ch for ch in stem if ch.isprintable())
    while "--" in stem:
        stem = stem.replace("--", "-")
    return (stem or "file") + ("." + ext if ext else "")


def decide_rename(f: FileInfo) -> Action:
    new = clean_name(f.name)
    if new == f.name:
        return KEEP
    return Action("rename", new, "name has a copy marker, a double space or a trailing space", "low")


# ---------------------------------------------------------------- move
def folder_for(ext: str) -> str:
    if ext in PHOTO_EXT:
        return "Photos"
    if ext in VIDEO_EXT:
        return "Video"
    if ext in DOC_EXT:
        return "Documents"
    if ext in ARCHIVE_EXT:
        return "Archives"
    return ""


def decide_move(f: FileInfo) -> Action:
    target = folder_for(f.ext)
    if not target:
        return KEEP
    head = f.rel.split("\\")[0].split("/")[0]
    if head == target:
        return KEEP
    return Action("move", target, f"{f.ext} belongs with the other {target.lower()}", "low")
