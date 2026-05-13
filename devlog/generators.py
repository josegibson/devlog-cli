from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from .models import Aim, Arch, Brief, Call, Constraint, Debt, Milestone, Note, Shift, Snag
from .storage import find_devlog_dir, read_all


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _build_threat_map(open_snags: list[Snag]) -> tuple[dict[str, list[Snag]], list[Snag]]:
    """Split open snags into {call_id: [snags]} and untethered (no threatens field)."""
    threatened: dict[str, list[Snag]] = {}
    untethered: list[Snag] = []
    for s in open_snags:
        if s.threatens:
            threatened.setdefault(s.threatens, []).append(s)
        else:
            untethered.append(s)
    return threatened, untethered


# ---------------------------------------------------------------------------
# Tension map
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    "a an the is are was were in on at to for of and or but not with by from"
    " this that we our its be have has had will would should could".split()
)


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 2}


def _assumption_overlaps(assumption_broke: str, *fields: Optional[str]) -> bool:
    broke_kw = _keywords(assumption_broke)
    for field in fields:
        if field and broke_kw & _keywords(field):
            return True
    return False


def derive_call_confidence(
    call: Call,
    open_snags: list[Snag],
    shifts: list[Shift],
    milestones: list[Milestone],
) -> tuple[str, list[str]]:
    """Return (confidence, reasons). Priority: confirmed > at-risk > degraded > nominal."""
    reasons: list[str] = []

    confirmed_at = [m for m in milestones if call.id in (m.calls or [])]
    if confirmed_at:
        for m in confirmed_at:
            reasons.append(f"Confirmed at: {m.version or m.text}")
        return "confirmed", reasons

    threatening = [s for s in open_snags if s.threatens == call.id]
    if threatening:
        for s in threatening:
            reasons.append(f"Snag: {s.text} [{s.impact}]")
        return "at-risk", reasons

    for shift in shifts:
        if shift.assumption_broke and _assumption_overlaps(
            shift.assumption_broke, call.facing, call.to_achieve, call.context
        ):
            reasons.append(f"Assumption broke: \"{shift.assumption_broke}\" → shifted to {shift.to}")
            return "degraded", reasons

    return "nominal", reasons


def generate_tension_map(devlog_dir: Optional[Path] = None) -> list[dict]:
    d = devlog_dir or find_devlog_dir()
    calls      = [c for c in read_all(Call, d) if c.status == "accepted"]
    snags      = read_all(Snag, d)
    shifts     = read_all(Shift, d)
    milestones = read_all(Milestone, d)
    open_snags = [s for s in snags if s.status == "open"]

    return [
        {
            "call_id":    c.id,
            "call_text":  c.text,
            "confidence": confidence,
            "reasons":    reasons,
        }
        for c in calls
        for confidence, reasons in [derive_call_confidence(c, open_snags, shifts, milestones)]
    ]


def write_tension_map(devlog_dir: Optional[Path] = None) -> Path:
    d = devlog_dir or find_devlog_dir()
    out_path = d / "tension.yaml"
    out_path.write_text(yaml.dump(generate_tension_map(d), allow_unicode=True, sort_keys=False))
    return out_path


# ---------------------------------------------------------------------------
# AGENTS.md — L1 / L2 / L3 render helpers
# ---------------------------------------------------------------------------

_CONFIDENCE_TAG = {
    "confirmed": " `[confirmed ✓]`",
    "at-risk":   " `[at-risk ⚠️]`",
    "degraded":  " `[degraded ↘]`",
    "nominal":   "",
}


def _render_l1(
    active_aim: Optional[Aim],
    latest_brief: Optional[Brief],
    recent_notes: list[Note],
) -> list[str]:
    lines: list[str] = ["\n## L1 Perception — Current State\n\n", "### Current Goal\n\n"]
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
            date_str = f"{n.date} " if n.date else ""
            kind_str = f"[{n.kind}] " if n.kind != "log" else ""
            int_tag  = " [internal]" if n.visibility == "internal" else ""
            lines.append(f"- {date_str}{kind_str}{n.text}{int_tag}\n")
    else:
        lines.append("No activity logged yet.\n")

    return lines


