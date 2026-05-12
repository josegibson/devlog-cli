from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Type, TypeVar

import yaml

from .models import Aim, Arch, Brief, Call, Constraint, Debt, Milestone, Note, Shift, Snag

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
    """Walk up from start (or cwd) to find .devlog/."""
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
    """Create .devlog/ and return its path."""
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
    entries = read_all(type(entry), devlog_dir)
    entries.append(entry)
    write_all(type(entry), entries, devlog_dir)


def update_entry(
    model_cls: Type[T],
    entry_id: str,
    mutate: Callable[[T], None],
    devlog_dir: Optional[Path] = None,
) -> bool:
    """Find entry by id, apply mutate(), save. Returns True if found."""
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
    """Case-insensitive text match — returns first open/active match."""
    entries = read_all(model_cls, devlog_dir)
    search_lower = search.lower()
    for entry in entries:
        if search_lower in entry.text.lower():
            return entry
    return None


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

def git_commit(devlog_dir: Path, message: str, extra_files: Optional[List[Path]] = None) -> None:
    repo_root = find_git_root(devlog_dir)
    if not repo_root:
        return
    try:
        to_add = [str(devlog_dir)] + ([str(f) for f in extra_files] if extra_files else [])
        subprocess.run(
            ["git", "-C", str(repo_root), "add", *to_add],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_root), "commit", "-m", message],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError:
        pass
