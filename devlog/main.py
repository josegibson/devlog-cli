import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .generators import write_agents_md, write_devlog_json, generate_agents_md
from .models import Aim, Brief, Call, Constraint, Debt, Note, Shift, Snag, Arch, make_id
from .storage import (
    append_entry,
    find_devlog_dir,
    find_git_root,
    git_commit,
    init_devlog,
    read_all,
    update_entry,
    find_entry_by_text,
    write_all,
)

app = typer.Typer(help="devlog — meta state engine for software projects")
console = Console()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_devlog_dir() -> Path:
    try:
        return find_devlog_dir()
    except FileNotFoundError:
        console.print("[red]No .devlog/ found. Run [bold]devlog init[/bold] first.[/red]")
        raise typer.Exit(1)


def _sync(devlog_dir: Path, message: str) -> None:
    """Regenerate AGENTS.md + DEVLOG.json, then commit everything."""
    agents_path = write_agents_md(devlog_dir)
    devlog_json_path = write_devlog_json(devlog_dir)
    git_commit(devlog_dir, message, extra_files=[agents_path, devlog_json_path])


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

@app.command()
def init():
    """Initialise devlog in the current project."""
    project_root = Path.cwd()
    devlog_dir = init_devlog(project_root)

    agents_path = write_agents_md(devlog_dir)
    devlog_json_path = write_devlog_json(devlog_dir)

    repo_root = find_git_root(devlog_dir)
    if repo_root:
        git_commit(
            devlog_dir,
            "devlog: init",
            extra_files=[agents_path, devlog_json_path],
        )
        console.print(f"[green]Initialised .devlog/ and committed.[/green]")
    else:
        console.print(f"[green]Initialised .devlog/[/green] (no git repo found — skipping commit)")

    console.print(f"  [dim]{devlog_dir}[/dim]")
    console.print(f"  [dim]{agents_path}[/dim]")


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@app.command()
def status():
    """Show current project state via AGENTS.md."""
    devlog_dir = _get_devlog_dir()
    agents_path = devlog_dir.parent / "AGENTS.md"
    if agents_path.exists():
        console.print(Panel(Markdown(agents_path.read_text()), title="Agent Context"))
    else:
        console.print(Panel(generate_agents_md(devlog_dir), title="Agent Context"))


# ---------------------------------------------------------------------------
# goal
# ---------------------------------------------------------------------------

@app.command()
def goal(
    text: Optional[str] = typer.Argument(None),
    done: bool = typer.Option(False, "--done", help="Mark current goal as completed"),
    clear: bool = typer.Option(False, "--clear", help="Clear current goal without completing"),
    list_goals: bool = typer.Option(False, "--list", help="Show active and completed goals"),
):
    """Set, complete, or list goals."""
    devlog_dir = _get_devlog_dir()
    aims = read_all(Aim, devlog_dir)
    active = next((a for a in reversed(aims) if a.status == "active"), None)

    if list_goals:
        completed = [a for a in aims if a.status == "completed"]
        if active:
            console.print(f"[bold green]● Active:[/bold green] {active.text}")
            if active.horizon:
                console.print(f"  [dim]Done looks like:[/dim] {active.horizon}")
        else:
            console.print("[dim]No active goal.[/dim]")
        if completed:
            console.print("\n[bold]Completed:[/bold]")
            for a in reversed(completed):
                console.print(f"  [dim]✓ {a.done_at}[/dim]  {a.text}")
        return

    if done:
        if not active:
            console.print("[yellow]No active goal to mark done.[/yellow]")
            return
        active.status = "completed"
        active.done_at = date.today().isoformat()
        write_all(Aim, aims, devlog_dir)
        _sync(devlog_dir, f"devlog: [goal-done] {active.text[:60]}")
        console.print(f"[green]Goal completed:[/green] {active.text}")
        return

    if clear:
        if not active:
            console.print("[yellow]No active goal to clear.[/yellow]")
            return
        active.status = "cleared"
        write_all(Aim, aims, devlog_dir)
        _sync(devlog_dir, f"devlog: [goal-clear] {active.text[:60]}")
        console.print("[yellow]Goal cleared.[/yellow]")
        return

    if text:
        if active and active.text == text:
            console.print(f"[blue]Goal unchanged:[/blue] {text}")
            return
        new_aim = Aim(
            id=make_id("aim", text),
            date=date.today().isoformat(),
            text=text,
        )
        append_entry(new_aim, devlog_dir)
        _sync(devlog_dir, f"devlog: [goal] {text[:60]}")
        console.print(f"[blue]Goal set:[/blue] {text}")
        return

    if active:
        console.print(f"[blue]Current goal:[/blue] {active.text}")
    else:
        console.print("[dim]No active goal.[/dim]")


