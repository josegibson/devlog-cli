# devlog Roadmap

## What This Tool Is

devlog is a **meta state engine** for software projects. It captures not just what happened,
but why decisions were made, what was ruled out, when direction changed, and where things
are heading — structured well enough that any agent, developer, or system picking up the
project has genuine situational awareness, not just a log dump.

The primary consumers are coding agents and developers across sessions, providers, and time.
The primary outputs are `AGENTS.md` (in-repo context file) and `DEVLOG.json` (portfolio export).

---

## Design Principles

**Local-first.** All state lives in `.devlog/` inside the project repo. No external
dependencies to function. Data travels with the code when cloned.

**Git is the audit trail.** Every write auto-commits. Diffs are human-readable YAML lines,
not binary blobs. The history of decisions is the git log.

**Schema enforces meaning, not labels.** Agent drift is prevented by required structured
fields, not by trusting that agents interpret command names correctly.

**Frameworks over intuition.** Every schema field is derived from a battle-tested theory.
Nothing is invented.

**Portfolio is a consumer, not a dependency.** `DEVLOG.json` is committed to the repo root.
Portfolio systems read it via URL. devlog does not know or care about portfolio systems.

---

## Theoretical Foundations

Each entry type maps directly to an established framework.

| Entry | Framework | Key insight |
|---|---|---|
| `call` | ADR Y-statement (Zdun et al.) | Decisions need: context, alternatives rejected, goal pursued, tradeoff accepted |
| `snag` | Argyris double-loop learning | A blocker is only meaningful when linked to the assumption it threatens |
| `shift` | AAR (US Army) + Argyris | A pivot is an after-action review: intended vs actual, plus the governing variable that broke |
| `brief` | SBAR (healthcare handoffs) | Handoffs need four layers: Situation (L1), Background (L1), Assessment (L2), Recommendation (L3) |
| `aim` | Endsley Situation Awareness L3 | Goals need a projected end state, anticipated risks, and upcoming decision points |
| `arch` | C4 model (Simon Brown) | Architecture lives at Container level: independently deployable units and their relationships |
| `constraint` | arc42 Section 2 | Hard constraints box in all future decisions and must be surfaced explicitly |
| `debt` | Fowler/Cunningham quadrant | Debt is only manageable when classified by intent (deliberate/inadvertent) and prudence |
| `note` | Electronic Lab Notebook | Immutable, timestamped observations — the raw record |

### Situational Awareness model (Endsley)

All generated output (AGENTS.md) is structured around three levels:

- **L1 — Perception:** what is happening (current goal, open snags, recent activity)
- **L2 — Comprehension:** what it means (which snags threaten which calls, active assumptions)
- **L3 — Projection:** where this is heading (aim horizon, risks, next decision points, handoff recommendation)

---

## Command Reference

### v0.2.0 names (current) → v0.3.0 names (next)

| v0.2 | v0.3 | Role |
|---|---|---|
| `log` | `note` | Record a general observation or milestone |
| `decide` | `call` | Record an architectural decision |
| `decisions` | `calls` | List architectural decisions |
| `block` | `snag` | Log a blocker |
| `resolve` | `clear` | Mark a blocker as resolved |
| `handoff` | `brief` | Leave a structured handoff note |
| `journey` | `log` | View the activity log |
| `onboard` | `orient` | Agent orientation briefing |
| `goal` | `goal` | Set, complete, or list goals |
| `status` | `status` | Show current state via AGENTS.md |
| `standup` | `standup` | Aggregate standup summary |
| *(new)* | `shift` | Log a direction change (pivot) |
| *(new)* | `arch` | Describe current system architecture |
| *(new)* | `constraint` | Log a hard constraint |
| *(new)* | `debt` | Log technical debt |

---

## Full Schemas (v0.3.0 target)

### `call` — ADR Y-statement

```bash
devlog call "use JWT for stateless auth" \
  --context "distributed auth across 3 services with no shared session store" \
  --facing "need token verification without inter-service calls" \
  --over "session-based auth, OAuth server, mTLS" \
  --to-achieve "horizontal scalability and service independence" \
  --tradeoff "no server-side revocation without a token blocklist" \
  --status accepted \
  --supersedes "call-2024-01-10-basic-auth"
```

