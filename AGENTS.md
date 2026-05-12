# Agent Context

> Auto-managed by `devlog`. Run `devlog orient` for full orientation.

## 🎯 Current Goal

start v0.4.0 intelligence design

**Done looks like:** AGENTS.md, standup, and orient explicitly separate L1 perception, L2 comprehension, and L3 projection
**Target:** next development phase
**Risk:** current generator still mixes perception, assessment, and projection in legacy sections
**Next decision:** exact L1/L2/L3 layout and how milestone timeline should appear in AGENTS.md

## 🤝 Last Brief

**Situation:** Milestone/timeline implementation is complete and most roadmap information has been migrated into structured devlog entries
**Background:** ROADMAP.md had grown into a second state store covering foundations, schemas, milestones, future releases, constraints, and design principles
**Assessment:** The canonical project state is now .devlog YAML plus .devlog/index.json; ROADMAP.md should remain a compact orientation document rather than duplicate entry details
**Recommendation:** Use devlog status, timeline, calls, and log for current state; keep ROADMAP.md short and update devlog first for future decisions

## ⚠️ Active Blockers

No active blockers.

## 🧠 Key Decisions

- **2026-05-13** Use final v0.3 command names without deprecated aliases — the tool has no external users yet and compatibility does not matter more than vocabulary clarity
  - *Tradeoff:* local scripts using v0.2 command names will break
- **2026-05-13** Keep the Python package at the repository root as devlog — the package is small and the user explicitly preferred not adding a src/devlog nesting layer
  - *Tradeoff:* tests need configuration discipline so imports do not mask packaging issues
- **2026-05-13** Keep LLM support optional with deterministic offline core — devlog core operations are writing records, reading YAML, and projecting AGENTS.md from local state
  - *Tradeoff:* fallback keyword matching will be less accurate than provider-backed semantic matching
- **2026-05-13** Use provider-configured AI only for tension overlap and natural-language ask — .devlog/config.yaml can specify ai_provider as anthropic, openai, or ollama
  - *Tradeoff:* provider integrations need adapters and test doubles without weakening deterministic core behavior
- **2026-05-13** Use D3.js force-directed graph for devlog gui — the graph view is a read layer over .devlog/tension.yaml
  - *Tradeoff:* devlog gui requires a local web server and frontend asset pipeline that the core CLI otherwise avoids

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

- v0.4.0-agent-memory: Introduce human intent, agent observe scratch memory, config.yaml thresholds, and AGENTS.md as deterministic projection owned by the CLI
- v0.5.0-tension: Derive .devlog/tension.yaml from calls, snags, shifts, and milestones; track call confidence as nominal, degraded, at-risk, unconfirmed, or confirmed-at-milestone
- v0.6.0-compression: Compress tier-1 scratch observations into briefs, archive processed scratch windows, and keep AGENTS.md concise with only recent observations
- v0.7.0-inspect: Add inspect, show/list/graph style query commands, and plain-language tension summaries for humans reviewing agent state
- v0.8.0-ai-optional: Add ai_provider config for anthropic, openai, or ollama; use AI only for tension overlap detection and devlog ask natural-language decision queries, with keyword fallback when unconfigured

## 📜 Recent Activity

- 2026-05-13 [shipped] Added pytest coverage for v0.2.0 CLI behavior: init, goals, logs, decisions, blockers, handoff, standup, validate, export, and git commits
- 2026-05-13 [shipped] Expanded v0.2.0 test suite to 23 tests with coverage reporting, 95.28% total coverage, CI workflow, and obsolete Markdown parser removal
- 2026-05-13 [shipped] Switched CLI and tests to v0.3.0 final command paradigm with note/call/calls/snag/clear/brief/log/orient plus shift, arch, constraint, and debt
- 2026-05-13 [shipped] v0.2.0 foundation shipped: local .devlog YAML storage, generated AGENTS.md and .devlog/index.json, all Pydantic models, init-based setup, and central repo dependencies removed
- 2026-05-13 [shipped] v0.3.0 schema work implemented in code: final command names, richer call/snag/brief/goal fields, and new shift/arch/constraint/debt commands
- 2026-05-13 [shipped] Moved roadmap details into devlog state: theoretical foundations, design principles, architecture, constraints, version milestones, future debt, and current handoff now live as structured entries
- 2026-05-13 [shipped] Drafted COMMAND_PARADIGM.md to explain the devlog command model, schema theory, progressive disclosure tiers, storage/projection design, relationships, and abstraction questions

## 📋 Agent Instructions

- Run `devlog orient` at session start for full orientation.
- Use `devlog note "..."` to record milestones (`--type shipped|learning`).
- Use `devlog call "..."` to log architectural decisions.
- Use `devlog snag "..."` to log blockers.
- Use `devlog clear "..."` once a blocker is fixed.
- Use `devlog goal --done` to complete the current goal.
- Use `devlog brief --situation "..."` before ending your session.
- Never edit `.devlog/` files directly — always use the devlog CLI.
