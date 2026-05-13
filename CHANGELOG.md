# Changelog

## [1.0.0] — 2026-05-13

First stable release. Public API is locked.

### Added
- `events.jsonl` — append-only temporal record inside `.devlog/`. Every write appends a structured event `{ts, op, id, summary}`. Replaces git auto-commits as the temporal record.
- `tension.yaml` — derived confidence map for accepted decisions: `confirmed` (in milestone.calls), `at-risk` (open snag threatens it), `degraded` (shift assumption overlaps call fields), `nominal`.
- `devlog tension` command — prints the confidence map as a table.
- `devlog timeline` command — shows milestone timeline.
- `devlog arch` command — records architecture snapshots with containers, relationships, external systems, quality goals.
- `devlog constraint` command — records system constraints with type, source, impact.
- `devlog debt` command — records technical debt with quadrant, interest, principal, fix-by.
- `devlog milestone` command — records milestones with version, achieved date, linked calls and shifts.
- `devlog shift` command — records course corrections with from/to, intended/actual outcome, broken assumption.
- L1/L2/L3 structure in `AGENTS.md` and `devlog orient` / `devlog standup` output based on Endsley situation awareness model.
- Active Assumptions section in L2 derived from `call.to_achieve` and `call.facing`.
- Tension map confidence states rendered in L2 decisions list.
- `uncommitted_devlog_files()` in storage — `devlog status` warns when devlog files have uncommitted changes.
- `visibility: public|internal` on all 10 entry models. Internal entries are filtered from `index.json` export.

### Changed
- Removed all git auto-commits. State travels with the repo via natural user commits.
- `devlog orient` replaces `devlog onboard` / `devlog handoff` (v0.2 aliases removed).
- `devlog calls` replaces `devlog decisions`.
- `devlog log` replaces `devlog journey`.
- `devlog snag` / `devlog clear` replace `devlog block` / `devlog resolve`.
- `devlog brief` replaces `devlog handoff` for handoff briefs.
- Enum validation now uses `click.Choice` (exit code 2) instead of manual checks (exit code 1).
- `generate_agents_md` split into `_render_l1`, `_render_l2`, `_render_l3` helpers.
- `_build_threat_map` extracted as a shared helper used by standup, orient, and generator.
- `schema_version` in `index.json` export is now `"0.5.0"` (semver-aligned with data schema, separate from CLI version).

### Removed
- `git_commit()` from storage — no longer needed.
- `devlog decide` / `devlog decisions` / `devlog block` / `devlog resolve` / `devlog handoff` / `devlog journey` / `devlog onboard` — all v0.2 aliases.

---

## [0.5.0] — 2026-05-12

### Added
- `events.jsonl` temporal record (pre-release version).
- Tension map generation.
- `visibility` field on all models.
- `HasText` structural protocol in models.

---

## [0.4.0] — 2026-05-11

### Added
- `devlog arch`, `devlog constraint`, `devlog debt`, `devlog milestone` commands.
- `devlog shift` for course corrections.
- L3 Projection layer in `AGENTS.md` and orient output.
- `devlog timeline` command.

---

## [0.3.0] — 2026-05-10

### Added
- `devlog brief` with situation/background/assessment/recommendation fields.
- `devlog orient` command (L1/L2 output).
- `devlog standup --since YYYY-MM-DD` date filter.
- `devlog validate` for YAML integrity checks.
- `devlog export --out file.json` file output option.

### Changed
- `devlog calls` replaces `devlog decisions`.
- `devlog log` replaces `devlog journey`.
- `devlog snag` / `devlog clear` replace `devlog block` / `devlog resolve`.

---

## [0.2.0] — 2026-05-05

### Added
- `devlog call` for architectural decisions with context, tradeoffs, alternatives.
- `devlog snag` / `devlog resolve` for blocker tracking.
- `devlog decisions` / `devlog journey` read commands.
- `devlog handoff` / `devlog onboard` session handoff.
- `--internal` visibility flag on notes and blockers.

---

## [0.1.0] — 2026-04-28

Initial release.

### Added
- `devlog init`, `devlog goal`, `devlog note`, `devlog status`, `devlog standup`.
- Local YAML storage under `.devlog/`.
- `AGENTS.md` auto-generation.
- `index.json` public export.