| Field | Y-statement clause | Required |
|---|---|---|
| text | the decision | yes |
| --context | "In the context of" | recommended |
| --facing | "facing" | recommended |
| --over | "and against" (comma-separated) | recommended |
| --to-achieve | "to achieve" | recommended |
| --tradeoff | "accepting that" | recommended |
| --status | proposed / accepted / superseded | default: accepted |
| --supersedes | ID of superseded call | optional |

---

### `snag` — Argyris governing variables

```bash
devlog snag "Postgres connection timeouts under load" \
  --threatens "call-2024-01-15-use-single-region-postgres" \
  --blocks "auth service going to production" \
  --impact high
```

| Field | Source | Required |
|---|---|---|
| text | the observable problem | yes |
| --threatens | call ID whose assumption is at risk | recommended |
| --blocks | concrete work blocked | optional |
| --impact | high / medium / low | default: medium |

---

### `shift` — AAR + Argyris double-loop

```bash
devlog shift \
  --from "REST API with per-resource endpoints" \
  --to "GraphQL with single schema" \
  --intended "ship auth service with REST by Friday" \
  --actual "frontend needed 6 round-trips per page; unacceptable performance" \
  --assumption-broke "REST per-resource design would be sufficient for frontend" \
  --sustain "auth logic itself is solid, keep it"
```

| Field | Source | Required |
|---|---|---|
| --from | old direction | yes |
| --to | new direction | yes |
| --intended | AAR Q1: what was supposed to happen | recommended |
| --actual | AAR Q2: what actually happened | recommended |
| --assumption-broke | Argyris: governing variable that broke | recommended |
| --sustain | AAR Q4: what to keep doing | optional |

---

### `brief` — SBAR

```bash
devlog brief \
  --situation "auth service deployed to staging, JWT flow working end-to-end" \
  --background "shifted from REST to GraphQL last week; Postgres timeout snag still open" \
  --assessment "timeout likely a connection pool config issue, not schema" \
  --recommendation "investigate pg pool before touching schema; do not merge auth PR until cleared"
```

| Field | SBAR | Endsley | Required |
|---|---|---|---|
| --situation | S | L1 | yes |
| --background | B | L1 | recommended |
| --assessment | A | L2 | recommended |
| --recommendation | R | L3 | recommended |

---

### `aim` — Endsley L3

```bash
devlog aim "ship auth service to production" \
  --horizon "SSO working across 3 services, latency under 200ms, zero session state" \
  --by "end of sprint 4" \
  --risk "Postgres timeout snag could invalidate DB call before launch" \
  --next-decision "whether to add token blocklist before launch"
```

| Field | Source | Required |
|---|---|---|
| text | the goal | yes |
| --horizon | L3: projected end state | recommended |
| --by | L3: time projection | optional |
| --risk | L3: what could break this | recommended |
| --next-decision | L3: upcoming choice point | optional |

---

### `arch` — C4 Container level

```bash
devlog arch "initial auth service architecture" \
  --containers "auth-service (Node.js), postgres (user store), redis (token blocklist)" \
  --relationships "auth-service → postgres for user store; auth-service → redis for blocklist" \
  --external "GitHub OAuth as identity provider" \
  --quality-goals "security: no plaintext credentials; scalability: stateless services" \
  --intent "move redis to managed cache before public launch"
```

| Field | Source | Required |
|---|---|---|
| text | snapshot description | yes |
| --containers | C4: independently deployable units | recommended |
| --relationships | C4: how containers connect | recommended |
| --external | C4 Context: external dependencies | optional |
| --quality-goals | arc42 Section 1.2: top NFRs | recommended |
| --intent | L3: where architecture is heading | optional |

---

### `constraint` — arc42 Section 2

```bash
devlog constraint "must run entirely on-prem, no cloud services" \
  --type organizational \
  --source "enterprise security policy, InfoSec team" \
  --impact "rules out managed DB, CDN, cloud auth providers"
```

| Field | Source | Required |
|---|---|---|
| text | the constraint | yes |
| --type | technical / organizational / regulatory / convention | default: technical |
| --source | who imposed it | recommended |
| --impact | what design freedom is lost | recommended |

---

### `debt` — Fowler/Cunningham quadrant

```bash
devlog debt "auth endpoints have no rate limiting" \
  --quadrant prudent-deliberate \
  --interest "DDoS risk under load; any abuse goes unchecked" \
  --principal "implement Redis rate limiter and middleware" \
  --fix-by "before public launch"
```

