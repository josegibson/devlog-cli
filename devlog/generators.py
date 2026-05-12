from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from .models import Aim, Arch, Brief, Call, Constraint, Debt, Milestone, Note, Shift, Snag
from .storage import find_devlog_dir, read_all


# ---------------------------------------------------------------------------
# AGENTS.md
# ---------------------------------------------------------------------------

def generate_agents_md(devlog_dir: Optional[Path] = None) -> str:
    d = devlog_dir or find_devlog_dir()

    aims        = read_all(Aim, d)
    briefs      = read_all(Brief, d)
    calls       = read_all(Call, d)
    snags       = read_all(Snag, d)
    notes       = read_all(Note, d)
    open_debt   = [e for e in read_all(Debt, d) if e.status == "open"]
    milestones  = read_all(Milestone, d)

    active_aim    = next((a for a in reversed(aims) if a.status == "active"), None)
    latest_brief  = briefs[-1] if briefs else None
    open_snags    = [s for s in snags if s.status == "open"]
    accepted_calls = [c for c in calls if c.status == "accepted"]
    recent_notes  = notes[-15:]

    # Build a call lookup for snag threat resolution
    call_index = {c.id: c for c in calls}

    lines: list[str] = []

    lines.append("# Agent Context\n\n")
    lines.append("> Auto-managed by `devlog`. Run `devlog orient` for full orientation.\n")

    # --- Current Goal (L1 + L3) ---
    lines.append("\n## 🎯 Current Goal\n\n")
    if active_aim:
        lines.append(f"{active_aim.text}\n")
        if active_aim.horizon:
            lines.append(f"\n**Done looks like:** {active_aim.horizon}\n")
        if active_aim.by:
            lines.append(f"**Target:** {active_aim.by}\n")
        if active_aim.risk:
            lines.append(f"**Risk:** {active_aim.risk}\n")
        if active_aim.next_decision:
            lines.append(f"**Next decision:** {active_aim.next_decision}\n")
    else:
        lines.append("No active goal set.\n")

    # --- Last Handoff (SBAR) ---
    lines.append("\n## 🤝 Last Brief\n\n")
    if latest_brief:
        lines.append(f"**Situation:** {latest_brief.situation}\n")
        if latest_brief.background:
            lines.append(f"**Background:** {latest_brief.background}\n")
        if latest_brief.assessment:
            lines.append(f"**Assessment:** {latest_brief.assessment}\n")
        if latest_brief.recommendation:
            lines.append(f"**Recommendation:** {latest_brief.recommendation}\n")
    else:
        lines.append("No brief recorded yet.\n")

    # --- Active Blockers (L2: threaten calls) ---
    lines.append("\n## ⚠️ Active Blockers\n\n")
    if open_snags:
        for s in open_snags:
            impact_tag = f" `[{s.impact}]`" if s.impact else ""
            lines.append(f"- {s.text}{impact_tag}\n")
            if s.threatens:
                threatened = call_index.get(s.threatens)
                label = f"`{s.threatens}`"
                if threatened:
                    label = f'"{threatened.text}" (`{s.threatens}`)'
                lines.append(f"  - ⚡ threatens call: {label}\n")
            if s.blocks:
                lines.append(f"  - blocks: {s.blocks}\n")
    else:
        lines.append("No active blockers.\n")

    # --- Key Decisions ---
    lines.append("\n## 🧠 Key Decisions\n\n")
    if accepted_calls:
        for c in accepted_calls[-5:]:
            ctx = f" — {c.context}" if c.context else ""
            lines.append(f"- **{c.date}** {c.text}{ctx}\n")
            if c.tradeoff:
                lines.append(f"  - *Tradeoff:* {c.tradeoff}\n")
    else:
        lines.append("No decisions logged yet.\n")

    # --- Known Debt ---
    if open_debt:
        lines.append("\n## 💳 Known Debt\n\n")
        for item in open_debt:
            lines.append(f"- [{item.quadrant}] {item.text}\n")
            if item.fix_by:
                lines.append(f"  - Fix by: {item.fix_by}\n")

    # --- Milestones ---
    if milestones:
        lines.append("\n## 🧭 Milestones\n\n")
        for item in milestones[-5:]:
            label = item.version or item.text
            achieved = f" ({item.achieved})" if item.achieved else ""
            lines.append(f"- {label}{achieved}: {item.summary or item.text}\n")

    # --- Recent Activity ---
    lines.append("\n## 📜 Recent Activity\n\n")
    if recent_notes:
        for n in recent_notes:
            date_str  = f"{n.date} " if n.date else ""
            kind_str  = f"[{n.kind}] " if n.kind != "log" else ""
            int_tag   = " [internal]" if n.visibility == "internal" else ""
            lines.append(f"- {date_str}{kind_str}{n.text}{int_tag}\n")
    else:
        lines.append("No activity logged yet.\n")

    # --- Agent Instructions ---
    lines.append("\n## 📋 Agent Instructions\n\n")
    lines.append("- Run `devlog orient` at session start for full orientation.\n")
    lines.append("- Use `devlog note \"...\"` to record milestones (`--type shipped|learning`).\n")
    lines.append("- Use `devlog call \"...\"` to log architectural decisions.\n")
    lines.append("- Use `devlog snag \"...\"` to log blockers.\n")
    lines.append("- Use `devlog clear \"...\"` once a blocker is fixed.\n")
    lines.append("- Use `devlog goal --done` to complete the current goal.\n")
    lines.append("- Use `devlog brief --situation \"...\"` before ending your session.\n")
    lines.append("- Never edit `.devlog/` files directly — always use the devlog CLI.\n")

    return "".join(lines)


def write_agents_md(devlog_dir: Optional[Path] = None) -> Path:
    d = devlog_dir or find_devlog_dir()
    agents_path = d.parent / "AGENTS.md"
    agents_path.write_text(generate_agents_md(d))
    return agents_path


# ---------------------------------------------------------------------------
# devlog index export
# ---------------------------------------------------------------------------

def generate_devlog_index(devlog_dir: Optional[Path] = None) -> dict:
    d = devlog_dir or find_devlog_dir()

    def _dump(entries: list) -> list:
        return [e.model_dump(by_alias=True, exclude_none=True) for e in entries]

    return {
        "schema_version": "0.3.0",
        "exported_at": date.today().isoformat(),
        "calls":       _dump(read_all(Call, d)),
        "snags":       _dump([s for s in read_all(Snag, d) if s.visibility == "public"]),
        "shifts":      _dump(read_all(Shift, d)),
        "debt":        _dump([e for e in read_all(Debt, d) if e.visibility == "public"]),
        "arch":        _dump(read_all(Arch, d)),
        "constraints": _dump(read_all(Constraint, d)),
        "notes":       _dump([n for n in read_all(Note, d) if n.visibility == "public"]),
        "briefs":      _dump(read_all(Brief, d)),
        "aims":        _dump(read_all(Aim, d)),
        "milestones":  _dump(read_all(Milestone, d)),
    }


def write_devlog_index(devlog_dir: Optional[Path] = None) -> Path:
    d = devlog_dir or find_devlog_dir()
    out_path = d / "index.json"
    out_path.write_text(json.dumps(generate_devlog_index(d), indent=2))
    return out_path
