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

from .generators import generate_agents_md, write_agents_md, write_devlog_index, write_tension_map
from .models import Aim, Brief, Call, Constraint, Debt, Milestone, Note, Shift, Snag, Arch, make_id
from .storage import append_entry, find_devlog_dir, find_git_root, init_devlog, log_event, read_all, uncommitted_devlog_files, write_all

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


def _sync(devlog_dir: Path) -> None:
    """Regenerate AGENTS.md, tension.yaml, and index.json from current state."""
    write_agents_md(devlog_dir)
    write_tension_map(devlog_dir)
    write_devlog_index(devlog_dir)


def _split_csv(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

@app.command()
def init():
    """Initialise devlog in the current project."""
    project_root = Path.cwd()
    devlog_dir = init_devlog(project_root)

    agents_path = write_agents_md(devlog_dir)
    write_devlog_index(devlog_dir)

    console.print(f"[green]Initialised .devlog/[/green]")
    console.print(f"  [dim]{devlog_dir}[/dim]")
    console.print(f"  [dim]{agents_path}[/dim]")

    repo_root = find_git_root(devlog_dir)
    if repo_root:
        console.print(
            "\n[dim]Tip: commit .devlog/ and AGENTS.md with your next code change "
            "so devlog state travels with the repo.[/dim]"
        )


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@app.command()
def status():
    """Show current project state via AGENTS.md."""
    devlog_dir = _get_devlog_dir()

    dirty = uncommitted_devlog_files(devlog_dir)
    if dirty:
        console.print(
            f"[yellow]⚠ {len(dirty)} devlog file(s) not yet committed — "
            "run [bold]git add .devlog/ AGENTS.md && git commit[/bold] to persist state.[/yellow]"
        )

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
    horizon: Optional[str] = typer.Option(None, "--horizon", help="Projected end state"),
    by: Optional[str] = typer.Option(None, "--by", help="Time projection"),
    risk: Optional[str] = typer.Option(None, "--risk", help="What could break this goal"),
    next_decision: Optional[str] = typer.Option(None, "--next-decision", help="Upcoming choice point"),
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
        log_event(devlog_dir, "aim.done", active.id, active.text)
        _sync(devlog_dir)
        console.print(f"[green]Goal completed:[/green] {active.text}")
        return

    if clear:
        if not active:
            console.print("[yellow]No active goal to clear.[/yellow]")
            return
        active.status = "cleared"
        write_all(Aim, aims, devlog_dir)
        log_event(devlog_dir, "aim.clear", active.id, active.text)
        _sync(devlog_dir)
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
            horizon=horizon,
            by=by,
            risk=risk,
            next_decision=next_decision,
        )
        append_entry(new_aim, devlog_dir)
        _sync(devlog_dir)
        console.print(f"[blue]Goal set:[/blue] {text}")
        return

    if active:
        console.print(f"[blue]Current goal:[/blue] {active.text}")
    else:
        console.print("[dim]No active goal.[/dim]")


# ---------------------------------------------------------------------------
# note
# ---------------------------------------------------------------------------