| Field | Source | Required |
|---|---|---|
| text | the debt item | yes |
| --quadrant | Fowler: prudent-deliberate / prudent-inadvertent / reckless-deliberate / reckless-inadvertent | default: prudent-deliberate |
| --interest | Cunningham: ongoing cost of carrying this | recommended |
| --principal | Cunningham: what payoff looks like | recommended |
| --fix-by | arc42 risk: commitment to resolve | recommended |

---

## Storage Model

```
my-project/
  .devlog/
    aims.yaml          # goals + L3 projection fields
    briefs.yaml        # SBAR handoffs
    calls.yaml         # ADR Y-statement decisions
    snags.yaml         # blockers + threat linkage
    shifts.yaml        # AAR + double-loop pivots
    debt.yaml          # Fowler quadrant items
    arch.yaml          # C4 container snapshots
    constraints.yaml   # arc42 hard constraints
    notes.yaml         # general log entries
  AGENTS.md            # generated — L1/L2/L3 layered context
  DEVLOG.json          # generated — portfolio export
  src/
  ...
```

**YAML with explicit IDs.** Every entry has an auto-generated ID in the format
`{type}-{YYYY-MM-DD}-{text-slug}`. Relationships are expressed as ID references
(e.g. `snag.threatens: call-2024-01-15-use-jwt`), not foreign keys in a database.

**Git-native.** Every devlog write auto-commits `.devlog/`, `AGENTS.md`, and `DEVLOG.json`.
Diffs are readable YAML line changes. The git log is a typed audit trail.

**No external dependencies.** No database, no server, no portfolio repo required.

---

## Portfolio Integration

devlog does not know about portfolio systems. `DEVLOG.json` is committed to the repo root
and readable at a plain HTTPS URL (e.g. `raw.githubusercontent.com/user/repo/main/DEVLOG.json`).

Portfolio systems register that URL and read it on demand — no webhooks, no monitoring,
no access to the local machine required. Data becomes visible when the developer pushes,
which is the natural boundary.

---

## AGENTS.md Structure (v0.4.0 target)

```markdown
# Agent Context

## Current Situation (L1)
Active goal, open snags, last handoff situation

## What It Means (L2)
Snags grouped by which calls they threaten.
Active assumptions surfaced from accepted calls.

## Where This Is Heading (L3)
Aim horizon, risk, next decision point.
Last handoff recommendation.

## Key Decisions
Last 5 accepted calls with tradeoffs.

## Known Debt
Open debt items with fix-by commitments.

## Recent Activity
Last 15 notes.

## Agent Instructions
How to use devlog commands.
```

---

## Version Roadmap

### v0.1.0 — Initial (shipped)
Central portfolio repo model. Old command names. Markdown bullet-point storage.

### v0.2.0 — Foundation (shipped)
- Local-first `.devlog/` storage with YAML per entry type
- All 9 Pydantic models
- `devlog init` replaces `devlog link`
- All commands rerouted to `.devlog/`
- Removed: `link`, `unlink`, `publish`, `--publish`, `config --index`
- Removed dependencies: `openai`, `python-frontmatter`

### v0.3.0 — Schema
- Rename all commands to final names (`call`, `snag`, `clear`, `brief`, `note`, `log`, `orient`, `shift`)
- Old names print deprecation warnings and delegate
- New commands: `shift`, `arch`, `constraint`, `debt`
- Full schemas on all commands (Y-statement, SBAR, AAR, Fowler, C4, arc42)
- `goal` enriched with L3 fields (`--horizon`, `--by`, `--risk`, `--next-decision`)

### v0.4.0 — Intelligence
- AGENTS.md rebuilt with explicit L1/L2/L3 sections
- L2 linkage: snags grouped by which calls they threaten
- L3 fields from `aim` surfaced as "Where This Is Heading"
- `brief` recommendation rendered as L3 in AGENTS.md
- `standup` shows L2 linkages
- `orient` shows full three-layer situational brief
- `DEVLOG.json` schema version bumped to 0.4.0

### v0.5.0 — Clean
- Remove all deprecated command aliases (old names introduced in v0.3)
- Remove `devlog/parser.py` (old Markdown bullet-point parser)
- Migration helper: `devlog migrate` reads old `projects/slug.md` and converts to `.devlog/` YAML
- All tests passing on clean install

### v1.0.0 — Stable
- README rewritten for new architecture
- CHANGELOG covering v0.1 through v1.0
- `validate` command covers all schema rules
- Published to PyPI
- Stable public API (no breaking changes without major version bump)
