# Agent Context

> Auto-managed by `devlog`. Run `devlog orient` for full orientation.

## 🎯 Current Goal

No active goal set.

## 🤝 Last Brief

**Situation:** Milestone/timeline implementation is complete and most roadmap information has been migrated into structured devlog entries
**Background:** ROADMAP.md had grown into a second state store covering foundations, schemas, milestones, future releases, constraints, and design principles
**Assessment:** The canonical project state is now .devlog YAML plus .devlog/index.json; ROADMAP.md should remain a compact orientation document rather than duplicate entry details
**Recommendation:** Use devlog status, timeline, calls, and log for current state; keep ROADMAP.md short and update devlog first for future decisions

## ⚠️ Active Blockers

No active blockers.

## 🧠 Key Decisions

- **2026-05-13** Use git commits as the audit trail for every devlog write — devlog state is plain YAML and generated context files inside the project repo
  - *Tradeoff:* each CLI write creates commit noise that must be managed intentionally
- **2026-05-13** Derive devlog entry schemas from established frameworks — agent drift is prevented by structured fields rather than vague command names
  - *Tradeoff:* the schema is richer than casual note taking and needs progressive disclosure
- **2026-05-13** Use progressive disclosure for the CLI interface — users and agents should get value from text-only commands while richer context remains available through flags
  - *Tradeoff:* some entries will be sparse and AGENTS.md must degrade gracefully
- **2026-05-13** Use final v0.3 command names without deprecated aliases — the tool has no external users yet and compatibility does not matter more than vocabulary clarity
  - *Tradeoff:* local scripts using v0.2 command names will break
- **2026-05-13** Keep the Python package at the repository root as devlog — the package is small and the user explicitly preferred not adding a src/devlog nesting layer
  - *Tradeoff:* tests need configuration discipline so imports do not mask packaging issues

## 💳 Known Debt

- [prudent-deliberate] edit command is intentionally thinly tested because it execs into an editor
  - Fix by: before packaging v1.0
- [prudent-deliberate] v0.4 intelligence rendering is not implemented yet
  - Fix by: v0.4.0
- [prudent-deliberate] README and ROADMAP need a final pass after deciding milestone and timeline scope
  - Fix by: before tagging v0.3.0
- [prudent-deliberate] v0.4 intelligence release remains unimplemented
  - Fix by: v0.4.0
- [prudent-deliberate] migration helper for old projects is not implemented
  - Fix by: v0.5.0
- [prudent-deliberate] stable release packaging is pending
  - Fix by: v1.0.0

## 🧭 Milestones

- v0.2.0 (2026-05-13): Local-first .devlog YAML storage, generated AGENTS.md and .devlog/index.json, Pydantic models, init workflow, and obsolete parser removal
- v0.3.0 (2026-05-13): Final command names, rich schemas, shift/arch/constraint/debt/milestone/timeline commands, coverage gate, and CI
- v0.4.0: Planned AGENTS.md, standup, and orient rewrite around explicit L1 perception, L2 comprehension, and L3 projection
- v0.5.0: Planned cleanup release for migration helper, deprecated-removal aftermath, and clean install verification
- v1.0.0: Planned stable release with rewritten README, changelog, full validation, PyPI publishing, and stable public API

## 📜 Recent Activity

- 2026-05-13 [shipped] Added pytest coverage for v0.2.0 CLI behavior: init, goals, logs, decisions, blockers, handoff, standup, validate, export, and git commits
- 2026-05-13 [shipped] Expanded v0.2.0 test suite to 23 tests with coverage reporting, 95.28% total coverage, CI workflow, and obsolete Markdown parser removal
- 2026-05-13 [shipped] Switched CLI and tests to v0.3.0 final command paradigm with note/call/calls/snag/clear/brief/log/orient plus shift, arch, constraint, and debt
- 2026-05-13 [shipped] v0.2.0 foundation shipped: local .devlog YAML storage, generated AGENTS.md and .devlog/index.json, all Pydantic models, init-based setup, and central repo dependencies removed
- 2026-05-13 [shipped] v0.3.0 schema work implemented in code: final command names, richer call/snag/brief/goal fields, and new shift/arch/constraint/debt commands
- 2026-05-13 [shipped] Moved roadmap details into devlog state: theoretical foundations, design principles, architecture, constraints, version milestones, future debt, and current handoff now live as structured entries

## 📋 Agent Instructions

- Run `devlog orient` at session start for full orientation.
- Use `devlog note "..."` to record milestones (`--type shipped|learning`).
- Use `devlog call "..."` to log architectural decisions.
- Use `devlog snag "..."` to log blockers.
- Use `devlog clear "..."` once a blocker is fixed.
- Use `devlog goal --done` to complete the current goal.
- Use `devlog brief --situation "..."` before ending your session.
- Never edit `.devlog/` files directly — always use the devlog CLI.