@app.command()
def note(
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
    _sync(devlog_dir)
    console.print(f"[green]Logged.[/green]")


# ---------------------------------------------------------------------------
# call
# ---------------------------------------------------------------------------

@app.command()
def call(
    text: str,
    context: Optional[str] = typer.Option(None, "--context", "-c"),
    facing: Optional[str] = typer.Option(None, "--facing"),
    over: Optional[str] = typer.Option(None, "--over", help="Comma-separated rejected alternatives"),
    to_achieve: Optional[str] = typer.Option(None, "--to-achieve"),
    tradeoff: Optional[str] = typer.Option(None, "--tradeoff"),
    status: str = typer.Option("accepted", "--status", help="proposed | accepted | superseded"),
    supersedes: Optional[str] = typer.Option(None, "--supersedes"),
    internal: bool = typer.Option(False, "--internal"),
):
    """Record an architectural decision."""
    devlog_dir = _get_devlog_dir()
    if status not in {"proposed", "accepted", "superseded"}:
        console.print("[red]--status must be proposed, accepted, or superseded[/red]")
        raise typer.Exit(1)
    call = Call(
        id=make_id("call", text),
        date=date.today().isoformat(),
        text=text,
        context=context,
        facing=facing,
        over=_split_csv(over),
        to_achieve=to_achieve,
        tradeoff=tradeoff,
        status=status,
        supersedes=supersedes,
        visibility="internal" if internal else "public",
    )
    append_entry(call, devlog_dir)
    _sync(devlog_dir)
    console.print(f"[blue]Decision recorded.[/blue]")


@app.command()
def calls():
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
# snag / clear
# ---------------------------------------------------------------------------

@app.command()
def snag(
    text: str,
    threatens: Optional[str] = typer.Option(None, "--threatens"),
    blocks: Optional[str] = typer.Option(None, "--blocks"),
    impact: str = typer.Option("medium", "--impact", help="high | medium | low"),
    internal: bool = typer.Option(False, "--internal"),
):
    """Log a blocker."""
    devlog_dir = _get_devlog_dir()
    if impact not in {"high", "medium", "low"}:
        console.print("[red]--impact must be high, medium, or low[/red]")
        raise typer.Exit(1)
    snag = Snag(
        id=make_id("snag", text),
        date=date.today().isoformat(),
        text=text,
        threatens=threatens,
        blocks=blocks,
        impact=impact,
        visibility="internal" if internal else "public",
    )
    append_entry(snag, devlog_dir)
    _sync(devlog_dir)
    console.print("[red]Blocker logged.[/red]")


@app.command()
def clear(text: str):
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
    log_event(devlog_dir, "snag.clear", matched.id, matched.text)
    _sync(devlog_dir)
    console.print(f"[green]Blocker cleared:[/green] {matched.text}")


@app.command()
def pay(text: str):
    """Mark technical debt as paid."""
    devlog_dir = _get_devlog_dir()
    debts = read_all(Debt, devlog_dir)
    search = text.lower()
    matched = next(
        (d for d in debts if search in d.text.lower() and d.status == "open"),
        None,
    )
    if not matched:
        console.print(f"[yellow]No open debt matching '{text}'.[/yellow]")
        return
    matched.status = "paid"
    write_all(Debt, debts, devlog_dir)
    log_event(devlog_dir, "debt.paid", matched.id, matched.text)
    _sync(devlog_dir)
    console.print(f"[green]Debt paid:[/green] {matched.text}")


# ---------------------------------------------------------------------------
# brief
# ---------------------------------------------------------------------------

@app.command()
def brief(
    situation: Optional[str] = typer.Option(None, "--situation", help="Current situation"),
    background: Optional[str] = typer.Option(None, "--background"),
    assessment: Optional[str] = typer.Option(None, "--assessment"),
    recommendation: Optional[str] = typer.Option(None, "--recommendation"),
):
    """Leave a structured brief for the next agent or session."""
    devlog_dir = _get_devlog_dir()

    if not situation:
        briefs = read_all(Brief, devlog_dir)
        if not briefs:
            console.print("[dim]No brief recorded yet.[/dim]")
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
        id=make_id("brief", situation),
        date=date.today().isoformat(),
        situation=situation,
        background=background,
        assessment=assessment,
        recommendation=recommendation,
    )
    append_entry(brief, devlog_dir)
    _sync(devlog_dir)
    console.print("[yellow]Brief saved.[/yellow]")


# ---------------------------------------------------------------------------
# log view
# ---------------------------------------------------------------------------

