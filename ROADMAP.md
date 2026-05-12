# devlog Roadmap

`devlog` is a meta state engine for software projects. Its detailed project state now lives
in this repository's own `.devlog/` files and generated `.devlog/index.json`; this file is
kept as a compact orientation document, not a second source of truth.

## Source of Truth

Use the CLI for current state:

```bash
devlog status
devlog timeline
devlog calls
devlog log
devlog orient
```

The generated export for tools and portfolio consumers is:

```text
.devlog/index.json
```

## Principles

- Local-first: project state lives under `.devlog/` and travels with the repo.
- Git-native: every write updates generated context and creates a readable git commit.
- Schema-first: entries use structured fields derived from ADR Y-statements, SBAR,
  AAR, Endsley situation awareness, C4, arc42, and Fowler/Cunningham debt.
- Progressive disclosure: text-only commands work immediately; richer flags add L2/L3
  meaning when needed.
- Portfolio is a consumer: external systems fetch `.devlog/index.json`; devlog does
  not depend on portfolio infrastructure.

## Current Command Surface

| Command | Role |
|---|---|
| `note` | Record an observation or shipped/learning milestone |
| `call` / `calls` | Record and list architectural decisions |
| `snag` / `clear` | Track and resolve blockers |
| `brief` | Leave structured SBAR handoff context |
| `goal` | Set, complete, clear, or list aims |
| `log` | View activity notes |
| `orient` / `status` / `standup` | Read current project context |
| `shift` | Record a direction change |
| `arch` | Record a C4 container-level architecture snapshot |
| `constraint` | Record a hard design constraint |
| `debt` | Record technical debt |
| `milestone` / `timeline` | Record and render version boundary nodes |
| `validate` / `export` | Check and export devlog state |

## Version Arc

The detailed version arc is stored in `.devlog/milestones.yaml` and rendered with:

```bash
devlog timeline
```

Current high-level arc:

- `v0.1.0`: initial extraction.
- `v0.2.0`: local-first foundation.
- `v0.3.0`: final command names, rich schemas, milestone/timeline support, tests, CI.
- `v0.4.0`: planned explicit L1/L2/L3 intelligence in generated context.
- `v0.5.0`: planned migration and cleanup release.
- `v1.0.0`: planned stable API, changelog, validation completeness, and PyPI release.

## Maintenance Rule

When direction changes, record it first with `devlog call`, `devlog shift`,
`devlog constraint`, `devlog debt`, or `devlog milestone`. Update this file only when
the high-level orientation itself changes.
