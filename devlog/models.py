from __future__ import annotations

import re
from datetime import date as _date
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def _slugify(text: str, max_len: int = 35) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


def make_id(prefix: str, text: str) -> str:
    return f"{prefix}-{_date.today().isoformat()}-{_slugify(text)}"


# ---------------------------------------------------------------------------
# Entry models
# ---------------------------------------------------------------------------

class Note(BaseModel):
    id: str
    date: str
    text: str
    kind: Literal["log", "shipped", "learning"] = "log"
    visibility: Literal["public", "internal"] = "public"


class Call(BaseModel):
    id: str
    date: str
    text: str
    context: Optional[str] = None
    facing: Optional[str] = None
    over: List[str] = Field(default_factory=list)
    to_achieve: Optional[str] = None
    tradeoff: Optional[str] = None
    status: Literal["proposed", "accepted", "superseded"] = "accepted"
    supersedes: Optional[str] = None
    visibility: Literal["public", "internal"] = "public"


class Snag(BaseModel):
    id: str
    date: str
    text: str
    threatens: Optional[str] = None  # references a Call.id
    blocks: Optional[str] = None
    impact: Literal["high", "medium", "low"] = "medium"
    status: Literal["open", "cleared"] = "open"
    visibility: Literal["public", "internal"] = "public"


class Shift(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    date: str
    from_: str = Field(..., alias="from")
    to: str
    intended: Optional[str] = None
    actual: Optional[str] = None
    assumption_broke: Optional[str] = None
    sustain: Optional[str] = None
    visibility: Literal["public", "internal"] = "public"


class Debt(BaseModel):
    id: str
    date: str
    text: str
    quadrant: Literal[
        "prudent-deliberate",
        "prudent-inadvertent",
        "reckless-deliberate",
        "reckless-inadvertent",
    ] = "prudent-deliberate"
    interest: Optional[str] = None
    principal: Optional[str] = None
    fix_by: Optional[str] = None
    status: Literal["open", "paid"] = "open"
    visibility: Literal["public", "internal"] = "public"


class Arch(BaseModel):
    id: str
    date: str
    text: str
    containers: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    external: List[str] = Field(default_factory=list)
    quality_goals: List[str] = Field(default_factory=list)
    intent: Optional[str] = None


class Constraint(BaseModel):
    id: str
    date: str
    text: str
    type: Literal["technical", "organizational", "regulatory", "convention"] = "technical"
    source: Optional[str] = None
    impact: Optional[str] = None


class Brief(BaseModel):
    id: str
    date: str
    situation: str
    background: Optional[str] = None
    assessment: Optional[str] = None
    recommendation: Optional[str] = None


class Aim(BaseModel):
    id: str
    date: str
    text: str
    horizon: Optional[str] = None
    by: Optional[str] = None
    risk: Optional[str] = None
    next_decision: Optional[str] = None
    status: Literal["active", "completed", "cleared"] = "active"
    done_at: Optional[str] = None


class Milestone(BaseModel):
    id: str
    date: str
    text: str
    version: Optional[str] = None
    achieved: Optional[str] = None
    summary: Optional[str] = None
    calls: List[str] = Field(default_factory=list)
    shifts: List[str] = Field(default_factory=list)
    parent: Optional[str] = None
