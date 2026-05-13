# devlog Command Paradigm

This document explains the core idea behind `devlog` commands so the model can be
discussed, challenged, and improved.

## Core Idea

`devlog` is not a task tracker or a changelog. It is a **project state engine**.

The purpose is to capture enough structured context that a developer, coding agent,
or external tool can understand:

- what is happening now,
- why the project moved in this direction,
- what assumptions are active,
- what blocked progress,
- what tradeoffs were accepted,
- what should happen next.

The command set is built around semantic entry types rather than generic CRUD nouns.
Each command creates a typed record in `.devlog/*.yaml`. Generated files like
`AGENTS.md` and `.devlog/index.json` are projections of that canonical state.

## Design Principle: Commands Encode Meaning

The command names are intended to force better thinking.

For example:

- `call` is not just "write a decision"; it asks for decision context, rejected
  alternatives, intended goal, and accepted tradeoff.
- `snag` is not just "write a blocker"; it can identify which decision or assumption
  the blocker threatens.
- `brief` is not just "write a note"; it follows SBAR handoff structure.
- `shift` is not just "changed plan"; it captures intended vs actual outcome and the
  broken assumption.

The CLI should remain easy at the first tier, but the schema should make richer meaning
available as soon as it matters.

## Progressive Disclosure

The command paradigm has three usage tiers.

### Tier 1: Text Only

The user can record useful state with almost no ceremony:

```bash
devlog note "added pytest coverage"
devlog goal "ship v0.3 schema"
devlog snag "docs mention a command that does not exist"
devlog call "keep generated export inside .devlog/index.json"
```

Defaults carry the common case:

- decisions default to `accepted`,
- blockers default to `medium` impact,
- debt defaults to `prudent-deliberate`,
- visibility defaults to `public`,
- generated context still remains useful.

### Tier 2: Context Flags

When context matters, commands expose optional fields:

```bash
devlog call "use local .devlog YAML as source of truth" \
  --context "project state must travel with cloned repos" \
  --facing "agents need durable context across sessions" \
  --over "central portfolio repo, remote database" \
  --to-achieve "local-first operation and readable diffs" \
  --tradeoff "external consumers need a generated index"
```

```bash
devlog snag "ROADMAP documents milestone before CLI supports it" \
  --blocks "tagging v0.3 cleanly" \
  --impact high
```

This tier is where the system starts producing useful L2 comprehension: which problems
threaten which assumptions, what tradeoffs are active, and what work is blocked.

### Tier 3: Structural Entries

Some commands are for major project movement:

```bash
devlog shift \
  --from "root DEVLOG.json export" \
  --to ".devlog/index.json export" \
  --assumption-broke "portfolio export must live at repository root"
```

```bash
devlog arch "v0.3 local-first CLI architecture" \
  --containers "devlog CLI package, .devlog YAML store, AGENTS.md generator" \
  --quality-goals "local-first operation, readable diffs, high coverage"
```

```bash
devlog milestone "schema" \
  --version "v0.3.0" \
  --summary "final command names, rich schemas, milestone/timeline support"
```

These are less frequent, but they preserve the project arc.

## Command Types

### `note`

Records an immutable observation, milestone, shipped item, or learning.

Framework: electronic lab notebook.

Use when the fact matters, but it is not a decision, blocker, pivot, handoff, or debt item.

```bash
devlog note "expanded test suite to 27 tests" --type shipped
```

### `goal`

Records an active aim.

Framework: Endsley Situation Awareness L3.

The goal is not only "what I want"; it can also project:

- horizon: what done looks like,
- by: time horizon,
- risk: what could break it,
- next decision: upcoming choice point.

```bash
devlog goal "start v0.4 intelligence design" \
  --horizon "AGENTS.md separates L1/L2/L3" \
  --risk "current generator mixes perception and projection" \
  --next-decision "exact L1/L2/L3 layout"
```

### `call`

Records an architectural or product decision.

Framework: ADR Y-statement.

`call` is intentionally named as a judgment call. It captures:

- context,
- facing pressure,
- rejected alternatives,
- intended outcome,
- accepted tradeoff,
- status,
- supersession link.

```bash
devlog call "use events.jsonl as the temporal record" \
  --context "state is YAML in the repo" \
  --facing "agents need a command-level history without changing project git history" \
  --over "automatic git commits, external audit database" \
  --to-achieve "local append-only temporal history" \
  --tradeoff "users still need to commit .devlog files with project changes"
```

### `calls`

Lists recorded decisions.

This is a read model over `calls.yaml`.

### `snag`

Records a blocker or active problem.

Framework: Argyris double-loop learning.

A snag matters most when it threatens an assumption or decision.

```bash
devlog snag "coverage gate fails on milestone tests" \
  --threatens "call-2026-05-13-use-coverage-gate" \
  --blocks "tagging v0.3" \
  --impact high
```

### `clear`

Marks an open snag as cleared by text match.

```bash
devlog clear "coverage gate"
```

### `shift`

Records a direction change.

Framework: After Action Review plus Argyris double-loop learning.

A shift is stronger than a note. It says: the project changed course because reality
invalidated an assumption.

```bash
devlog shift \
  --from "compatibility aliases" \
  --to "breaking final command names" \
  --intended "avoid breaking users" \
  --actual "there are no external users yet" \
  --assumption-broke "aliases are needed before first public use" \
  --sustain "tests assert command surface directly"
```

### `brief`

Records a structured handoff.

Framework: SBAR.

Fields:

- situation: current facts,
- background: relevant history,
- assessment: what it means,
- recommendation: next action.

