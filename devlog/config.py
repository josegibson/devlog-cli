import json
from pathlib import Path
from typing import Dict, Optional

CONFIG_PATH = Path.home() / ".devlog_config.json"


def load_config() -> Dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {"path_map": {}, "index_path": None}


def save_config(config: Dict):
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def get_index_path() -> Optional[Path]:
    config = load_config()
    path_str = config.get("index_path")
    if path_str:
        return Path(path_str).expanduser().resolve()
    return None


def get_slug_for_path(current_path: Path) -> Optional[str]:
    config = load_config()
    for path_str, slug in config["path_map"].items():
        if str(current_path).startswith(path_str):
            return slug
    return None


# Per-project working state lives in .devlog.json inside the project directory.
# This replaces the old global ~/.devlog_session.json so goals and handoffs
# are scoped to the project and don't clobber across terminals.

def _state_path(project_path: Path) -> Path:
    return project_path / ".devlog.json"


def load_project_state(project_path: Path) -> Dict:
    p = _state_path(project_path)
    if p.exists():
        return json.loads(p.read_text())
    return {"slug": None, "current_goal": None, "last_handoff": None, "completed_goals": []}


def save_project_state(project_path: Path, state: Dict):
    _state_path(project_path).write_text(json.dumps(state, indent=2))


def init_project_state(project_path: Path, slug: str):
    existing = load_project_state(project_path)
    existing["slug"] = slug
    save_project_state(project_path, existing)
