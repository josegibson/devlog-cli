import json
import subprocess

import yaml
from typer.testing import CliRunner

from devlog.main import app
from devlog.storage import read_events


runner = CliRunner()


def run_cli(*args):
    result = runner.invoke(app, list(args), catch_exceptions=False)
    assert result.exit_code == 0, result.output
    return result


def init_git_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Devlog Test"],
        cwd=path, check=True, capture_output=True,
    )


def read_yaml(path):
    return yaml.safe_load(path.read_text()) or []


def test_init_creates_local_state_and_exports(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = run_cli("init")

    assert "Initialised .devlog/" in result.output
    assert (tmp_path / ".devlog").is_dir()
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / ".devlog" / "index.json").exists()
    assert not (tmp_path / "DEVLOG.json").exists()

    payload = json.loads((tmp_path / ".devlog" / "index.json").read_text())
    assert payload["schema_version"] == "0.3.0"

    # devlog no longer auto-commits — project git history stays clean (no commits at all)
    git_log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_path, text=True, capture_output=True,
    )
    assert git_log.stdout.strip() == ""


def test_goal_lifecycle_updates_aims_and_generated_context(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    run_cli("goal", "Ship v0.2 test coverage")
    list_result = run_cli("goal", "--list")
    assert "Active" in list_result.output
    assert "Ship v0.2 test coverage" in list_result.output
    assert "Ship v0.2 test coverage" in (tmp_path / "AGENTS.md").read_text()

    run_cli("goal", "--done")
    done_result = run_cli("goal", "--list")
    assert "No active goal" in done_result.output
    assert "Completed" in done_result.output

    aims = read_yaml(tmp_path / ".devlog" / "aims.yaml")
    assert aims[0]["status"] == "completed"
    assert aims[0]["done_at"]

    # event log captures lifecycle mutations
    events = read_events(tmp_path / ".devlog")
    ops = [e["op"] for e in events]
    assert "aim.create" in ops
    assert "aim.done" in ops


def test_activity_log_visibility_export_filtering_and_journey(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    run_cli("note", "Public milestone", "--type", "shipped")
    run_cli("note", "Private diagnostic", "--internal")

    journey = run_cli("log", "--oneline")
    assert "Public milestone" in journey.output
    assert "Private diagnostic" in journey.output

    notes = read_yaml(tmp_path / ".devlog" / "notes.yaml")
    assert [note["visibility"] for note in notes] == ["public", "internal"]

    export = run_cli("export")
    payload = json.loads(export.output[export.output.index("{"):])
    assert [note["text"] for note in payload["notes"]] == ["Public milestone"]


def test_decision_blocker_handoff_standup_and_validate_flow(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    run_cli("goal", "Exercise v0.2 core flow")
    run_cli("call", "Use YAML under .devlog", "--context", "human-readable git diffs")
    run_cli("snag", "Need verify generated exports")
    run_cli("clear", "exports")
    run_cli("brief", "--situation", "Core flow tested")

    decisions = run_cli("calls")
    assert "Use YAML under .devlog" in decisions.output

    standup = run_cli("standup")
    assert "Exercise v0.2 core flow" in standup.output
    assert "Core flow tested" in standup.output
    assert "No active blockers" in standup.output

    validate = run_cli("validate")
    assert ".devlog/ is valid" in validate.output

    snags = read_yaml(tmp_path / ".devlog" / "snags.yaml")
    assert snags[0]["status"] == "cleared"

    # event log captures the clear mutation
    events = read_events(tmp_path / ".devlog")
    ops = [e["op"] for e in events]
    assert "snag.create" in ops
    assert "snag.clear" in ops


def test_validate_reports_unknown_threatened_call(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    snags_path = tmp_path / ".devlog" / "snags.yaml"
    snags_path.write_text(yaml.dump(
        [{
            "id": "snag-2026-01-01-bad-reference",
            "date": "2026-01-01",
            "text": "Bad reference",
            "threatens": "call-2026-01-01-missing",
            "impact": "medium",
            "status": "open",
            "visibility": "public",
        }],
        sort_keys=False,
    ))

    result = run_cli("validate")
    assert "warning" in result.output.lower()
    assert "threatens unknown call" in result.output
