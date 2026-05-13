# devlog

A meta state engine for software projects. `devlog` gives AI coding agents structured, persistent context across sessions — and gives developers a lightweight way to track decisions, blockers, and handoffs without polluting git history.

## Install

```bash
pipx install devlog
```

For development:

```bash
uv run devlog --help
uv run pytest
```

## Quick start

```bash
devlog init                          # create .devlog/ in current directory
devlog goal "Ship payment API"       # set the active goal
devlog call "Use Stripe over Braintree" --context "better SDK"
devlog snag "Webhook timeout in staging" --impact high
devlog note "Stripe sandbox working end-to-end" --type shipped
devlog brief --situation "Webhooks passing, need prod keys"
devlog orient                        # full L1/L2/L3 orientation for agents
```

## How it works

Every command writes to plain YAML files under `.devlog/`. After each write, three derived files are regenerated:

| File | Purpose |
|---|---|
| `AGENTS.md` | Agent-readable context — L1 current state, L2 risk, L3 projection |
| `.devlog/tension.yaml` | Confidence map: `confirmed / at-risk / degraded / nominal` for each decision |
| `.devlog/index.json` | Public export for portfolio tools and external consumers |

State travels with the repo via normal user commits. `.devlog/events.jsonl` is the internal temporal record — every write appends a structured event so agents can reconstruct what happened and when.

## Command reference

| Command | What it does |
|---|---|
| `devlog init` | Initialize `.devlog/` in the current directory |
| `devlog orient` | Full L1/L2/L3 orientation (primary agent entry point) |
| `devlog status` | Compact status: goal, snags, recent notes |
| `devlog standup [--since YYYY-MM-DD]` | Standup summary filtered by date |
| `devlog goal "text"` | Set active goal |
| `devlog goal --done` | Mark current goal complete |
| `devlog goal --clear` | Discard current goal without marking done |
| `devlog goal --list` | List goal history |
| `devlog note "text"` | Log an activity note |
| `devlog note "text" --type shipped\|learning` | Log a typed note |
| `devlog call "text"` | Log an architectural decision |
| `devlog calls` | List all decisions |
| `devlog snag "text"` | Log a blocker |
| `devlog clear "text"` | Clear a blocker by text match |
| `devlog brief --situation "..."` | Record a handoff brief |
| `devlog brief` | Show latest brief |
| `devlog log [--limit N] [--oneline]` | Activity log |
| `devlog shift --from "X" --to "Y"` | Record a course correction |
| `devlog arch "text"` | Record architecture snapshot |
| `devlog constraint "text"` | Record a system constraint |
| `devlog debt "text"` | Record technical debt |
| `devlog milestone "text"` | Record a milestone |
| `devlog timeline` | Show milestone timeline |
| `devlog export [--out file.json]` | Export public state as JSON |
| `devlog validate` | Check YAML integrity |
| `devlog config` | Show current config |

### Progressive disclosure

**Tier 1 — text only** (most common):
```bash
devlog call "Use JWT over sessions"
devlog snag "Redis flaky in CI"
devlog note "Auth flow green"
```

**Tier 2 — context flags** (when the why matters):
```bash
devlog call "Use JWT over sessions" \
  --context "stateless scaling" \
  --over "sessions, cookies" \
  --tradeoff "token revocation complexity"

devlog snag "Redis flaky in CI" --impact high --blocks "deployment gate"
```

**Tier 3 — structural commands** (architecture and planning):
```bash
devlog arch "local-first CLI" \
  --containers "devlog CLI,.devlog storage" \
  --relationships "CLI writes YAML, generator writes index" \
  --external "git" \
  --quality-goals "readable diffs,offline use"

devlog milestone "v1.0" --version "v1.0.0" \
  --achieved 2026-05-13 \
  --summary "Stable public API"
```

## Storage

```
.devlog/
  aims.yaml           active and historical goals
  calls.yaml          architectural decisions
  snags.yaml          blockers (open and cleared)
  shifts.yaml         course corrections
  debt.yaml           technical debt
  arch.yaml           architecture snapshots
  constraints.yaml    system constraints
  briefs.yaml         handoff briefs
  notes.yaml          activity log
  milestones.yaml     project milestones
  events.jsonl        append-only temporal record
  index.json          public export (auto-generated)
  tension.yaml        decision confidence map (auto-generated)
AGENTS.md             agent orientation file (auto-generated)
```

All files are human-readable YAML. Commit them with your project — they are the record.

## For AI coding agents

At the start of every session:

```bash
devlog orient
```

This emits L1/L2/L3 structured context:
- **L1 Perception** — current goal, last brief, recent activity
- **L2 Comprehension** — constraints, decisions with confidence states, open blockers, debt
- **L3 Projection** — broken assumptions, goal horizon, recommended next move, milestone timeline

Agents should:
- Call `devlog orient` at session start
- Use `devlog note`, `devlog snag`, `devlog call` as they work
- Leave a `devlog brief --situation "..."` before ending the session
- Never edit `.devlog/` files directly

## Theoretical foundations

| Concept | Source |
|---|---|
| L1/L2/L3 situation awareness | Endsley (1995) — Toward a Theory of Situation Awareness |
| Decision logging | ADR pattern (Architecture Decision Records) |
| Tension map confidence | Cynefin-inspired signal aggregation |
| Progressive disclosure | Nielsen Norman Group UX research |
| Handoff brief | Military SMEAC / BLUF brief format |
