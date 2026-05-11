import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal

import frontmatter
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class Hurdle(BaseModel):
    text: str
    visibility: Literal["public", "internal"]
    status: Literal["open", "fixed"]


class Decision(BaseModel):
    text: str
    context: Optional[str] = None
    date: Optional[str] = None
    visibility: Literal["public", "internal"]


class JourneyEntry(BaseModel):
    text: str
    date: Optional[str]
    visibility: Literal["public", "internal"]
    kind: Literal["log", "goal_set", "goal_done", "fixed", "shipped", "learning", "decision"]


class Project(BaseModel):
    slug: str
    title: str
    one_line_summary: str = ""
    sections: Dict[str, str]
    hurdles: List[Hurdle]
    decisions: List[Decision]
    journey: List[JourneyEntry]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2}):\s*(.+)$")


def _parse_hurdle_line(line: str) -> Optional[Hurdle]:
    line = line.lstrip("- ").strip()
    if not line:
        return None
    internal = "[INTERNAL]" in line
    fixed = "[FIXED]" in line
    text = line.replace("[INTERNAL]", "").replace("[FIXED]", "").strip()
    return Hurdle(
        text=text,
        visibility="internal" if internal else "public",
        status="fixed" if fixed else "open",
    )


def _parse_decision_line(line: str) -> Optional[Decision]:
    line = line.lstrip("- ").strip()
    if not line:
        return None
    internal = "[INTERNAL]" in line
    text_full = line.replace("[INTERNAL]", "").strip()

    date = None
    m = _DATE_PREFIX.match(text_full)
    if m:
        date, text_full = m.group(1), m.group(2).strip()

    context = None
    if " | " in text_full:
        text_full, context = text_full.split(" | ", 1)
        text_full = text_full.strip()
        context = context.strip()

    return Decision(
        text=text_full,
        context=context,
        date=date,
        visibility="internal" if internal else "public",
    )


def _parse_journey_line(line: str) -> Optional[JourneyEntry]:
    line = line.lstrip("- ").strip()
    if not line:
        return None
    internal = "[INTERNAL]" in line
    text = line.replace("[INTERNAL]", "").strip()

    date = None
    m = _DATE_PREFIX.match(text)
    if m:
        date, text = m.group(1), m.group(2).strip()

    _PREFIXES = {
        "Goal Set:": "goal_set",
        "Goal Done:": "goal_done",
        "Fixed:": "fixed",
        "Shipped:": "shipped",
        "Learned:": "learning",
        "Decided:": "decision",
    }
    kind = "log"
    for prefix, k in _PREFIXES.items():
        if text.startswith(prefix):
            kind = k
            text = text[len(prefix):].strip()
            break

    return JourneyEntry(
        text=text,
        date=date,
        visibility="internal" if internal else "public",
        kind=kind,
    )


def _parse_list_section(content: str, parser_fn) -> list:
    results = []
    for line in content.split("\n"):
        if line.strip().startswith("- "):
            item = parser_fn(line)
            if item:
                results.append(item)
    return results


def _parse_sections(body: str) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    # Split on "## Header" at start of string or after a newline
    parts = re.split(r"(?:^|\n)##\s+", body)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n")
        header = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        sections[header] = content
    return sections


# ---------------------------------------------------------------------------
# ProjectParser
# ---------------------------------------------------------------------------

