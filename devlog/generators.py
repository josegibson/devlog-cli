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
    constraints = read_all(Constraint, d)
    shifts      = read_all(Shift, d)

    active_aim    = next((a for a in reversed(aims) if a.status == "active"), None)
    latest_brief  = briefs[-1] if briefs else None
    open_snags    = [s for s in snags if s.status == "open"]
    
    # Decisions to show: all accepted + any proposed that are threatened
    # (Actually, let's just take all active/proposed calls for now to be safe)
    call_index = {c.id: c for c in calls}
    threatened_map: dict[str, list[Snag]] = {}
    untethered_snags: list[Snag] = []
    
    for s in open_snags:
        if s.threatens:
            threatened_map.setdefault(s.threatens, []).append(s)
        else:
            untethered_snags.append(s)

    # Show the last 5 relevant calls (accepted OR proposed+threatened)
    relevant_calls = [
        c for c in calls 
        if c.status == "accepted" or (c.status == "proposed" and c.id in threatened_map)
    ]
    recent_notes  = notes[-15:]

    lines: list[str] = []

    lines.append("# Agent Context\n\n")
    lines.append("> Auto-managed by `devlog`. Run `devlog orient` for full orientation.\n")

    # --- L1 Perception: raw/current observable state ---
    lines.append("\n## L1 Perception — Current State\n\n")
    lines.append("### Current Goal\n\n")
    if active_aim:
        lines.append(f"{active_aim.text}\n")
        if active_aim.by:
            lines.append(f"\n**Target:** {active_aim.by}\n")
    else:
        lines.append("No active goal set.\n")

    lines.append("\n### Last Brief\n\n")
    if latest_brief:
        lines.append(f"**Situation:** {latest_brief.situation}\n")
        if latest_brief.background:
            lines.append(f"**Background:** {latest_brief.background}\n")
    else:
        lines.append("No brief recorded yet.\n")

    lines.append("\n### Recent Activity\n\n")
    if recent_notes:
        for n in recent_notes:
            date_str  = f"{n.date} " if n.date else ""
            kind_str  = f"[{n.kind}] " if n.kind != "log" else ""
            int_tag   = " [internal]" if n.visibility == "internal" else ""
            lines.append(f"- {date_str}{kind_str}{n.text}{int_tag}\n")
    else:
        lines.append("No activity logged yet.\n")

    # --- L2 Comprehension: meaning, risks, decisions, constraints ---
    lines.append("\n## L2 Comprehension — Meaning and Risk\n\n")

    if constraints:
        lines.append("### Active Constraints\n\n")
        for c in constraints:
            lines.append(f"- [{c.id}] {c.text}\n")
            if c.impact:
                lines.append(f"  - *Impact:* {c.impact}\n")
        lines.append("\n")

    lines.append("### Key Decisions & Tension\n\n")
    if relevant_calls:
        for c in relevant_calls[-5:]:
            ctx = f" — {c.context}" if c.context else ""
            confidence_tag = " `[at-risk ⚠️]`" if c.id in threatened_map else ""
            lines.append(f"- **{c.date}** {c.text}{ctx}{confidence_tag}\n")
            if c.tradeoff:
                lines.append(f"  - *Tradeoff:* {c.tradeoff}\n")
            if c.over:
                lines.append(f"  - *Ruled out:* {', '.join(c.over)}\n")
            if c.id in threatened_map:
                for s in threatened_map[c.id]:
                    impact_tag = f" `[{s.impact}]`" if s.impact else ""
                    lines.append(f"  - ⚡ **Snag:** {s.text}{impact_tag}\n")
    else:
        lines.append("No decisions logged yet.\n")

    # Active assumptions: what accepted calls are currently betting on
    assumptions = [
        (c.text, c.to_achieve, c.facing)
        for c in relevant_calls[-5:]
        if c.status == "accepted" and (c.to_achieve or c.facing)
    ]
    if assumptions:
        lines.append("\n### Active Assumptions\n\n")
        for call_text, to_achieve, facing in assumptions:
            if to_achieve:
                lines.append(f"- Betting that **{to_achieve}** (via: {call_text})\n")
            if facing:
                lines.append(f"- Assumes **{facing}** is the real problem (via: {call_text})\n")

    if untethered_snags:
        lines.append("\n### Open Snags (Untethered)\n\n")
        for s in untethered_snags:
            impact_tag = f" `[{s.impact}]`" if s.impact else ""
            lines.append(f"- {s.text}{impact_tag}\n")
            if s.blocks:
                lines.append(f"  - blocks: {s.blocks}\n")

    lines.append("\n### Brief Assessment\n\n")
    if latest_brief and latest_brief.assessment:
        lines.append(f"{latest_brief.assessment}\n")
    else:
        lines.append("No assessment recorded yet.\n")

    if open_debt:
        lines.append("\n### Known Debt\n\n")
        for item in open_debt:
            lines.append(f"- [{item.quadrant}] {item.text}\n")
            if item.fix_by:
                lines.append(f"  - Fix by: {item.fix_by}\n")

    # --- L3 Projection: target state, next decision, timeline ---
    lines.append("\n## L3 Projection — Path Forward\n\n")
    
    if shifts:
        recent_shifts = [s for s in shifts if s.assumption_broke][-3:]
        if recent_shifts:
            lines.append("### Active Assumptions (Recently Broken)\n\n")
            for s in recent_shifts:
                lines.append(f"- Broken: \"{s.assumption_broke}\"\n")
                lines.append(f"  - *Shifted to:* {s.to}\n")
            lines.append("\n")

    lines.append("### Goal Horizon\n\n")
    if active_aim:
        if active_aim.horizon:
            lines.append(f"**Done looks like:** {active_aim.horizon}\n\n")
        if active_aim.risk:
            lines.append(f"**Risk:** {active_aim.risk}\n\n")
        if active_aim.next_decision:
            lines.append(f"**Next decision:** {active_aim.next_decision}\n\n")
    else:
        lines.append("No active projection.\n")

    lines.append("\n### Recommended Next Move\n\n")
    if latest_brief and latest_brief.recommendation:
        lines.append(f"**Recommendation:** {latest_brief.recommendation}\n")
    else:
        lines.append("No recommendation recorded yet.\n")

    if milestones:
        lines.append("\n### Milestone Timeline\n\n")
        for item in milestones[-5:]:
            label = item.version or item.text
            when = item.achieved or item.date
            parent = f" parent `{item.parent}`" if item.parent else ""
            anchors = []
            if item.calls:
                anchors.append(f"{len(item.calls)} call(s)")
            if item.shifts:
                anchors.append(f"{len(item.shifts)} shift(s)")
            anchor_text = f" [{', '.join(anchors)}]" if anchors else ""
            lines.append(f"- **{when}** {label}: {item.summary or item.text}{anchor_text}{parent}\n")
    else:
        lines.append("\n### Milestone Timeline\n\nNo milestones recorded yet.\n")

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
        "schema_version": "0.5.0",
        "exported_at": date.today().isoformat(),
        "calls":       _dump([c for c in read_all(Call, d) if c.visibility == "public"]),
        "snags":       _dump([s for s in read_all(Snag, d) if s.visibility == "public"]),
        "shifts":      _dump([s for s in read_all(Shift, d) if s.visibility == "public"]),
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