@app.command()
def log(
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
    
    threatened_map: dict[str, list[Snag]] = {}
    untethered_snags: list[Snag] = []
    for s in open_snags:
        if s.threatens:
            threatened_map.setdefault(s.threatens, []).append(s)
        else:
            untethered_snags.append(s)

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
        f"[bold]Target:[/bold] {active_aim.by if active_aim and active_aim.by else '[dim]None[/dim]'}\n"
        f"[bold]Situation:[/bold] {latest_brief.situation if latest_brief else '[dim]None[/dim]'}",
        title="[bold blue]L1 Perception — Current State[/bold blue]",
        expand=False,
    ))

    if recent_notes:
        t = Table(title="L1 Perception — Recent Activity", show_lines=False)
        t.add_column("Date", style="dim", width=12)
        t.add_column("Kind", style="cyan", width=10)
        t.add_column("Entry")
        for n in recent_notes[-limit:]:
            t.add_row(n.date or "", n.kind, n.text)
        console.print(t)

    if recent_calls or threatened_map:
        t = Table(title="L2 Comprehension — Decisions & Tension", show_lines=False)
        t.add_column("Date", style="dim", width=12)
        t.add_column("Decision")
        t.add_column("Status", width=12)
        
        # Add threatened calls first, even if not in "recent_calls"
        shown_ids = set()
        for call_id in threatened_map:
            call = next((c for c in calls if c.id == call_id), None)
            if call:
                t.add_row(call.date or "", call.text, "[red]at-risk ⚠️[/red]")
                for s in threatened_map[call_id]:
                    t.add_row("", f"  [red]⚡ Snag:[/red] {s.text}", "")
                shown_ids.add(call_id)
        
        for c in recent_calls:
            if c.id in shown_ids:
                continue
            t.add_row(c.date or "", c.text, "[green]nominal[/green]")
        
        console.print(t)

    if untethered_snags:
        blocker_text = "\n".join(
            f"• {s.text}" + (f" [{s.impact}]" if s.impact else "")
            for s in untethered_snags
        )
        console.print(Panel(blocker_text, title="[bold red]L2 Comprehension — Untethered Blockers[/bold red]", expand=False))
    elif not threatened_map:
        console.print(Panel("[green]No active blockers.[/green]", title="L2 Comprehension — Blockers", expand=False))

    projection_lines = []
    if active_aim:
        if active_aim.horizon:
            projection_lines.append(f"[bold]Done looks like:[/bold] {active_aim.horizon}")
        if active_aim.risk:
            projection_lines.append(f"[bold]Risk:[/bold] {active_aim.risk}")
        if active_aim.next_decision:
            projection_lines.append(f"[bold]Next decision:[/bold] {active_aim.next_decision}")
    if latest_brief and latest_brief.recommendation:
        projection_lines.append(f"[bold]Recommendation:[/bold] {latest_brief.recommendation}")
    console.print(Panel(
        "\n".join(projection_lines) if projection_lines else "[dim]No projection recorded.[/dim]",
        title="[bold blue]L3 Projection — Path Forward[/bold blue]",
        expand=False,
    ))


# ---------------------------------------------------------------------------
# orient
# ---------------------------------------------------------------------------

@app.command()
def orient():
    """Orientation briefing for agents: tool overview and current project state."""
    devlog_dir = _get_devlog_dir()

    console.print(Panel(
        "[bold]devlog[/bold] is a shared state engine between you (the agent) and the developer.\n"
        "It keeps [cyan]AGENTS.md[/cyan] as your working copy — [bold]read it now[/bold] for full context.\n"
        "State lives in [dim].devlog/[/dim] and travels with the repo. Commit it with your code.",
        title="[bold blue]devlog — What This Tool Is[/bold blue]",
        expand=False,
    ))

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("Command")
    table.add_column("When to use it")
    table.add_row("[green]devlog status[/green]",      "Check current goal, brief, and blockers")
    table.add_row("[green]devlog standup[/green]",     "Summarise current goal, recent activity, decisions, blockers")
    table.add_row("[green]devlog goal \"...\"[/green]","Set the current goal")
    table.add_row("[green]devlog goal --done[/green]", "Mark the current goal as completed")
    table.add_row("[green]devlog note \"...\"[/green]", "Record a milestone (--type shipped|learning)")
    table.add_row("[green]devlog call \"...\"[/green]", "Log an architectural decision")
    table.add_row("[green]devlog snag \"...\"[/green]",  "Log a blocker")
    table.add_row("[green]devlog clear \"...\"[/green]","Mark a blocker as fixed")
    table.add_row("[green]devlog pay \"...\"[/green]",  "Mark technical debt as paid")
    table.add_row("[green]devlog brief --situation \"...\"[/green]","Leave a structured handoff")
    console.print(Panel(table, title="[bold blue]Commands[/bold blue]", expand=False))

    aims  = read_all(Aim, devlog_dir)
    snags = read_all(Snag, devlog_dir)
    briefs = read_all(Brief, devlog_dir)
    calls = read_all(Call, devlog_dir)
    
    active_aim  = next((a for a in reversed(aims) if a.status == "active"), None)
    latest_brief = briefs[-1] if briefs else None
    open_snags  = [s for s in snags if s.status == "open"]
    
    threatened_map: dict[str, list[Snag]] = {}
    untethered_snags: list[Snag] = []
    for s in open_snags:
        if s.threatens:
            threatened_map.setdefault(s.threatens, []).append(s)
        else:
            untethered_snags.append(s)

    console.print(Panel(
        f"[bold]Goal:[/bold] {active_aim.text if active_aim else '[dim]None[/dim]'}\n"
        f"[bold]Target:[/bold] {active_aim.by if active_aim and active_aim.by else '[dim]None[/dim]'}\n"
        f"[bold]Situation:[/bold] {latest_brief.situation if latest_brief else '[dim]None[/dim]'}",
        title="[bold blue]L1 Perception — Current State[/bold blue]",
        expand=False,
    ))

    assessment = latest_brief.assessment if latest_brief and latest_brief.assessment else "[dim]None[/dim]"
    
    # Simple tension display for orient
    tension_bits = []
    for call_id, call_snags in threatened_map.items():
        call = next((c for c in calls if c.id == call_id), None)
        call_text = call.text if call else call_id
        tension_bits.append(f"  • [red]at-risk:[/red] {call_text}")
        for s in call_snags:
            tension_bits.append(f"    - ⚡ {s.text}")
    
    for s in untethered_snags:
        tension_bits.append(f"  • [yellow]untethered snag:[/yellow] {s.text}")
    
    if not tension_bits:
        tension_bits.append("[dim]None[/dim]")

    console.print(Panel(
        f"[bold]Assessment:[/bold] {assessment}\n"
        f"[bold]Tension Map:[/bold]\n" + "\n".join(tension_bits),
        title="[bold blue]L2 Comprehension — Meaning and Risk[/bold blue]",
        expand=False,
    ))

    projection_bits = []
    if active_aim and active_aim.horizon:
        projection_bits.append(f"[bold]Done looks like:[/bold] {active_aim.horizon}")
    if active_aim and active_aim.risk:
        projection_bits.append(f"[bold]Risk:[/bold] {active_aim.risk}")
    if active_aim and active_aim.next_decision:
        projection_bits.append(f"[bold]Next decision:[/bold] {active_aim.next_decision}")
    if latest_brief and latest_brief.recommendation:
        projection_bits.append(f"[bold]Recommendation:[/bold] {latest_brief.recommendation}")
    console.print(Panel(
        "\n".join(projection_bits) if projection_bits else "[dim]No projection recorded.[/dim]",
        title="[bold blue]L3 Projection — Path Forward[/bold blue]",
        expand=False,
    ))

    console.print("[dim]Log decisions, dead ends, breakthroughs, and blockers as they happen.[/dim]\n")