# ---------------------------------------------------------------------------
# log  (note — v0.2 keeps old name; v0.3 renames)
# ---------------------------------------------------------------------------

@app.command()
def log(
    entry: str,
    internal: bool = typer.Option(False, "--internal"),
    type: Optional[str] = typer.Option(None, "--type", help="shipped | learning"),
):
    """Log a milestone or observation to the activity record."""
    devlog_dir = _get_devlog_dir()
    _KINDS = {"shipped": "shipped", "learning": "learning"}
    kind = _KINDS.get(type or "", "log")
    note = Note(
        id=make_id("note", entry),
        date=date.today().isoformat(),
        text=entry,
        kind=kind,
        visibility="internal" if internal else "public",
    )
    append_entry(note, devlog_dir)
    _sync(devlog_dir, f"devlog: [note] {entry[:60]}")
    console.print(f"[green]Logged.[/green]")


# ---------------------------------------------------------------------------
# decide  (call — v0.3 renames)
# ---------------------------------------------------------------------------

@app.command()
def decide(
    text: str,
    context: Optional[str] = typer.Option(None, "--context", "-c"),
    internal: bool = typer.Option(False, "--internal"),
):
    """Record an architectural decision."""
    devlog_dir = _get_devlog_dir()
    call = Call(
        id=make_id("call", text),
        date=date.today().isoformat(),
        text=text,
        context=context,
        visibility="internal" if internal else "public",
    )
    append_entry(call, devlog_dir)
    _sync(devlog_dir, f"devlog: [call] {text[:60]}")
    console.print(f"[blue]Decision recorded.[/blue]")


@app.command()
def decisions():
    """List architectural decisions."""
    devlog_dir = _get_devlog_dir()
    calls = read_all(Call, devlog_dir)
    if not calls:
        console.print("[dim]No decisions logged yet.[/dim]")
        return
    table = Table(title="Decisions", show_lines=True)
    table.add_column("Date", style="dim", width=12)
    table.add_column("Status", width=10)
    table.add_column("Decision")
    table.add_column("Context", style="dim")
    for c in calls:
        status_color = "green" if c.status == "accepted" else "yellow" if c.status == "proposed" else "dim"
        table.add_row(c.date, f"[{status_color}]{c.status}[/{status_color}]", c.text, c.context or "")
    console.print(table)


# ---------------------------------------------------------------------------
# block / resolve  (snag / clear — v0.3 renames)
# ---------------------------------------------------------------------------

@app.command()
def block(
    text: str,
    internal: bool = typer.Option(False, "--internal"),
):
    """Log a blocker."""
    devlog_dir = _get_devlog_dir()
    snag = Snag(
        id=make_id("snag", text),
        date=date.today().isoformat(),
        text=text,
        visibility="internal" if internal else "public",
    )
    append_entry(snag, devlog_dir)
    _sync(devlog_dir, f"devlog: [snag] {text[:60]}")
    console.print("[red]Blocker logged.[/red]")


