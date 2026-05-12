# Agent Context

> Auto-managed by `devlog`. Run `devlog orient` for full orientation.

## 🎯 Current Goal

finish v0.3.0 schema release and prepare v0.4.0 intelligence

**Done looks like:** final command names, rich schema entries, .devlog/index.json export, tests and CI green, roadmap gaps made explicit
**Target:** before starting v0.4.0
**Risk:** ROADMAP.md now mentions milestone/timeline but the CLI does not implement them yet
**Next decision:** whether milestone/timeline belong in v0.3.0 or move to a later release

## 🤝 Last Brief

No brief recorded yet.

## ⚠️ Active Blockers

No active blockers.

## 🧠 Key Decisions

- **2026-05-13** Keep generated portfolio export inside .devlog/index.json — root should stay clean; tools can fetch one pretty-printed index from the devlog state directory
- **2026-05-13** Use local .devlog YAML as the canonical project state — devlog is a meta state engine that must travel with cloned repos and work without external services
  - *Tradeoff:* external portfolio consumers need a generated index rather than querying normalized storage
- **2026-05-13** Use git commits as the audit trail for every devlog write — devlog state is plain YAML and generated context files inside the project repo
  - *Tradeoff:* each CLI write creates commit noise that must be managed intentionally

## 📜 Recent Activity

- 2026-05-13 [shipped] Added pytest coverage for v0.2.0 CLI behavior: init, goals, logs, decisions, blockers, handoff, standup, validate, export, and git commits
- 2026-05-13 [shipped] Expanded v0.2.0 test suite to 23 tests with coverage reporting, 95.28% total coverage, CI workflow, and obsolete Markdown parser removal
- 2026-05-13 [shipped] Switched CLI and tests to v0.3.0 final command paradigm with note/call/calls/snag/clear/brief/log/orient plus shift, arch, constraint, and debt

## 📋 Agent Instructions

- Run `devlog orient` at session start for full orientation.
- Use `devlog note "..."` to record milestones (`--type shipped|learning`).
- Use `devlog call "..."` to log architectural decisions.
- Use `devlog snag "..."` to log blockers.
- Use `devlog clear "..."` once a blocker is fixed.
- Use `devlog goal --done` to complete the current goal.
- Use `devlog brief --situation "..."` before ending your session.
- Never edit `.devlog/` files directly — always use the devlog CLI.