# ---------------------------------------------------------------------------
# shift
# ---------------------------------------------------------------------------

@app.command()
def shift(
    from_: str = typer.Option(..., "--from", help="Old direction"),
    to: str = typer.Option(..., "--to", help="New direction"),
    intended: Optional[str] = typer.Option(None, "--intended"),
    actual: Optional[str] = typer.Option(None, "--actual"),
    assumption_broke: Optional[str] = typer.Option(None, "--assumption-broke"),
    sustain: Optional[str] = typer.Option(None, "--sustain"),
    internal: bool = typer.Option(False, "--internal"),
):
    """Log a direction change."""
    devlog_dir = _get_devlog_dir()
    entry = Shift(
        id=make_id("shift", f"{from_} to {to}"),
        date=date.today().isoformat(),
        from_=from_,
        to=to,
        intended=intended,
        actual=actual,
        assumption_broke=assumption_broke,
        sustain=sustain,
        visibility="internal" if internal else "public",
    )
    append_entry(entry, devlog_dir)
    _sync(devlog_dir)
    console.print("[yellow]Shift recorded.[/yellow]")


# ---------------------------------------------------------------------------
# arch
# ---------------------------------------------------------------------------

@app.command()
def arch(
    text: str,
    containers: Optional[str] = typer.Option(None, "--containers", help="Comma-separated containers"),
    relationships: Optional[str] = typer.Option(None, "--relationships", help="Comma-separated relationships"),
    external: Optional[str] = typer.Option(None, "--external", help="Comma-separated external systems"),
    quality_goals: Optional[str] = typer.Option(None, "--quality-goals", help="Comma-separated quality goals"),
    intent: Optional[str] = typer.Option(None, "--intent"),
):
    """Describe current system architecture."""
    devlog_dir = _get_devlog_dir()
    entry = Arch(
        id=make_id("arch", text),
        date=date.today().isoformat(),
        text=text,
        containers=_split_csv(containers),
        relationships=_split_csv(relationships),
        external=_split_csv(external),
        quality_goals=_split_csv(quality_goals),
        intent=intent,
    )
    append_entry(entry, devlog_dir)
    _sync(devlog_dir)
    console.print("[blue]Architecture recorded.[/blue]")


# ---------------------------------------------------------------------------
# constraint
# ---------------------------------------------------------------------------