```bash
devlog brief \
  --situation "v0.3 commands implemented" \
  --background "v0.2 used old command names" \
  --assessment "tests now enforce new paradigm" \
  --recommendation "start v0.4 intelligence design"
```

### `arch`

Records a system architecture snapshot.

Framework: C4 container-level model.

The entry should describe independently meaningful units and relationships, not every
file or function.

```bash
devlog arch "local-first CLI architecture" \
  --containers "devlog CLI, .devlog YAML store, AGENTS.md generator" \
  --relationships "CLI writes YAML, generators rebuild projections" \
  --external "git, uv, GitHub Actions" \
  --quality-goals "readable diffs, no service dependency"
```

### `constraint`

Records a hard constraint.

Framework: arc42 Section 2.

Constraints explain lost design freedom.

```bash
devlog constraint "state must stay local-first" \
  --type technical \
  --source "design principles" \
  --impact "rules out required database or hosted API"
```

### `debt`

Records technical debt.

Framework: Fowler/Cunningham debt quadrant.

Debt needs both interest and principal:

- interest: what it costs to carry,
- principal: what payoff looks like.

```bash
devlog debt "edit command is thinly tested" \
  --quadrant prudent-deliberate \
  --interest "editor exec path has manual regression risk" \
  --principal "extract target resolution into testable helper" \
  --fix-by "before v1.0"
```

### `milestone`

Records a version boundary node.

Framework: event sourcing plus impact mapping.

Milestones make the project arc traversable. They can anchor calls and shifts by ID and
link to a parent milestone.

```bash
devlog milestone "schema" \
  --version "v0.3.0" \
  --achieved "2026-05-13" \
  --summary "final command names and rich schemas" \
  --parent "milestone-2026-05-13-v0-2-0"
```

### `timeline`

Renders milestones as a chronological project arc.

```bash
devlog timeline
```

### `status`, `standup`, `orient`, `log`, `validate`, `export`

These are read/projection commands:

- `status`: render generated agent context,
- `standup`: summarize current project state,
- `orient`: explain command usage and current state to an agent,
- `log`: view activity notes,
- `tension`: show derived decision confidence states,
- `validate`: check YAML integrity and relationship references,
- `export`: print or write the generated JSON index.

## Storage Model

Canonical state:

```text
.devlog/
  aims.yaml
  notes.yaml
  calls.yaml
  snags.yaml
  shifts.yaml
  briefs.yaml
  arch.yaml
  constraints.yaml
  debt.yaml
  milestones.yaml
  index.json
```

Generated projections:

```text
AGENTS.md
.devlog/index.json
```

`AGENTS.md` is for agents and humans inside the repo. `.devlog/index.json` is for tools
and portfolio consumers.

## Relationship Model

The model avoids a database. Relationships are plain ID references:

- `snag.threatens -> call.id`
- `call.supersedes -> call.id`
- `milestone.parent -> milestone.id`
- `milestone.calls[] -> call.id`
- `milestone.shifts[] -> shift.id`

This keeps the system local-first and git-readable while still allowing graph-like
navigation.

## Current Abstraction Questions

These are the places where better abstractions may be useful.

### 1. Is `goal` Really `aim`?

The storage model uses `Aim`, but the command is `goal` because it is more familiar.
This is a vocabulary mismatch. Possible directions:

- keep command as `goal` and model as `Aim`,
- rename command to `aim`,
- support both but make one canonical,
- introduce aliases only for human ergonomics, not semantic drift.

### 2. Are `note` Types Too Weak?

`note --type shipped|learning` is useful, but shipped items may deserve stronger
structure. `milestone` handles version boundaries, but not every shipped change is a
version boundary.

Possible abstraction: separate `event`, `note`, and `release`.

### 3. Should `milestone` Anchor IDs Automatically?

Today milestones accept explicit call and shift IDs. That is transparent but manual.

Possible abstraction: milestone creation could infer recent calls/shifts since the last
milestone, while still allowing explicit overrides.

### 4. Should `snag.threatens` Be Required for High Impact?

A blocker is more meaningful when linked to a threatened decision. But requiring that
too early raises friction.

Possible abstraction: validation warning for high-impact snags without `--threatens`.

### 5. Should `brief` Become the Main Session Boundary?

`brief` is currently a handoff command. It could become the formal session boundary:
start with `orient`, end with `brief`, and optionally summarize notes/calls/snags
created during the session.

Possible abstraction: `devlog session close`.

### 6. Do We Need a Query Layer?

As entries grow, commands like `calls`, `log`, and `timeline` may not be enough.

Possible abstraction:

```bash
devlog show call-...
devlog list snags --open
devlog graph --from milestone-...
```

### 7. Should Projections Be Versioned Separately?

The canonical schema and generated projection schema may evolve at different speeds.

Possible abstraction:

- `.devlog/schema.yaml` for local schema version,
- `.devlog/index.json` for external export schema version,
- migration commands that upgrade one or both.

## Success Criteria

The command paradigm is working if:

- a new agent can run `devlog status` and understand what matters,
- a developer can reconstruct why major decisions happened,
- blockers are connected to assumptions rather than floating as isolated complaints,
- version boundaries tell a coherent project story,
- external consumers can read `.devlog/index.json` without knowing internal YAML details,
- the CLI remains useful with simple text-only commands.

## Summary

The current abstraction is:

```text
typed commands -> YAML state -> generated projections -> git history
```

The design challenge is to keep the command surface small enough for daily use while
preserving enough structure for agents and tools to reason over the project.