@app.command()
def resolve(text: str):
    """Mark a blocker as cleared."""
    devlog_dir = _get_devlog_dir()
    snags = read_all(Snag, devlog_dir)
    search = text.lower()
    matched = next(
        (s for s in snags if search in s.text.lower() and s.status == "open"),
        None,
    )
    if not matched:
        console.print(f"[yellow]No open blocker matching '{text}'.[/yellow]")
        return
    matched.status = "cleared"
    write_all(Snag, snags, devlog_dir)
    _sync(devlog_dir, f"devlog: [cleared] {matched.text[:60]}")
    console.print(f"[green]Blocker cleared:[/green] {matched.text}")


# ---------------------------------------------------------------------------
# handoff  (brief — v0.3 renames)
# ---------------------------------------------------------------------------

@app.command()
def handoff(
    text: Optional[str] = typer.Argument(None, help="Situation summary (free-text shorthand)"),
):
    """Leave a handoff note for the next agent or session."""
    devlog_dir = _get_devlog_dir()

    if not text:
        briefs = read_all(Brief, devlog_dir)
        if not briefs:
            console.print("[dim]No handoff recorded yet.[/dim]")
            return
        last = briefs[-1]
        console.print(Panel(
            f"[bold]Situation:[/bold] {last.situation}\n"
            + (f"[bold]Background:[/bold] {last.background}\n" if last.background else "")
            + (f"[bold]Assessment:[/bold] {last.assessment}\n" if last.assessment else "")
            + (f"[bold]Recommendation:[/bold] {last.recommendation}\n" if last.recommendation else ""),
            title=f"Last Handoff — {last.date}",
        ))
        return

    brief = Brief(
        id=make_id("brief", text),
        date=date.today().isoformat(),
        situation=text,
    )
    append_entry(brief, devlog_dir)
    _sync(devlog_dir, f"devlog: [brief] {text[:60]}")
    console.print("[yellow]Handoff saved.[/yellow]")


# ---------------------------------------------------------------------------
# journey  (log view — v0.3 renames)
# ---------------------------------------------------------------------------

@app.command()
def journey(
    limit: int = typer.Option(0, "--limit", help="Show last N entries (0 = all)"),
    oneline: bool = typer.Option(False, "--oneline"),
):
    """Show the activity log."""
    devlog_dir = _get_devlog_dir()
    notes = read_all(Note, devlog_dir)
    if limit > 0:
        notes = notes[-limit:]

    if not notes:
        console.print("[dim]No activity logged yet.[/dim]")
        return

    if oneline:
        for n in notes:
            kind_tag = f"[{n.kind}] " if n.kind != "log" else ""
            int_tag = " [internal]" if n.visibility == "internal" else ""
            console.print(f"[dim]{n.date or '          '}[/dim] {kind_tag}{n.text}{int_tag}")
    else:
        table = Table(title="Activity Log", show_lines=True)
        table.add_column("Date", style="dim", width=12)
        table.add_column("Kind", style="cyan", width=10)
        table.add_column("Vis", width=8)
        table.add_column("Entry")
        for n in notes:
            vis_color = "dim" if n.visibility == "internal" else "green"
            table.add_row(n.date or "", n.kind, f"[{vis_color}]{n.visibility}[/{vis_color}]", n.text)
        console.print(table)


# ---------------------------------------------------------------------------
# standup
# ---------------------------------------------------------------------------