@app.command()
def constraint(
    text: str,
    type: str = typer.Option("technical", "--type", help="technical | organizational | regulatory | convention"),
    source: Optional[str] = typer.Option(None, "--source"),
    impact: Optional[str] = typer.Option(None, "--impact"),
):
    """Log a hard constraint."""
    devlog_dir = _get_devlog_dir()
    if type not in {"technical", "organizational", "regulatory", "convention"}:
        console.print("[red]--type must be technical, organizational, regulatory, or convention[/red]")
        raise typer.Exit(1)
    entry = Constraint(
        id=make_id("constraint", text),
        date=date.today().isoformat(),
        text=text,
        type=type,
        source=source,
        impact=impact,
    )
    append_entry(entry, devlog_dir)
    _sync(devlog_dir)
    console.print("[blue]Constraint recorded.[/blue]")


# ---------------------------------------------------------------------------
# debt
# ---------------------------------------------------------------------------

@app.command()
def debt(
    text: str,
    quadrant: str = typer.Option("prudent-deliberate", "--quadrant"),
    interest: Optional[str] = typer.Option(None, "--interest"),
    principal: Optional[str] = typer.Option(None, "--principal"),
    fix_by: Optional[str] = typer.Option(None, "--fix-by"),
    internal: bool = typer.Option(False, "--internal"),
):
    """Log technical debt."""
    devlog_dir = _get_devlog_dir()
    valid = {"prudent-deliberate", "prudent-inadvertent", "reckless-deliberate", "reckless-inadvertent"}
    if quadrant not in valid:
        console.print("[red]--quadrant must be one of Fowler's four debt quadrants[/red]")
        raise typer.Exit(1)
    entry = Debt(
        id=make_id("debt", text),
        date=date.today().isoformat(),
        text=text,
        quadrant=quadrant,
        interest=interest,
        principal=principal,
        fix_by=fix_by,
        visibility="internal" if internal else "public",
    )
    append_entry(entry, devlog_dir)
    _sync(devlog_dir)
    console.print("[blue]Debt recorded.[/blue]")


# ---------------------------------------------------------------------------
# milestone / timeline
# ---------------------------------------------------------------------------

@app.command()
def milestone(
    text: str,
    version: Optional[str] = typer.Option(None, "--version"),
    achieved: Optional[str] = typer.Option(None, "--achieved", help="YYYY-MM-DD"),
    summary: Optional[str] = typer.Option(None, "--summary"),
    calls: Optional[str] = typer.Option(None, "--calls", help="Comma-separated call IDs"),
    shifts: Optional[str] = typer.Option(None, "--shifts", help="Comma-separated shift IDs"),
    parent: Optional[str] = typer.Option(None, "--parent", help="Parent milestone ID"),
):
    """Mark a version boundary node in the project DAG."""
    devlog_dir = _get_devlog_dir()
    entry = Milestone(
        id=make_id("milestone", version or text),
        date=date.today().isoformat(),
        text=text,
        version=version,
        achieved=achieved,
        summary=summary,
        calls=_split_csv(calls),
        shifts=_split_csv(shifts),
        parent=parent,
    )
    append_entry(entry, devlog_dir)
    _sync(devlog_dir)
    console.print("[blue]Milestone recorded.[/blue]")


@app.command()
def timeline():
    """Render the milestone DAG as a chronological project arc."""
    devlog_dir = _get_devlog_dir()
    milestones = read_all(Milestone, devlog_dir)
    if not milestones:
        console.print("[dim]No milestones recorded yet.[/dim]")
        return

    table = Table(title="Timeline", show_lines=True)
    table.add_column("Version", style="cyan", width=12)
    table.add_column("Achieved", style="dim", width=12)
    table.add_column("Milestone")
    table.add_column("Parent", style="dim")
    table.add_column("Anchors", style="dim")
    for item in sorted(milestones, key=lambda m: (m.achieved or m.date, m.version or m.text)):
        anchors = []
        if item.calls:
            anchors.append(f"{len(item.calls)} call(s)")
        if item.shifts:
            anchors.append(f"{len(item.shifts)} shift(s)")
        table.add_row(
            item.version or "",
            item.achieved or item.date,
            item.summary or item.text,
            item.parent or "",
            ", ".join(anchors),
        )
    console.print(table)


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

    milestone_ids = {m.id for m in read_all(Milestone, devlog_dir)}
    for m in read_all(Milestone, devlog_dir):
        if m.parent and m.parent not in milestone_ids:
            warnings.append(f"milestones.yaml: milestone '{m.id}' has unknown parent '{m.parent}'")

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
    """Export project state as pretty-printed JSON."""
    devlog_dir = _get_devlog_dir()
    from .generators import generate_devlog_index
    payload = json.dumps(generate_devlog_index(devlog_dir), indent=2)
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
