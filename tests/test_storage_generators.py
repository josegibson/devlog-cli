import json
import subprocess

import pytest
import yaml

from devlog.generators import (
    generate_agents_md,
    generate_devlog_index,
    write_agents_md,
    write_devlog_index,
)
from devlog.models import Aim, Brief, Call, Debt, Milestone, Note, Snag, make_id
from devlog.storage import (
    append_entry,
    find_devlog_dir,
    find_entry_by_text,
    git_commit,
    init_devlog,
    read_all,
    update_entry,
    write_all,
)


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


def test_storage_round_trip_update_search_and_parent_discovery(tmp_path, monkeypatch):
    devlog_dir = init_devlog(tmp_path)
    note = Note(
        id=make_id("note", "Storage round trip"),
        date="2026-05-13",
        text="Storage round trip",
        kind="learning",
    )

    append_entry(note, devlog_dir)
    assert read_all(Note, devlog_dir)[0].text == "Storage round trip"

    found = find_entry_by_text(Note, "round", devlog_dir)
    assert found and found.id == note.id

    updated = update_entry(
        Note,
        note.id,
        lambda entry: setattr(entry, "visibility", "internal"),
        devlog_dir,
    )
    assert updated is True
    assert read_all(Note, devlog_dir)[0].visibility == "internal"
    assert update_entry(Note, "missing", lambda entry: None, devlog_dir) is False

    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert find_devlog_dir() == devlog_dir


def test_write_all_omits_none_values_and_empty_files_read_as_empty(tmp_path):
    devlog_dir = init_devlog(tmp_path)
    call = Call(
        id="call-2026-05-13-use-yaml",
        date="2026-05-13",
        text="Use YAML",
    )

    write_all(Call, [call], devlog_dir)

    raw_calls = yaml.safe_load((devlog_dir / "calls.yaml").read_text())
    assert "context" not in raw_calls[0]
    assert read_all(Snag, devlog_dir) == []

    (devlog_dir / "notes.yaml").write_text("")
    assert read_all(Note, devlog_dir) == []


def test_generators_render_agents_context_and_filter_public_index(tmp_path):
    devlog_dir = init_devlog(tmp_path)
    call = Call(
        id="call-2026-05-13-use-yaml",
        date="2026-05-13",
        text="Use YAML",
        context="readable diffs",
        tradeoff="manual merge conflicts remain visible",
    )
    append_entry(call, devlog_dir)
    append_entry(
        Snag(
            id="snag-2026-05-13-bad-reference",
            date="2026-05-13",
            text="Bad reference",
            threatens=call.id,
            blocks="release",
            impact="high",
        ),
        devlog_dir,
    )
    append_entry(
        Aim(
            id="aim-2026-05-13-ship-tests",
            date="2026-05-13",
            text="Ship tests",
            horizon="coverage gates in place",
            risk="untested exports",
            next_decision="coverage threshold",
        ),
        devlog_dir,
    )
    append_entry(
        Note(
            id="note-2026-05-13-public",
            date="2026-05-13",
            text="Public note",
        ),
        devlog_dir,
    )
    append_entry(
        Note(
            id="note-2026-05-13-private",
            date="2026-05-13",
            text="Private note",
            visibility="internal",
        ),
        devlog_dir,
    )

    agents_md = generate_agents_md(devlog_dir)
    assert "Ship tests" in agents_md
    assert "coverage gates in place" in agents_md
    assert "threatens call" in agents_md
    assert "Use YAML" in agents_md
    assert "Tradeoff" in agents_md

    agents_path = write_agents_md(devlog_dir)
    index_path = write_devlog_index(devlog_dir)
    assert agents_path == tmp_path / "AGENTS.md"
    assert index_path == devlog_dir / "index.json"

    index = generate_devlog_index(devlog_dir)
    assert [note["text"] for note in index["notes"]] == ["Public note"]
    assert json.loads(index_path.read_text())["schema_version"] == "0.3.0"


def test_generators_render_optional_handoff_goal_target_and_known_debt(tmp_path):
    devlog_dir = init_devlog(tmp_path)
    append_entry(
        Aim(
            id="aim-2026-05-13-release",
            date="2026-05-13",
            text="Release v0.2",
            by="Friday",
        ),
        devlog_dir,
    )
    append_entry(
        Brief(
            id="brief-2026-05-13-handoff",
            date="2026-05-13",
            situation="Tests are expanded",
            background="Coverage reports are enabled",
            assessment="Remaining risk is CLI branch drift",
            recommendation="Add CI before v0.3 work",
        ),
        devlog_dir,
    )
    append_entry(
        Debt(
            id="debt-2026-05-13-cli-branches",
            date="2026-05-13",
            text="Some CLI branches remain thinly tested",
            fix_by="before v0.3",
        ),
        devlog_dir,
    )
    append_entry(
        Milestone(
            id="milestone-2026-05-13-v0-3",
            date="2026-05-13",
            text="v0.3",
            version="v0.3.0",
            achieved="2026-05-13",
            summary="Schema commands",
        ),
        devlog_dir,
    )

    agents_md = generate_agents_md(devlog_dir)

    assert "**Target:** Friday" in agents_md
    assert "Background" in agents_md
    assert "Assessment" in agents_md
    assert "Recommendation" in agents_md
    assert "Known Debt" in agents_md
    assert "before v0.3" in agents_md
    assert "Milestones" in agents_md
    assert "v0.3.0" in agents_md

    index = generate_devlog_index(devlog_dir)
    assert index["milestones"][0]["version"] == "v0.3.0"


def test_git_commit_noops_outside_git_repo(tmp_path):
    devlog_dir = init_devlog(tmp_path)
    append_entry(
        Note(
            id="note-2026-05-13-no-git",
            date="2026-05-13",
            text="No git",
        ),
        devlog_dir,
    )

    git_commit(devlog_dir, "devlog: no git")

    assert not (tmp_path / ".git").exists()


def test_git_commit_adds_devlog_and_extra_files_but_not_unrelated_files(tmp_path):
    init_git_repo(tmp_path)
    devlog_dir = init_devlog(tmp_path)
    append_entry(
        Note(
            id="note-2026-05-13-git",
            date="2026-05-13",
            text="Git commit",
        ),
        devlog_dir,
    )
    agents_path = write_agents_md(devlog_dir)
    (tmp_path / "scratch.txt").write_text("do not add me")

    git_commit(devlog_dir, "devlog: test commit", extra_files=[agents_path])

    committed = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    assert ".devlog/notes.yaml" in committed
    assert "AGENTS.md" in committed
    assert "?? scratch.txt" in status


def test_find_devlog_dir_raises_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError):
        find_devlog_dir()
