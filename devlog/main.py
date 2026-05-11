import typer
import json
import os
import re
from pathlib import Path
from datetime import date
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from .parser import ProjectParser
from .config import (
    load_config, save_config, get_slug_for_path,
    load_project_state, save_project_state, init_project_state,
    get_index_path,
)

app = typer.Typer(help="Devlog: Agent-Aware Project Manager")
console = Console()


def get_projects_dir() -> Path:
    """Retrieve the path to the central portfolio index (projects/ folder)."""
    path = get_index_path()
    if not path:
        # Fallback to local discovery for development or legacy setups
        path = Path(__file__).parent.parent
    
    projects_dir = path / "projects"
    if not projects_dir.exists():
        raise typer.BadParameter(
            f"Portfolio index not found at {projects_dir}. "
            "Run 'devlog config index <path_to_portfolio_repo>' first."
        )
    return projects_dir


def get_active_slug(slug: Optional[str] = None) -> str:
    if slug:
        return slug
    mapped = get_slug_for_path(Path.cwd())
    if mapped:
        return mapped
    raise typer.BadParameter(
        "No active project. Run 'devlog link <slug>' in this directory first."
    )


def sync_local_devlog(slug: str):
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    project = parser.parse(slug)
    state = load_project_state(Path.cwd())
    hurdle_lines = [
        f"{'[INTERNAL] ' if h.visibility == 'internal' else ''}{h.text}"
        for h in project.hurdles if h.status == "open"  # project.hurdles maps to Blockers section
    ]
    parser.update_local_devlog(
        project_path=Path.cwd(),
        slug=slug,
        title=project.title,
        one_line_summary=project.one_line_summary,
        goal=state.get("current_goal"),
        handoff=state.get("last_handoff"),
        hurdles=hurdle_lines[-10:],
        journey=project.journey[-15:],
        decisions=project.decisions,
        completed_goals=state.get("completed_goals", []),
    )


@app.command()
def config(
    index: Optional[Path] = typer.Option(None, "--index", help="Set the path to your central portfolio repository"),
):
    """Manage global devlog configuration."""
    cfg = load_config()
    if index:
        cfg["index_path"] = str(index.expanduser().resolve())
        save_config(cfg)
        console.print(f"[green]Central index set to: {cfg['index_path']}[/green]")
    else:
        console.print(f"[bold]Current Config:[/bold]")
        console.print(f"  Index Path: [cyan]{cfg.get('index_path', 'Not set')}[/cyan]")