@app.command()
def standup(
    since: Optional[str] = typer.Option(None, "--since", help="YYYY-MM-DD"),
    limit: int = typer.Option(8, "--limit"),
):
    """Aggregate current project state into a standup summary."""
    devlog_dir = _get_devlog_dir()

    aims   = read_all(Aim, devlog_dir)
    notes  = read_all(Note, devlog_dir)
    calls  = read_all(Call, devlog_dir)
    snags  = read_all(Snag, devlog_dir)
    briefs = read_all(Brief, devlog_dir)

    active_aim   = next((a for a in reversed(aims) if a.status == "active"), None)
    latest_brief = briefs[-1] if briefs else None
    open_snags   = [s for s in snags if s.status == "open"]

    since_date = None
    if since:
        try:
            from datetime import date as _date
            since_date = _date.fromisoformat(since)
        except ValueError:
            console.print("[red]--since must be YYYY-MM-DD[/red]")
            raise typer.Exit(1)

    if since_date:
        recent_notes = [n for n in notes if n.date and n.date >= since_date.isoformat()]
        recent_calls = [c for c in calls if c.date and c.date >= since_date.isoformat()]
    else:
        recent_notes = notes[-limit:]
        recent_calls = [c for c in calls if c.status == "accepted"][-3:]

    console.print(Panel(
        f"[bold]Goal:[/bold] {active_aim.text if active_aim else '[dim]None[/dim]'}\n"
        f"[bold]Last handoff:[/bold] {latest_brief.situation if latest_brief else '[dim]None[/dim]'}",
        title="[bold blue]Standup[/bold blue]",
        expand=False,
    ))

    if recent_notes:
        t = Table(title="Recent Activity", show_lines=False)
        t.add_column("Date", style="dim", width=12)
        t.add_column("Kind", style="cyan", width=10)
        t.add_column("Entry")
        for n in recent_notes[-limit:]:
            t.add_row(n.date or "", n.kind, n.text)
        console.print(t)

    if recent_calls:
        t = Table(title="Recent Decisions", show_lines=False)
        t.add_column("Date", style="dim", width=12)
        t.add_column("Decision")
        t.add_column("Context", style="dim")
        for c in recent_calls:
            t.add_row(c.date or "", c.text, c.context or "")
        console.print(t)

    if open_snags:
        blocker_text = "\n".join(
            f"• {s.text}" + (f" [{s.impact}]" if s.impact else "")
            for s in open_snags
        )
        console.print(Panel(blocker_text, title="[bold red]Active Blockers[/bold red]", expand=False))
    else:
        console.print(Panel("[green]No active blockers.[/green]", title="Blockers", expand=False))


# ---------------------------------------------------------------------------
# onboard  (orient — v0.3 renames)
# ---------------------------------------------------------------------------

@app.command()
def onboard():
    """Orientation briefing for agents: tool overview and current project state."""
    devlog_dir = _get_devlog_dir()

    console.print(Panel(
        "[bold]devlog[/bold] is a shared state engine between you (the agent) and the developer.\n"
        "It keeps [cyan]AGENTS.md[/cyan] as your working copy — [bold]read it now[/bold] for full context.\n"
        "Every write auto-commits to git.",
        title="[bold blue]devlog — What This Tool Is[/bold blue]",
        expand=False,
    ))

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("Command")
    table.add_column("When to use it")
    table.add_row("[green]devlog status[/green]",      "Check current goal, handoff, and blockers")
    table.add_row("[green]devlog standup[/green]",     "Summarise current goal, recent activity, decisions, blockers")
    table.add_row("[green]devlog goal \"...\"[/green]","Set the current goal")
    table.add_row("[green]devlog goal --done[/green]", "Mark the current goal as completed")
    table.add_row("[green]devlog log \"...\"[/green]", "Record a milestone (--type shipped|learning)")
    table.add_row("[green]devlog decide \"...\"[/green]", "Log an architectural decision (--context \"why\")")
    table.add_row("[green]devlog block \"...\"[/green]",  "Log a blocker")
    table.add_row("[green]devlog resolve \"...\"[/green]","Mark a blocker as fixed")
    table.add_row("[green]devlog handoff \"...\"[/green]","Leave a note before ending your session")
    console.print(Panel(table, title="[bold blue]Commands[/bold blue]", expand=False))

    aims  = read_all(Aim, devlog_dir)
    snags = read_all(Snag, devlog_dir)
    briefs = read_all(Brief, devlog_dir)
    active_aim  = next((a for a in reversed(aims) if a.status == "active"), None)
    latest_brief = briefs[-1] if briefs else None
    open_snags  = [s for s in snags if s.status == "open"]
    blockers_str = "\n".join(f"  • {s.text}" for s in open_snags) if open_snags else "[dim]None[/dim]"

    console.print(Panel(
        f"[bold]Goal:[/bold] {active_aim.text if active_aim else '[dim]None[/dim]'}\n"
        f"[bold]Last Handoff:[/bold] {latest_brief.situation if latest_brief else '[dim]None[/dim]'}\n"
        f"[bold]Active Blockers:[/bold]\n{blockers_str}",
        title="[bold blue]Current State[/bold blue]",
        expand=False,
    ))

    console.print("[dim]Log decisions, dead ends, breakthroughs, and blockers as they happen.[/dim]\n")


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

