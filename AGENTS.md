# Agent Context

> Auto-managed by `devlog`. Run `devlog orient` for full orientation.

## L1 Perception — Current State

### Current Goal

No active goal set.

### Last Brief

**Situation:** v0.4 intelligence design implemented

### Recent Activity

- 2026-05-13 [shipped] Added pytest coverage for v0.2.0 CLI behavior: init, goals, logs, decisions, blockers, handoff, standup, validate, export, and git commits
- 2026-05-13 [shipped] Expanded v0.2.0 test suite to 23 tests with coverage reporting, 95.28% total coverage, CI workflow, and obsolete Markdown parser removal
- 2026-05-13 [shipped] Switched CLI and tests to v0.3.0 final command paradigm with note/call/calls/snag/clear/brief/log/orient plus shift, arch, constraint, and debt
- 2026-05-13 [shipped] v0.2.0 foundation shipped: local .devlog YAML storage, generated AGENTS.md and .devlog/index.json, all Pydantic models, init-based setup, and central repo dependencies removed
- 2026-05-13 [shipped] v0.3.0 schema work implemented in code: final command names, richer call/snag/brief/goal fields, and new shift/arch/constraint/debt commands
- 2026-05-13 [shipped] Moved roadmap details into devlog state: theoretical foundations, design principles, architecture, constraints, version milestones, future debt, and current handoff now live as structured entries
- 2026-05-13 [shipped] Drafted COMMAND_PARADIGM.md to explain the devlog command model, schema theory, progressive disclosure tiers, storage/projection design, relationships, and abstraction questions
- 2026-05-13 [shipped] Implemented v0.4 intelligence projection labels across AGENTS.md, standup, and orient with explicit L1 perception, L2 comprehension, and L3 projection sections
- 2026-05-13 [shipped] v0.5.0 shipped: no auto-commits, events.jsonl temporal record, uncommitted-state warning in status

## L2 Comprehension — Meaning and Risk

### Active Constraints

- [constraint-2026-05-13-devlog-must-remain-local-first-with] devlog must remain local-first with no database or required network service
  - *Impact:* all state must be represented as files under .devlog/ plus generated local artifacts
- [constraint-2026-05-13-generated-portfolio-tool-export-mus] generated portfolio/tool export must stay inside .devlog/index.json
  - *Impact:* root DEVLOG.json is obsolete; external consumers should fetch .devlog/index.json
- [constraint-2026-05-13-test-coverage-gate-must-run-through] test coverage gate must run through pytest-cov with at least 80 percent total coverage
  - *Impact:* new features need tests or the default pytest command fails
- [constraint-2026-05-13-llm-features-must-gracefully-degrad] LLM features must gracefully degrade to keyword matching when no provider is configured
  - *Impact:* tension overlap detection and ask queries cannot require network credentials or hosted AI availability

### Key Decisions & Tension

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

### Brief Assessment

L1/L2/L3 separation, constraint surfacing, assumption tracking, and debt paying are now in the CLI

### Known Debt

- [prudent-deliberate] edit command is intentionally thinly tested because it execs into an editor
  - Fix by: before packaging v1.0
- [prudent-deliberate] README and ROADMAP need a final pass after deciding milestone and timeline scope
  - Fix by: before tagging v0.3.0
- [prudent-deliberate] migration helper for old projects is not implemented
  - Fix by: v0.5.0
- [prudent-deliberate] stable release packaging is pending
  - Fix by: v1.0.0
- [prudent-deliberate] call.over (rejected alternatives) not rendered in AGENTS.md — new agents re-propose ruled-out approaches
  - Fix by: v0.5.0
- [prudent-deliberate] active assumptions not surfaced in L2 — only broken assumptions (shifts) shown in L3
  - Fix by: v0.5.0
- [prudent-inadvertent] brief discipline not enforced — agents leave one-sentence situation with no background/assessment/recommendation
  - Fix by: v0.5.0

## L3 Projection — Path Forward

### Active Assumptions (Recently Broken)

- Broken: "one career index should own project state"
  - *Shifted to:* local-first .devlog YAML inside each project repository
- Broken: "portfolio export must live at the repository root"
  - *Shifted to:* .devlog/index.json export
- Broken: "aliases are needed before first public use"
  - *Shifted to:* breaking v0.3 final command names only

### Goal Horizon

No active projection.

### Recommended Next Move

**Recommendation:** tag v0.4.0 and move to v0.5.0-tension

### Milestone Timeline

- **2026-05-13** v0.6.0-compression: Compress tier-1 scratch observations into briefs, archive processed scratch windows, and keep AGENTS.md concise with only recent observations parent `milestone-2026-05-13-v0-5-0-tension`
- **2026-05-13** v0.7.0-inspect: Add inspect, show/list/graph style query commands, and plain-language tension summaries for humans reviewing agent state parent `milestone-2026-05-13-v0-6-0-compression`
- **2026-05-13** v0.8.0-ai-optional: Add ai_provider config for anthropic, openai, or ollama; use AI only for tension overlap detection and devlog ask natural-language decision queries, with keyword fallback when unconfigured parent `milestone-2026-05-13-v0-7-0-inspect`
- **2026-05-13** v0.9.0-gui: Add devlog gui command that starts a local web server and renders .devlog/tension.yaml as a D3 force-directed graph of calls, snags, shifts, confidence states, and threatens/degrades edges parent `milestone-2026-05-13-v0-8-0-ai-optional`
- **2026-05-13** v0.5.0: Removed git auto-commits; added events.jsonl as internal temporal record; devlog no longer touches project git history parent `milestone-2026-05-13-v0-4-0-agent-memory`

## 📋 Agent Instructions

- Run `devlog orient` at session start for full orientation.
- Use `devlog note "..."` to record milestones (`--type shipped|learning`).
- Use `devlog call "..."` to log architectural decisions.
- Use `devlog snag "..."` to log blockers.
- Use `devlog clear "..."` once a blocker is fixed.
- Use `devlog goal --done` to complete the current goal.
- Use `devlog brief --situation "..."` before ending your session.
- Never edit `.devlog/` files directly — always use the devlog CLI.