@app.command()
def onboard(slug: Optional[str] = typer.Option(None, "--slug")):
    """Orientation briefing for agents: tool overview, commands, and current project state."""
    try:
        projects_dir = get_projects_dir()
        parser = ProjectParser(projects_dir)
        active_slug = get_active_slug(slug)
        project = parser.parse(active_slug)
        state = load_project_state(Path.cwd())

        # Tool briefing
        console.print(Panel(
            "[bold]devlog[/bold] is a shared state engine between you (the agent) and the developer.\n"
            "It keeps [cyan]AGENTS.md[/cyan] as your working copy — [bold]read it now[/bold] for full context: goal, handoff, and journey history.\n"
            "Every write auto-commits to git.",
            title="[bold blue]Devlog — What This Tool Is[/bold blue]",
            expand=False,
        ))

        # Command cheatsheet
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
        table.add_column("Command")
        table.add_column("When to use it")
        table.add_row("[green]devlog status[/green]",             "Check current goal, handoff, and blockers")
        table.add_row("[green]devlog standup[/green]",            "Summarize current goal, recent progress, decisions, and blockers")
        table.add_row("[green]devlog goal --done[/green]",        "Mark the current goal as completed")
        table.add_row("[green]devlog goal --list[/green]",        "See active and completed goals")
        table.add_row("[green]devlog log \"...\"[/green]",        "Record a milestone (--type shipped|learning)")
        table.add_row("[green]devlog decide \"...\"[/green]",     "Log an architectural decision (--context \"why\")")
        table.add_row("[green]devlog block \"...\"[/green]",      "Log a blocker the next agent should know about")
        table.add_row("[green]devlog resolve \"...\"[/green]",    "Mark a blocker as fixed")
        table.add_row("[green]devlog handoff \"...\"[/green]",    "Leave a note before ending your session")
        console.print(Panel(table, title="[bold blue]Use These Commands Actively[/bold blue]", expand=False))

        # Current project state
        goal = state.get("current_goal") or "[dim]None[/dim]"
        handoff = state.get("last_handoff") or "[dim]None[/dim]"
        open_blockers = [h for h in project.hurdles if h.status == "open"]
        blockers_str = "\n".join(f"  • {h.text}" for h in open_blockers) if open_blockers else "[dim]None[/dim]"

        console.print(Panel(
            f"[bold]Project:[/bold] {project.title} ([dim]{active_slug}[/dim])\n"
            f"[bold]Goal:[/bold] {goal}\n"
            f"[bold]Last Handoff:[/bold] {handoff}\n"
            f"[bold]Active Blockers:[/bold]\n{blockers_str}",
            title="[bold blue]Current State[/bold blue]",
            expand=False,
        ))

        console.print("[dim]Treat devlog as your pocket notebook — log decisions, dead ends, breakthroughs, and blockers as they happen. Not just at the end.[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def link(slug: str):
    """Link directory to a project slug and create AGENTS.md."""
    config = load_config()
    current_path = str(Path.cwd())
    config["path_map"][current_path] = slug
    save_config(config)

    init_project_state(Path.cwd(), slug)
    sync_local_devlog(slug)
    console.print(f"[green]Linked {current_path} → {slug} and created AGENTS.md[/green]")


@app.command()
def unlink():
    """Remove the path mapping for the current directory."""
    config = load_config()
    current_path = str(Path.cwd())
    if current_path in config["path_map"]:
        slug = config["path_map"].pop(current_path)
        save_config(config)
        console.print(f"[yellow]Unlinked {current_path} (was → {slug})[/yellow]")
    else:
        console.print("[red]No mapping found for current directory.[/red]")


@app.command()
def status(slug: Optional[str] = typer.Option(None, "--slug")):
    """Orientation: reads AGENTS.md or the central index."""
    try:
        agents_path = Path.cwd() / "AGENTS.md"
        if agents_path.exists() and not slug:
            console.print(Panel(Markdown(agents_path.read_text()), title="Local Agent State"))
        else:
            projects_dir = get_projects_dir()
            parser = ProjectParser(projects_dir)
            active_slug = get_active_slug(slug)
            project = parser.parse(active_slug)
            state = load_project_state(Path.cwd())
            console.print(Panel(f"[bold green]{project.title}[/bold green] ({active_slug})", title="Central Index State"))
            if state.get("current_goal"):
                console.print(f"\n[bold blue]Goal:[/bold blue] {state['current_goal']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def goal(
    text: Optional[str] = typer.Argument(None),
    clear: bool = typer.Option(False, "--clear"),
    done: bool = typer.Option(False, "--done", help="Mark the current goal as completed"),
    list_goals: bool = typer.Option(False, "--list", help="Show active and completed goals"),
    slug: Optional[str] = typer.Option(None, "--slug"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Immediately push to the content branch to trigger AI review"),
):
    """Set, complete, or list goals."""
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    active_slug = get_active_slug(slug)
    state = load_project_state(Path.cwd())

    if list_goals:
        active = state.get("current_goal")
        completed = state.get("completed_goals", [])
        if active:
            console.print(f"[bold green]● Active:[/bold green] {active}")
        else:
            console.print("[dim]No active goal.[/dim]")
        if completed:
            console.print("\n[bold]Completed:[/bold]")
            for g in reversed(completed):
                console.print(f"  [dim]✓ {g['done_at']}[/dim]  {g['text']}")
        return

    if done:
        current = state.get("current_goal")
        if not current:
            console.print("[yellow]No active goal to mark done.[/yellow]")
            return
        completed = state.get("completed_goals", [])
        completed.append({"text": current, "done_at": date.today().isoformat()})
        state["completed_goals"] = completed
        state["current_goal"] = None
        save_project_state(Path.cwd(), state)
        parser.append_to_list(active_slug, "Developer Journey", f"Goal Done: {current}", commit_prefix="goal")
        if (Path.cwd() / "AGENTS.md").exists():
            sync_local_devlog(active_slug)
        console.print(f"[green]Goal completed:[/green] {current}")
    elif clear:
        state["current_goal"] = None
        console.print("[yellow]Current goal cleared.[/yellow]")
    elif text:
        if state.get("current_goal") == text:
            console.print(f"[blue]Goal unchanged:[/blue] {text}")
            return
        state["current_goal"] = text
        parser.append_to_list(active_slug, "Developer Journey", f"Goal Set: {text}", commit_prefix="goal")
        console.print(f"[blue]Goal set:[/blue] {text}")
    else:
        console.print(f"[blue]Current goal:[/blue] {state.get('current_goal', 'None')}")
        return

    save_project_state(Path.cwd(), state)
    if (Path.cwd() / "AGENTS.md").exists():
        sync_local_devlog(active_slug)

    if publish:
        with console.status("[bold blue]Pushing to content branch..."):
            parser._git_push()
        console.print("[bold green]✓ Pushed! AI review triggered.[/bold green]")


@app.command()
def block(
    text: str,
    internal: bool = typer.Option(False, "--internal"),
    slug: Optional[str] = typer.Option(None, "--slug"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Immediately push to the content branch to trigger AI review"),
):
    """Log a blocker."""
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    active_slug = get_active_slug(slug)
    parser.append_to_list(active_slug, "Blockers", text, is_internal=internal, commit_prefix="block")
    if (Path.cwd() / "AGENTS.md").exists():
        sync_local_devlog(active_slug)
    console.print("[red]Blocker logged.[/red]")

    if publish:
        with console.status("[bold blue]Pushing to content branch..."):
            parser._git_push()
        console.print("[bold green]✓ Pushed! AI review triggered.[/bold green]")


@app.command()
def resolve(
    text: str,
    slug: Optional[str] = typer.Option(None, "--slug"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Immediately push to the content branch to trigger AI review"),
):
    """Mark a blocker as fixed."""
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    active_slug = get_active_slug(slug)
    if parser.resolve_in_list(active_slug, "Blockers", text):
        parser.append_to_list(active_slug, "Developer Journey", f"Fixed: {text}", commit_prefix="fix")
        if (Path.cwd() / "AGENTS.md").exists():
            sync_local_devlog(active_slug)
        console.print(f"[green]Blocker resolved:[/green] {text}")

        if publish:
            with console.status("[bold blue]Pushing to content branch..."):
                parser._git_push()
            console.print("[bold green]✓ Pushed! AI review triggered.[/bold green]")
    else:
        console.print(f"[yellow]No active blocker matching '{text}' found.[/yellow]")


@app.command()
def handoff(
    text: Optional[str] = typer.Argument(None),
    clear: bool = typer.Option(False, "--clear"),
    slug: Optional[str] = typer.Option(None, "--slug"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Immediately push to the content branch to trigger AI review"),
):
    """Leave a handoff note or clear it."""
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    active_slug = get_active_slug(slug)
    state = load_project_state(Path.cwd())

    if clear:
        state["last_handoff"] = None
        console.print("[yellow]Handoff message cleared.[/yellow]")
    elif text:
        state["last_handoff"] = f"{date.today().isoformat()}: {text}"
        console.print("[yellow]Handoff saved.[/yellow]")
    else:
        console.print(f"[yellow]Last handoff:[/yellow] {state.get('last_handoff', 'None')}")
        return

    save_project_state(Path.cwd(), state)
    if (Path.cwd() / "AGENTS.md").exists():
        sync_local_devlog(active_slug)

    if publish:
        with console.status("[bold blue]Pushing to content branch..."):
            parser._git_push()
        console.print("[bold green]✓ Pushed! AI review triggered.[/bold green]")


@app.command()
def reset(slug: Optional[str] = typer.Option(None, "--slug")):
    """Reset goal and handoff for the current project."""
    active_slug = get_active_slug(slug)
    state = load_project_state(Path.cwd())
    state["current_goal"] = None
    state["last_handoff"] = None
    save_project_state(Path.cwd(), state)

    if (Path.cwd() / "AGENTS.md").exists():
        sync_local_devlog(active_slug)
    console.print("[bold yellow]Goal and handoff reset.[/bold yellow]")


@app.command()
def log(
    entry: str,
    internal: bool = typer.Option(False, "--internal"),
    type: Optional[str] = typer.Option(None, "--type", help="Entry type: shipped, learning"),
    slug: Optional[str] = typer.Option(None, "--slug"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Immediately push to the content branch to trigger AI review"),
):
    """Log an entry to the Developer Journey."""
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    active_slug = get_active_slug(slug)
    _PREFIXES = {"shipped": "Shipped", "learning": "Learned"}
    prefix = _PREFIXES.get(type or "", "")
    text = f"{prefix}: {entry}" if prefix else entry
    dated_entry = f"{date.today().isoformat()}: {text}"
    parser.append_to_list(active_slug, "Developer Journey", dated_entry, is_internal=internal)
    if (Path.cwd() / "AGENTS.md").exists():
        sync_local_devlog(active_slug)
    console.print(f"[green]Logged to {active_slug}[/green]")

    if publish:
        with console.status("[bold blue]Pushing to content branch..."):
            parser._git_push()
        console.print("[bold green]✓ Pushed! AI review triggered.[/bold green]")


@app.command()
def publish():
    """Push all local portfolio changes to the content branch to trigger AI review and update the rolling PR."""
    try:
        projects_dir = get_projects_dir()
        parser = ProjectParser(projects_dir)
        with console.status("[bold blue]Pushing to content branch..."):
            parser._git_push()
        console.print("[bold green]✓ Pushed! AI review triggered. Check your rolling PR on GitHub.[/bold green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def _is_on_or_after(value: Optional[str], since: date) -> bool:
    if not value:
        return False
    try:
        return date.fromisoformat(value) >= since
    except ValueError:
        return False


@app.command()
def standup(
    since: Optional[str] = typer.Option(None, "--since", help="Include dated activity on or after YYYY-MM-DD (default: today)"),
    limit: int = typer.Option(8, "--limit", help="Maximum recent activity entries to show"),
    slug: Optional[str] = typer.Option(None, "--slug"),
):
    """Aggregate the current project state into a standup summary."""
    try:
        projects_dir = get_projects_dir()
        parser = ProjectParser(projects_dir)
        active_slug = get_active_slug(slug)
        project = parser.parse(active_slug)
        state = load_project_state(Path.cwd())

        if since:
            try:
                since_date = date.fromisoformat(since)
            except ValueError:
                raise typer.BadParameter("--since must be a date in YYYY-MM-DD format")
        else:
            since_date = date.today()

        open_blockers = [h for h in project.hurdles if h.status == "open"]
        recent_entries = [e for e in project.journey if _is_on_or_after(e.date, since_date)]
        if not recent_entries:
            recent_entries = project.journey[-limit:]
        else:
            recent_entries = recent_entries[-limit:]

        recent_decisions = [
            d for d in project.decisions
            if d.visibility == "public" and (not d.date or _is_on_or_after(d.date, since_date))
        ]
        if not recent_decisions:
            recent_decisions = [d for d in project.decisions if d.visibility == "public"][-3:]

        console.print(Panel(
            f"[bold]Project:[/bold] {project.title} ([dim]{active_slug}[/dim])\n"
            f"[bold]Goal:[/bold] {state.get('current_goal') or '[dim]No active goal.[/dim]'}\n"
            f"[bold]Last Handoff:[/bold] {state.get('last_handoff') or '[dim]No handoff.[/dim]'}",
            title=f"[bold blue]Standup — since {since_date.isoformat()}[/bold blue]",
            expand=False,
        ))

        if recent_entries:
            table = Table(title="Recent Activity", show_lines=False)
            table.add_column("Date", style="dim", width=12)
            table.add_column("Kind", style="cyan", width=10)
            table.add_column("Entry")
            for e in recent_entries:
                internal_tag = " [dim][internal][/dim]" if e.visibility == "internal" else ""
                table.add_row(e.date or "", e.kind, f"{e.text}{internal_tag}")
            console.print(table)
        else:
            console.print("[dim]No journey entries logged yet.[/dim]")

        if recent_decisions:
            table = Table(title="Recent Decisions", show_lines=False)
            table.add_column("Date", style="dim", width=12)
            table.add_column("Decision")
            table.add_column("Context", style="dim")
            for d in recent_decisions[-3:]:
                table.add_row(d.date or "", d.text, d.context or "")
            console.print(table)

        if open_blockers:
            blocker_text = "\n".join(f"• {h.text}" for h in open_blockers)
            console.print(Panel(blocker_text, title="[bold red]Active Blockers[/bold red]", expand=False))
        else:
            console.print(Panel("[green]No active blockers.[/green]", title="[bold green]Active Blockers[/bold green]", expand=False))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def journey(
    oneline: bool = typer.Option(False, "--oneline", help="Compact one-liner format"),
    limit: int = typer.Option(0, "--limit", help="Show only the last N entries (0 = all)"),
    slug: Optional[str] = typer.Option(None, "--slug"),
):
    """Show the project's developer journey log."""
    try:
        projects_dir = get_projects_dir()
        parser = ProjectParser(projects_dir)
        active_slug = get_active_slug(slug)
        project = parser.parse(active_slug)
        entries = project.journey
        if limit > 0:
            entries = entries[-limit:]

        if oneline:
            for e in entries:
                date_str = e.date or "          "
                internal_tag = " \\[internal]" if e.visibility == "internal" else ""
                console.print(f"[dim]{date_str}[/dim] [cyan]\\[{e.kind}][/cyan]{internal_tag} {e.text}")
        else:
            table = Table(title=f"Developer Journey — {project.title}", show_lines=True)
            table.add_column("Date", style="dim", width=12)
            table.add_column("Kind", style="cyan", width=10)
            table.add_column("Vis", width=8)
            table.add_column("Entry")
            for e in entries:
                vis_color = "dim" if e.visibility == "internal" else "green"
                table.add_row(
                    e.date or "",
                    e.kind,
                    f"[{vis_color}]{e.visibility}[/{vis_color}]",
                    e.text,
                )
            console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def decide(
    text: str,
    context: Optional[str] = typer.Option(None, "--context", "-c", help="Why this decision was made"),
    internal: bool = typer.Option(False, "--internal"),
    slug: Optional[str] = typer.Option(None, "--slug"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Immediately push to the content branch to trigger AI review"),
):
    """Log an architectural decision (ADR-lite)."""
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    active_slug = get_active_slug(slug)
    entry = f"{date.today().isoformat()}: {text}"
    if context:
        entry += f" | {context}"
    parser.append_to_list(active_slug, "Decisions", entry, is_internal=internal, commit_prefix="decision")
    parser.append_to_list(active_slug, "Developer Journey", f"Decided: {text}", is_internal=internal, commit_prefix="decision")
    if (Path.cwd() / "AGENTS.md").exists():
        sync_local_devlog(active_slug)
    console.print(f"[blue]Decision logged:[/blue] {text}")

    if publish:
        with console.status("[bold blue]Pushing to content branch..."):
            parser._git_push()
        console.print("[bold green]✓ Pushed! AI review triggered.[/bold green]")


@app.command()
def decisions(slug: Optional[str] = typer.Option(None, "--slug")):
    """List architectural decisions for this project."""
    try:
        projects_dir = get_projects_dir()
        parser = ProjectParser(projects_dir)
        active_slug = get_active_slug(slug)
        project = parser.parse(active_slug)
        if not project.decisions:
            console.print("[dim]No decisions logged yet.[/dim]")
            return
        table = Table(title=f"Decisions — {project.title}", show_lines=True)
        table.add_column("Date", style="dim", width=12)
        table.add_column("Decision")
        table.add_column("Context", style="dim")
        for d in project.decisions:
            table.add_row(d.date or "", d.text, d.context or "")
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Sections devlog writes to — must exist with these exact names
_DEVLOG_SECTIONS = ["Developer Journey", "Blockers"]
# Sections required for the portfolio frontend
_REQUIRED_DISPLAY_SECTIONS = ["Stack"]


@app.command()
def validate(
    slug: Optional[str] = typer.Argument(None),
):
    """Validate project files: required fields, exact section names, date formats."""
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    files = [projects_dir / f"{slug}.md"] if slug else sorted(projects_dir.glob("*.md"))

    errors: list[str] = []
    warnings: list[str] = []

    for f in files:
        s = f.stem
        try:
            project = parser.parse(s)
        except Exception as e:
            errors.append(f"{s}: failed to parse: {e}")
            continue

        if not project.title:
            errors.append(f"{s}: missing `title` in frontmatter")
        if not project.one_line_summary:
            warnings.append(f"{s}: missing `one_line_summary` in frontmatter")

        for section in _REQUIRED_DISPLAY_SECTIONS:
            if section not in project.sections:
                warnings.append(f"{s}: missing `## {section}` section")

        for section in _DEVLOG_SECTIONS:
            if section not in project.sections:
                variants = [k for k in project.sections if k.startswith(section)]
                if variants:
                    errors.append(
                        f"{s}: has `## {variants[0]}` but devlog needs exact `## {section}` — rename it"
                    )
                else:
                    warnings.append(f"{s}: missing `## {section}` (will be created on first use)")

        for entry in project.journey:
            if entry.date and not _DATE_RE.match(entry.date):
                errors.append(f"{s}: journey entry has invalid date format: `{entry.date}`")

        for decision in project.decisions:
            if decision.date and not _DATE_RE.match(decision.date):
                errors.append(f"{s}: decision has invalid date format: `{decision.date}`")

    if errors:
        console.print(f"\n[bold red]✗ {len(errors)} error(s):[/bold red]")
        for e in errors:
            console.print(f"  [red]•[/red] {e}")
    if warnings:
        console.print(f"\n[bold yellow]⚠ {len(warnings)} warning(s):[/bold yellow]")
        for w in warnings:
            console.print(f"  [yellow]•[/yellow] {w}")
    if not errors and not warnings:
        console.print("[bold green]✓ All projects valid[/bold green]")

    if errors:
        raise typer.Exit(code=1)


@app.command()
def edit(slug: Optional[str] = typer.Argument(None)):
    """Open a project file in $EDITOR."""
    projects_dir = get_projects_dir()
    active_slug = get_active_slug(slug)
    project_path = projects_dir / f"{active_slug}.md"
    editor = os.environ.get("EDITOR", "nano")
    os.execlp(editor, editor, str(project_path))


@app.command()
def list():
    """List all projects."""
    projects_dir = get_projects_dir()
    parser = ProjectParser(projects_dir)
    table = Table(title="Developer Career Index")
    table.add_column("Slug", style="cyan")
    table.add_column("Title", style="green")
    for file in sorted(projects_dir.glob("*.md")):
        project = parser.parse(file.stem)
        table.add_row(project.slug, project.title)
    console.print(table)


@app.command()
def show(slug: str, json_output: bool = typer.Option(False, "--json")):
    """Show full details of a project."""
    try:
        projects_dir = get_projects_dir()
        parser = ProjectParser(projects_dir)
        project = parser.parse(slug)
        if json_output:
            console.print(project.model_dump_json(indent=2))
        else:
            console.print(Panel(project.title, style="bold green"))
            for h, b in project.sections.items():
                console.print(f"\n[bold cyan]## {h}[/bold cyan]\n{b}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def export(
    slug: Optional[str] = typer.Argument(None),
    output: Optional[Path] = typer.Option(None, "--out", help="Write JSON to file instead of stdout"),
):
    """Export sanitized project data as JSON (strips [INTERNAL] entries)."""
    try:
        projects_dir = get_projects_dir()
        parser = ProjectParser(projects_dir)
        files = [projects_dir / f"{slug}.md"] if slug else sorted(projects_dir.glob("*.md"))
        results = []
        for f in files:
            project = parser.parse(f.stem)
            results.append({
                "slug": project.slug,
                "title": project.title,
                "one_line_summary": project.one_line_summary,
                "sections": {
                    k: v for k, v in project.sections.items()
                    if k not in ("Developer Journey", "Blockers", "Decisions")
                },
                "hurdles": [
                    {"text": h.text, "status": h.status}
                    for h in project.hurdles
                    if h.visibility == "public"
                ],
                "decisions": [
                    {"text": d.text, "context": d.context, "date": d.date}
                    for d in project.decisions
                    if d.visibility == "public"
                ],
                "journey": [
                    {"text": e.text, "date": e.date, "kind": e.kind}
                    for e in project.journey
                    if e.visibility == "public"
                ],
            })

        payload = results[0] if slug else results
        out_json = json.dumps(payload, indent=2)

        if output:
            output.write_text(out_json)
            console.print(f"[green]Exported to {output}[/green]")
        else:
            console.print(out_json)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    app()