@app.command()
def validate():
    """Validate .devlog/ structure and YAML integrity."""
    devlog_dir = _get_devlog_dir()
    from .storage import _FILE_MAP
    errors = []
    warnings = []

    for model_cls, filename in _FILE_MAP.items():
        path = devlog_dir / filename
        if not path.exists():
            continue
        try:
            entries = read_all(model_cls, devlog_dir)
            ids = [e.id for e in entries]
            dupes = [i for i in ids if ids.count(i) > 1]
            if dupes:
                errors.append(f"{filename}: duplicate IDs — {set(dupes)}")
        except Exception as exc:
            errors.append(f"{filename}: parse error — {exc}")

    # Check snag threats resolve to real call IDs
    calls = read_all(Call, devlog_dir)
    call_ids = {c.id for c in calls}
    snags = read_all(Snag, devlog_dir)
    for s in snags:
        if s.threatens and s.threatens not in call_ids:
            warnings.append(f"snags.yaml: snag '{s.id}' threatens unknown call '{s.threatens}'")

    if errors:
        console.print(f"\n[bold red]✗ {len(errors)} error(s):[/bold red]")
        for e in errors:
            console.print(f"  [red]•[/red] {e}")
    if warnings:
        console.print(f"\n[bold yellow]⚠ {len(warnings)} warning(s):[/bold yellow]")
        for w in warnings:
            console.print(f"  [yellow]•[/yellow] {w}")
    if not errors and not warnings:
        console.print("[bold green]✓ .devlog/ is valid[/bold green]")
    if errors:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

@app.command()
def export(
    output: Optional[Path] = typer.Option(None, "--out", help="Write to file instead of stdout"),
):
    """Export project state as DEVLOG.json."""
    devlog_dir = _get_devlog_dir()
    from .generators import generate_devlog_json
    payload = json.dumps(generate_devlog_json(devlog_dir), indent=2)
    if output:
        output.write_text(payload)
        console.print(f"[green]Exported to {output}[/green]")
    else:
        console.print(payload)


# ---------------------------------------------------------------------------
# edit
# ---------------------------------------------------------------------------

@app.command()
def edit(
    type: Optional[str] = typer.Argument(None, help="Entry type to edit: calls, snags, notes, etc."),
):
    """Open .devlog/ (or a specific YAML file) in $EDITOR."""
    devlog_dir = _get_devlog_dir()
    if type:
        target = devlog_dir / f"{type}.yaml"
        if not target.exists():
            console.print(f"[red]{target} does not exist.[/red]")
            raise typer.Exit(1)
    else:
        target = devlog_dir
    editor = os.environ.get("EDITOR", "nano")
    os.execlp(editor, editor, str(target))


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

@app.command()
def config():
    """Show global devlog configuration."""
    from .config import load_config, _CONFIG_PATH
    cfg = load_config()
    console.print(f"[bold]Config path:[/bold] {_CONFIG_PATH}")
    if cfg:
        console.print(cfg)
    else:
        console.print("[dim]No configuration set.[/dim]")


if __name__ == "__main__":
    app()