class ProjectParser:
    def __init__(self, projects_dir: Path):
        self.projects_dir = projects_dir

    def get_project_path(self, slug: str) -> Path:
        return self.projects_dir / f"{slug}.md"

    def _git_commit(self, message: str, file_path: Path):
        try:
            repo_root = self.projects_dir.parent
            subprocess.run(["git", "-C", str(repo_root), "add", str(file_path)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo_root), "commit", "-m", message], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass

    def _git_push(self):
        try:
            repo_root = self.projects_dir.parent
            # Push the local 'content' branch to 'origin/content'
            subprocess.run(["git", "-C", str(repo_root), "push", "origin", "content"], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git push failed: {e.stderr.decode().strip()}")

    def parse(self, slug: str) -> Project:
        path = self.get_project_path(slug)
        if not path.exists():
            raise FileNotFoundError(f"Project '{slug}' not found at {path}")

        post = frontmatter.load(str(path))
        meta = post.metadata
        body = post.content

        sections = _parse_sections(body)

        hurdles = _parse_list_section(sections.get("Blockers", ""), _parse_hurdle_line)
        decisions = _parse_list_section(sections.get("Decisions", ""), _parse_decision_line)
        journey = _parse_list_section(sections.get("Developer Journey", ""), _parse_journey_line)

        return Project(
            slug=meta.get("slug", slug),
            title=meta.get("title", slug),
            one_line_summary=meta.get("one_line_summary", ""),
            sections=sections,
            hurdles=hurdles,
            decisions=decisions,
            journey=journey,
        )

    def save(self, slug: str, project: Project, commit_msg: Optional[str] = None):
        path = self.get_project_path(slug)
        post = frontmatter.load(str(path))

        # Update frontmatter fields
        post["slug"] = project.slug
        post["title"] = project.title
        post["one_line_summary"] = project.one_line_summary

        # Rebuild body from sections
        lines = []
        for header, body in project.sections.items():
            lines.append(f"## {header}\n")
            lines.append(f"{body}\n")
        post.content = "\n".join(lines)

        path.write_text(frontmatter.dumps(post))
        if commit_msg:
            self._git_commit(commit_msg, path)

    def _update_section(self, slug: str, section_name: str, content: str, commit_msg: Optional[str] = None):
        """Low-level: replace a single section's raw text content and save."""
        path = self.get_project_path(slug)
        post = frontmatter.load(str(path))
        body = post.content

        sections = _parse_sections(body)
        sections[section_name] = content

        lines = []
        for header, body_part in sections.items():
            lines.append(f"## {header}\n")
            lines.append(f"{body_part}\n")
        post.content = "\n".join(lines)

        path.write_text(frontmatter.dumps(post))
        if commit_msg:
            self._git_commit(commit_msg, path)

    def append_to_list(self, slug: str, section_name: str, item: str, is_internal: bool = False, commit_prefix: str = "log"):
        project = self.parse(slug)
        section_content = project.sections.get(section_name, "")

        if is_internal:
            item = f"[INTERNAL] {item}"

        # Deduplicate: skip if this exact item is already the last entry
        existing_lines = [l.lstrip("- ").strip() for l in section_content.split("\n") if l.strip()]
        if existing_lines and existing_lines[-1] == item:
            return

        if section_content and not section_content.endswith("\n"):
            section_content += "\n"
        section_content += f"- {item}"

        self._update_section(
            slug, section_name, section_content,
            commit_msg=f"devlog: [{commit_prefix}] {slug} - {item[:50]}...",
        )

    def resolve_in_list(self, slug: str, section_name: str, search_text: str) -> bool:
        project = self.parse(slug)
        section_content = project.sections.get(section_name, "")
        if not section_content:
            return False

        lines = section_content.split("\n")
        new_lines = []
        found = False
        for line in lines:
            if search_text.lower() in line.lower() and "- " in line and "[FIXED]" not in line:
                new_lines.append(line.replace("- ", "- [FIXED] ", 1))
                found = True
            else:
                new_lines.append(line)

        if found:
            self._update_section(
                slug, section_name, "\n".join(new_lines),
                commit_msg=f"devlog: [resolve] {slug} - {search_text[:50]}...",
            )
        return found

    # --- AGENTS.md (Local State) Management ---

    def update_local_devlog(self, project_path: Path, slug: str, title: str,
                             one_line_summary: str = "", goal: str = None,
                             handoff: str = None, hurdles: List[str] = None,
                             journey: List["JourneyEntry"] = None,
                             decisions: List["Decision"] = None,
                             completed_goals: List[dict] = None):
        agents_path = project_path / "AGENTS.md"
        existing_content = agents_path.read_text() if agents_path.exists() else ""

        active_hurdles = [h for h in (hurdles or []) if "[FIXED]" not in h]

        journey_lines = []
        for e in (journey or []):
            date_str = f"{e.date} " if e.date else ""
            internal_tag = " [internal]" if e.visibility == "internal" else ""
            journey_lines.append(f"- {date_str}[{e.kind}]{internal_tag} {e.text}")

        completed_lines = []
        for g in list(reversed(completed_goals or []))[:3]:
            completed_lines.append(f"- ✓ {g['done_at']}: {g['text']}")

        decision_lines = []
        for d in (decisions or [])[-5:]:
            if d.visibility == "public":
                date_str = f"{d.date}: " if d.date else ""
                ctx = f" — {d.context}" if d.context else ""
                decision_lines.append(f"- {date_str}{d.text}{ctx}")

        goal_section = goal or "No active goal set."
        if completed_lines:
            goal_section += "\n\n**Completed:**\n" + "\n".join(completed_lines)

        managed_sections = {
            "🎯 Current Goal": goal_section,
            "🤝 Last Handoff": handoff or "No handoff instructions yet.",
            "⚠️ Active Blockers": "\n".join([f"- {h}" for h in active_hurdles]) if active_hurdles else "No active blockers.",
            "🧠 Key Decisions": "\n".join(decision_lines) if decision_lines else "No decisions logged yet.",
            "📜 Recent Journey": "\n".join(journey_lines) if journey_lines else "No journey entries yet.",
        }

        new_content = [
            f"# Agent Context: {title}\n",
            f"**Project Slug:** `{slug}`  \n",
        ]
        if one_line_summary:
            new_content.append(f"**Summary:** {one_line_summary}\n")
        new_content.append("\n> This file is auto-managed by `devlog`. Use `devlog journey` for the full log.\n")

        for header, body in managed_sections.items():
            new_content.append(f"\n## {header}\n")
            new_content.append(f"{body}\n")

        if "## 📋 Agent Instructions" in existing_content:
            instr_match = re.search(r"## 📋 Agent Instructions\n(.*?)(?=\n##|$)", existing_content, re.DOTALL)
            if instr_match:
                instructions = instr_match.group(1).strip()
                instructions = instructions.replace('devlog hurdle "..."', 'devlog block "..."')
                instructions = instructions.replace("once a hurdle is fixed", "once a blocker is fixed")
                new_content.append("\n## 📋 Agent Instructions\n")
                new_content.append(instructions + "\n")
        else:
            new_content.append("\n## 📋 Agent Instructions\n")
            new_content.append(
                "- Run `devlog onboard` at session start for full orientation.\n"
                "- Run `devlog journey` to see the full project history.\n"
                "- Use `devlog log \"...\"` to record breakthroughs (--type shipped|learning).\n"
                "- Use `devlog decide \"...\"` to log architectural decisions.\n"
                "- Use `devlog block \"...\"` to log blockers.\n"
                "- Use `devlog resolve \"...\"` once a blocker is fixed.\n"
                "- Use `devlog goal --done` to complete the current goal.\n"
                "- Use `devlog handoff \"...\"` before ending your session.\n"
                "- Never edit project files directly — always use the devlog CLI.\n"
            )

        other_sections = re.split(r"\n##\s+", existing_content)
        managed_headers = set(managed_sections.keys()) | {"📋 Agent Instructions", "📜 Agent Instructions", "⚠️ Active Hurdles"}
        for section in other_sections[1:]:
            header = section.split("\n")[0].strip()
            if header not in managed_headers:
                new_content.append(f"\n## {header}\n")
                new_content.append("\n".join(section.split("\n")[1:]).strip() + "\n")

        agents_path.write_text("\n".join(new_content))