def _render_l2(
    constraints: list[Constraint],
    relevant_calls: list[Call],
    call_confidence: dict[str, tuple[str, list[str]]],
    open_snags: list[Snag],
    latest_brief: Optional[Brief],
    open_debt: list[Debt],
) -> list[str]:
    lines: list[str] = ["\n## L2 Comprehension — Meaning and Risk\n\n"]

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
            confidence, reasons = call_confidence.get(c.id, ("nominal", []))
            tag = _CONFIDENCE_TAG.get(confidence, "")
            lines.append(f"- **{c.date}** {c.text}{ctx}{tag}\n")
            if c.tradeoff:
                lines.append(f"  - *Tradeoff:* {c.tradeoff}\n")
            if c.over:
                lines.append(f"  - *Ruled out:* {', '.join(c.over)}\n")
            for reason in reasons:
                lines.append(f"  - ⚡ {reason}\n")
    else:
        lines.append("No decisions logged yet.\n")

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

    untethered = [s for s in open_snags if not s.threatens]
    if untethered:
        lines.append("\n### Open Snags (Untethered)\n\n")
        for s in untethered:
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

    return lines


def _render_l3(
    active_aim: Optional[Aim],
    latest_brief: Optional[Brief],
    shifts: list[Shift],
    milestones: list[Milestone],
) -> list[str]:
    lines: list[str] = ["\n## L3 Projection — Path Forward\n\n"]

    recent_broken = [s for s in shifts if s.assumption_broke][-3:]
    if recent_broken:
        lines.append("### Active Assumptions (Recently Broken)\n\n")
        for s in recent_broken:
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
            label     = item.version or item.text
            when      = item.achieved or item.date
            parent    = f" parent `{item.parent}`" if item.parent else ""
            anchors   = []
            if item.calls:
                anchors.append(f"{len(item.calls)} call(s)")
            if item.shifts:
                anchors.append(f"{len(item.shifts)} shift(s)")
            anchor_text = f" [{', '.join(anchors)}]" if anchors else ""
            lines.append(f"- **{when}** {label}: {item.summary or item.text}{anchor_text}{parent}\n")
    else:
        lines.append("\n### Milestone Timeline\n\nNo milestones recorded yet.\n")

    return lines


# ---------------------------------------------------------------------------
# AGENTS.md — top-level generator
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

    active_aim   = next((a for a in reversed(aims) if a.status == "active"), None)
    latest_brief = briefs[-1] if briefs else None
    open_snags   = [s for s in snags if s.status == "open"]

    relevant_calls = [
        c for c in calls
        if c.status == "accepted"
        or (c.status == "proposed" and any(s.threatens == c.id for s in open_snags))
    ]

    call_confidence: dict[str, tuple[str, list[str]]] = {
        c.id: derive_call_confidence(c, open_snags, shifts, milestones)
        for c in relevant_calls
    }

    lines: list[str] = [
        "# Agent Context\n\n",
        "> Auto-managed by `devlog`. Run `devlog orient` for full orientation.\n",
    ]
    lines += _render_l1(active_aim, latest_brief, notes[-15:])
    lines += _render_l2(constraints, relevant_calls, call_confidence, open_snags, latest_brief, open_debt)
    lines += _render_l3(active_aim, latest_brief, shifts, milestones)
    lines += [
        "\n## 📋 Agent Instructions\n\n",
        "- Run `devlog orient` at session start for full orientation.\n",
        "- Use `devlog note \"...\"` to record milestones (`--type shipped|learning`).\n",
        "- Use `devlog call \"...\"` to log architectural decisions.\n",
        "- Use `devlog snag \"...\"` to log blockers.\n",
        "- Use `devlog clear \"...\"` once a blocker is fixed.\n",
        "- Use `devlog goal --done` to complete the current goal.\n",
        "- Use `devlog brief --situation \"...\"` before ending your session.\n",
        "- Never edit `.devlog/` files directly — always use the devlog CLI.\n",
    ]
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

    def _pub(entries: list) -> list:
        return [
            e.model_dump(by_alias=True, exclude_none=True)
            for e in entries
            if getattr(e, "visibility", "public") == "public"
        ]

    return {
        "schema_version": "0.5.0",
        "exported_at":    date.today().isoformat(),
        "calls":          _pub(read_all(Call, d)),
        "snags":          _pub(read_all(Snag, d)),
        "shifts":         _pub(read_all(Shift, d)),
        "debt":           _pub(read_all(Debt, d)),
        "arch":           _pub(read_all(Arch, d)),
        "constraints":    _pub(read_all(Constraint, d)),
        "notes":          _pub(read_all(Note, d)),
        "briefs":         _pub(read_all(Brief, d)),
        "aims":           _pub(read_all(Aim, d)),
        "milestones":     _pub(read_all(Milestone, d)),
    }


def write_devlog_index(devlog_dir: Optional[Path] = None) -> Path:
    d = devlog_dir or find_devlog_dir()
    out_path = d / "index.json"
    out_path.write_text(json.dumps(generate_devlog_index(d), indent=2))
    return out_path
