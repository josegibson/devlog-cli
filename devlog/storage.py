from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Type, TypeVar

import yaml

from .models import Aim, Arch, Brief, Call, Constraint, Debt, HasText, Milestone, Note, Shift, Snag

T = TypeVar("T")

DEVLOG_DIR = ".devlog"

_FILE_MAP: dict[type, str] = {
    Note:       "notes.yaml",
    Call:       "calls.yaml",
    Snag:       "snags.yaml",
    Shift:      "shifts.yaml",
    Debt:       "debt.yaml",
    Arch:       "arch.yaml",
    Constraint: "constraints.yaml",
    Brief:      "briefs.yaml",
    Aim:        "aims.yaml",
    Milestone:  "milestones.yaml",
}


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def find_devlog_dir(start: Optional[Path] = None) -> Path:
    root = (start or Path.cwd()).resolve()
    for path in [root, *root.parents]:
        candidate = path / DEVLOG_DIR
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "No .devlog/ directory found. Run 'devlog init' first."
    )


def find_git_root(devlog_dir: Path) -> Optional[Path]:
    for path in [devlog_dir.parent, *devlog_dir.parent.parents]:
        if (path / ".git").is_dir():
            return path
    return None


def init_devlog(project_path: Optional[Path] = None) -> Path:
    root = (project_path or Path.cwd()).resolve()
    devlog_dir = root / DEVLOG_DIR
    devlog_dir.mkdir(exist_ok=True)
    return devlog_dir


# ---------------------------------------------------------------------------
# YAML read / write
# ---------------------------------------------------------------------------

def _load_file(path: Path) -> list:
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text())
    return raw if isinstance(raw, list) else []


def _dump_file(path: Path, data: list) -> None:
    path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False))


def read_all(model_cls: Type[T], devlog_dir: Optional[Path] = None) -> List[T]:
    d = devlog_dir or find_devlog_dir()
    path = d / _FILE_MAP[model_cls]
    raw = _load_file(path)
    return [model_cls.model_validate(item) for item in raw]


def write_all(model_cls: Type[T], entries: List[T], devlog_dir: Optional[Path] = None) -> None:
    d = devlog_dir or find_devlog_dir()
    path = d / _FILE_MAP[model_cls]
    data = [e.model_dump(by_alias=True, exclude_none=True) for e in entries]
    _dump_file(path, data)


def append_entry(entry: T, devlog_dir: Optional[Path] = None) -> None:
    d = devlog_dir or find_devlog_dir()
    entries = read_all(type(entry), d)
    entries.append(entry)
    write_all(type(entry), entries, d)
    summary = getattr(entry, "text", None) or getattr(entry, "situation", "")
    log_event(d, f"{type(entry).__name__.lower()}.create", entry.id, summary)


def update_entry(
    model_cls: Type[T],
    entry_id: str,
    mutate: Callable[[T], None],
    devlog_dir: Optional[Path] = None,
) -> bool:
    entries = read_all(model_cls, devlog_dir)
    for entry in entries:
        if entry.id == entry_id:
            mutate(entry)
            write_all(model_cls, entries, devlog_dir)
            return True
    return False


def find_entry_by_text(
    model_cls: Type[T],
    search: str,
    devlog_dir: Optional[Path] = None,
) -> Optional[T]:
    """Case-insensitive text match. T must have a .text: str attribute (see HasText)."""
    entries = read_all(model_cls, devlog_dir)
    search_lower = search.lower()
    for entry in entries:
        entry_text: str = getattr(entry, "text", "")
        if search_lower in entry_text.lower():
            return entry
    return None


# ---------------------------------------------------------------------------
# Event log  (.devlog/events.jsonl)
# ---------------------------------------------------------------------------

def log_event(devlog_dir: Path, op: str, entry_id: str, summary: str = "") -> None:
    """Append one event line to events.jsonl — the internal temporal record."""
    events_path = devlog_dir / "events.jsonl"
    event: dict = {"ts": datetime.now().isoformat(timespec="seconds"), "op": op, "id": entry_id}
    if summary:
        event["summary"] = summary[:100]
    with events_path.open("a") as f:
        f.write(json.dumps(event) + "\n")


def read_events(devlog_dir: Path, last_n: Optional[int] = None) -> list[dict]:
    """Read events.jsonl, optionally returning only the last N entries."""
    events_path = devlog_dir / "events.jsonl"
    if not events_path.exists():
        return []
    lines = [l for l in events_path.read_text().splitlines() if l.strip()]
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return events[-last_n:] if last_n else events


# ---------------------------------------------------------------------------
# Uncommitted state detection
# ---------------------------------------------------------------------------

def uncommitted_devlog_files(devlog_dir: Path) -> list[str]:
    """Return list of .devlog/ files that are modified but not committed."""
    repo_root = find_git_root(devlog_dir)
    if not repo_root:
        return []
    try:
        rel = devlog_dir.relative_to(repo_root)
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain", str(rel)],
            capture_output=True, text=True, check=True,
        )
        return [l.strip() for l in result.stdout.splitlines() if l.strip()]
    except subprocess.CalledProcessError:
        return []
