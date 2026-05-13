import json
import subprocess

import yaml
from typer.testing import CliRunner

from devlog.main import app


runner = CliRunner()


def run_cli(*args, expected_exit=0):
    result = runner.invoke(app, list(args), catch_exceptions=False)
    assert result.exit_code == expected_exit, result.output
    return result


def init_git_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Devlog Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def test_init_without_git_skips_commit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = run_cli("init")

    assert "no git repo found" in result.output
    assert (tmp_path / ".devlog" / "index.json").exists()


def test_status_onboard_and_handoff_read_paths(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    empty_brief = run_cli("brief")
    assert "No brief recorded yet" in empty_brief.output

    run_cli("goal", "Exercise read paths")
    run_cli("snag", "Read path blocker")
    run_cli("brief", "--situation", "Continue read path testing")

    status = run_cli("status")
    assert "Exercise read paths" in status.output
    assert "Read path blocker" in status.output

    orient = run_cli("orient")
    assert "devlog status" in orient.output
    assert "Continue read path testing" in orient.output

    brief = run_cli("brief")
    assert "Situation" in brief.output
    assert "Continue read path testing" in brief.output


def test_export_out_writes_pretty_json_file(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")
    run_cli("note", "Export me")

    out_path = tmp_path / "export.json"
    result = run_cli("export", "--out", str(out_path))

    assert "Exported to" in result.output
    assert "export.json" in result.output
    payload = json.loads(out_path.read_text())
    assert payload["notes"][0]["text"] == "Export me"


def test_validate_reports_duplicate_ids_and_malformed_yaml(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    notes_path = tmp_path / ".devlog" / "notes.yaml"
    notes_path.write_text(
        yaml.dump(
            [
                {
                    "id": "note-duplicate",
                    "date": "2026-05-13",
                    "text": "first",
                },
                {
                    "id": "note-duplicate",
                    "date": "2026-05-13",
                    "text": "second",
                },
            ],
            sort_keys=False,
        )
    )

    duplicate = run_cli("validate", expected_exit=1)
    assert "duplicate IDs" in duplicate.output

    notes_path.write_text("[")
    malformed = run_cli("validate", expected_exit=1)
    assert "parse error" in malformed.output


def test_invalid_since_and_missing_devlog_fail_cleanly(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    missing = run_cli("status", expected_exit=1)
    assert "No .devlog/ found" in missing.output

    init_git_repo(tmp_path)
    run_cli("init")
    bad_since = run_cli("standup", "--since", "13-05-2026", expected_exit=1)
    assert "--since must be YYYY-MM-DD" in bad_since.output


def test_goal_clear_duplicate_and_empty_done_paths(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    no_done = run_cli("goal", "--done")
    assert "No active goal to mark done" in no_done.output

    no_clear = run_cli("goal", "--clear")
    assert "No active goal to clear" in no_clear.output

    run_cli("goal", "Stabilize coverage")
    duplicate = run_cli("goal", "Stabilize coverage")
    assert "Goal unchanged" in duplicate.output

    cleared = run_cli("goal", "--clear")
    assert "Goal cleared" in cleared.output

    listed = run_cli("goal", "--list")
    assert "No active goal" in listed.output


def test_empty_decisions_journey_failed_resolve_and_limited_journey(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    decisions = run_cli("calls")
    assert "No decisions logged yet" in decisions.output

    journey = run_cli("log")
    assert "No activity logged yet" in journey.output

    resolve = run_cli("clear", "missing blocker")
    assert "No open blocker matching" in resolve.output

    run_cli("note", "First entry")
    run_cli("note", "Second entry", "--type", "learning")

    limited = run_cli("log", "--limit", "1", "--oneline")
    assert "First entry" not in limited.output
    assert "Second entry" in limited.output

    table = run_cli("log")
    assert "Activity Log" in table.output
    assert "First entry" in table.output


def test_standup_since_filters_recent_items(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    notes_path = tmp_path / ".devlog" / "notes.yaml"
    calls_path = tmp_path / ".devlog" / "calls.yaml"
    notes_path.write_text(
        yaml.dump(
            [
                {
                    "id": "note-2026-01-01-old",
                    "date": "2026-01-01",
                    "text": "Old note",
                    "kind": "log",
                    "visibility": "public",
                },
                {
                    "id": "note-2026-05-13-new",
                    "date": "2026-05-13",
                    "text": "New note",
                    "kind": "log",
                    "visibility": "public",
                },
            ],
            sort_keys=False,
        )
    )
    calls_path.write_text(
        yaml.dump(
            [
                {
                    "id": "call-2026-01-01-old",
                    "date": "2026-01-01",
                    "text": "Old call",
                    "over": [],
                    "status": "accepted",
                    "visibility": "public",
                },
                {
                    "id": "call-2026-05-13-new",
                    "date": "2026-05-13",
                    "text": "New call",
                    "over": [],
                    "status": "accepted",
                    "visibility": "public",
                },
            ],
            sort_keys=False,
        )
    )

    standup = run_cli("standup", "--since", "2026-05-01")
    assert "New note" in standup.output
    assert "New call" in standup.output
    assert "Old note" not in standup.output
    assert "Old call" not in standup.output


def test_config_cli_outputs_empty_and_loaded_config(tmp_path, monkeypatch):
    from devlog import config as config_module

    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "_CONFIG_PATH", config_path)

    empty = run_cli("config")
    assert "No configuration set" in empty.output

    config_path.write_text(json.dumps({"portfolio": "local"}))
    loaded = run_cli("config")
    assert "portfolio" in loaded.output
    assert "local" in loaded.output


def test_v030_schema_commands_write_expected_yaml(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    run_cli(
        "goal",
        "Ship v0.3 schema",
        "--horizon",
        "new commands only",
        "--by",
        "Friday",
        "--risk",
        "alias drift",
        "--next-decision",
        "coverage threshold",
    )
    run_cli(
        "call",
        "Use final command names",
        "--context",
        "no external users yet",
        "--facing",
        "v0.3 public CLI",
        "--over",
        "old aliases, compatibility layer",
        "--to-achieve",
        "clear schema vocabulary",
        "--tradeoff",
        "breaking local scripts",
        "--status",
        "proposed",
        "--supersedes",
        "call-old-names",
    )
    run_cli(
        "snag",
        "Old docs mention aliases",
        "--threatens",
        "call-old-names",
        "--blocks",
        "v0.3 release",
        "--impact",
        "high",
    )
    run_cli(
        "brief",
        "--situation",
        "v0.3 commands implemented",
        "--background",
        "v0.2 used old names",
        "--assessment",
        "tests need new paradigm",
        "--recommendation",
        "ship after coverage passes",
    )
    run_cli(
        "shift",
        "--from",
        "compatibility aliases",
        "--to",
        "breaking final commands",
        "--intended",
        "avoid churn",
        "--actual",
        "no users yet",
        "--assumption-broke",
        "compatibility matters now",
        "--sustain",
        "coverage gate",
    )
    run_cli(
        "arch",
        "local-first CLI",
        "--containers",
        "devlog CLI,.devlog storage",
        "--relationships",
        "CLI writes YAML, generator writes index",
        "--external",
        "git",
        "--quality-goals",
        "readable diffs,offline use",
        "--intent",
        "prepare v0.4 intelligence",
    )
    run_cli(
        "constraint",
        "state must stay local",
        "--type",
        "technical",
        "--source",
        "roadmap",
        "--impact",
        "no database",
    )
    run_cli(
        "debt",
        "README examples can drift",
        "--quadrant",
        "prudent-deliberate",
        "--interest",
        "confuses users",
        "--principal",
        "update docs with commands",
        "--fix-by",
        "v0.3",
    )
    run_cli(
        "milestone",
        "v0.3 schema",
        "--version",
        "v0.3.0",
        "--achieved",
        "2026-05-13",
        "--summary",
        "Final commands and schemas",
        "--calls",
        "call-old-names, call-schema",
        "--shifts",
        "shift-final-names",
        "--parent",
        "milestone-2026-05-13-v0-2-0",
    )

    aims = yaml.safe_load((tmp_path / ".devlog" / "aims.yaml").read_text())
    calls = yaml.safe_load((tmp_path / ".devlog" / "calls.yaml").read_text())
    snags = yaml.safe_load((tmp_path / ".devlog" / "snags.yaml").read_text())
    briefs = yaml.safe_load((tmp_path / ".devlog" / "briefs.yaml").read_text())
    shifts = yaml.safe_load((tmp_path / ".devlog" / "shifts.yaml").read_text())
    arch = yaml.safe_load((tmp_path / ".devlog" / "arch.yaml").read_text())
    constraints = yaml.safe_load((tmp_path / ".devlog" / "constraints.yaml").read_text())
    debt = yaml.safe_load((tmp_path / ".devlog" / "debt.yaml").read_text())
    milestones = yaml.safe_load((tmp_path / ".devlog" / "milestones.yaml").read_text())

    assert aims[0]["horizon"] == "new commands only"
    assert calls[0]["over"] == ["old aliases", "compatibility layer"]
    assert calls[0]["status"] == "proposed"
    assert snags[0]["impact"] == "high"
    assert briefs[0]["recommendation"] == "ship after coverage passes"
    assert shifts[0]["from"] == "compatibility aliases"
    assert arch[0]["containers"] == ["devlog CLI", ".devlog storage"]
    assert constraints[0]["impact"] == "no database"
    assert debt[0]["fix_by"] == "v0.3"
    assert milestones[0]["version"] == "v0.3.0"
    assert milestones[0]["calls"] == ["call-old-names", "call-schema"]
    assert milestones[0]["parent"] == "milestone-2026-05-13-v0-2-0"

    timeline = run_cli("timeline")
    assert "v0.3.0" in timeline.output
    assert "2026-05-13" in timeline.output

    standup = run_cli("standup")
    assert "L1 Perception" in standup.output
    assert "L2 Comprehension" in standup.output
    assert "L3 Projection" in standup.output

    orient = run_cli("orient")
    assert "L1 Perception" in orient.output
    assert "L2 Comprehension" in orient.output
    assert "L3 Projection" in orient.output


def test_old_v020_commands_are_removed(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    for command in ["decide", "decisions", "block", "resolve", "handoff", "journey", "onboard"]:
        result = runner.invoke(app, [command])
        assert result.exit_code != 0


def test_invalid_v030_enum_options_fail_cleanly(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    assert "--status must be" in run_cli("call", "Bad status", "--status", "done", expected_exit=1).output
    assert "--impact must be" in run_cli("snag", "Bad impact", "--impact", "critical", expected_exit=1).output
    assert "--type must be" in run_cli("constraint", "Bad type", "--type", "personal", expected_exit=1).output
    assert "--quadrant must be" in run_cli("debt", "Bad debt", "--quadrant", "messy", expected_exit=1).output


def test_empty_timeline_and_unknown_milestone_parent_warning(tmp_path, monkeypatch):
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_cli("init")

    empty = run_cli("timeline")
    assert "No milestones recorded yet" in empty.output

    run_cli("milestone", "orphan", "--parent", "milestone-missing")
    validate = run_cli("validate")
    assert "unknown parent" in validate.output
