# Agent Context

> Auto-managed by `devlog`. Run `devlog orient` for full orientation.

## L1 Perception — Current State

### Current Goal

No active goal set.

### Last Brief

**Situation:** Post-1.0 roadmap clarified
**Background:** v1.0.0 now means stable core CLI, while previously recorded v0.7/v0.8/v0.9 ideas were really expansion features

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
- 2026-05-13 [shipped] tension map implemented: derive_call_confidence produces confirmed/at-risk/degraded/nominal states from snag.threatens, milestone.calls, and shift.assumption_broke keyword overlap
- 2026-05-13 [shipped] Completed v1.0.0 implementation closure: added tension command, extended relationship validation, enforced brief quality warning, extracted edit target resolution, reconciled docs, and repaired devlog state validation
- 2026-05-13 [learning] Reframed roadmap: v1.0.0 is stable core CLI; inspect/query, optional AI, GUI, migration, and publishing are post-1.0 versions

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

- **2026-05-13** Keep the Python package at the repository root as devlog — the package is small and the user explicitly preferred not adding a src/devlog nesting layer `[degraded ↘]`
  - *Tradeoff:* tests need configuration discipline so imports do not mask packaging issues
  - *Ruled out:* src/devlog layout, package rename to src
  - ⚡ Assumption broke: "one career index should own project state" → shifted to local-first .devlog YAML inside each project repository
- **2026-05-13** Keep LLM support optional with deterministic offline core — devlog core operations are writing records, reading YAML, and projecting AGENTS.md from local state `[degraded ↘]`
  - *Tradeoff:* fallback keyword matching will be less accurate than provider-backed semantic matching
  - *Ruled out:* LLM-required architecture, cloud-only reasoning, embedding database dependency
  - ⚡ Assumption broke: "one career index should own project state" → shifted to local-first .devlog YAML inside each project repository
- **2026-05-13** Use provider-configured AI only for tension overlap and natural-language ask — .devlog/config.yaml can specify ai_provider as anthropic, openai, or ollama
  - *Tradeoff:* provider integrations need adapters and test doubles without weakening deterministic core behavior
  - *Ruled out:* AI on every command, no AI support, hard-coded provider
- **2026-05-13** Use D3.js force-directed graph for devlog gui — the graph view is a read layer over .devlog/tension.yaml
  - *Tradeoff:* devlog gui requires a local web server and frontend asset pipeline that the core CLI otherwise avoids
  - *Ruled out:* custom canvas graph, static Mermaid export, GUI as primary interface
- **2026-05-13** Treat v1.0.0 as the stable core CLI baseline — the CLI command surface, local-first storage, AGENTS.md projection, events.jsonl, tension map, validation, docs, and tests are implemented `[degraded ↘]`
  - *Tradeoff:* some previously recorded milestone labels need to be superseded or reinterpreted as post-1.0 work
  - *Ruled out:* keeping v0.7/v0.8/v0.9 as pre-1.0 milestones, renaming the package back below 1.0
  - ⚡ Assumption broke: "aliases are needed before first public use" → shifted to breaking v0.3 final command names only

### Active Assumptions

- Betting that **simple repository structure while retaining the import package name devlog** (via: Keep the Python package at the repository root as devlog)
- Assumes **production packaging benefits from src layout but project simplicity matters now** is the real problem (via: Keep the Python package at the repository root as devlog)
- Betting that **offline reliability with optional smarter analysis when a provider is configured** (via: Keep LLM support optional with deterministic offline core)
- Assumes **LLM providers add value for semantic overlap detection and natural-language historical queries, but must not be required for normal operation** is the real problem (via: Keep LLM support optional with deterministic offline core)
- Betting that **narrow AI surface area with local fallback and provider portability** (via: Use provider-configured AI only for tension overlap and natural-language ask)
- Assumes **semantic shift/snag overlap and 'why did we choose X?' queries benefit from language understanding** is the real problem (via: Use provider-configured AI only for tension overlap and natural-language ask)
- Betting that **interactive local graph inspection while keeping CLI as the primary interface** (via: Use D3.js force-directed graph for devlog gui)
- Assumes **humans need a visual map of calls, snags, shifts, confidence states, and threatens/degrades edges** is the real problem (via: Use D3.js force-directed graph for devlog gui)
- Betting that **clear release semantics: v1.0 is stable core; later versions extend the product** (via: Treat v1.0.0 as the stable core CLI baseline)
- Assumes **future inspect, AI, GUI, migration, and publishing work should not make v1.0.0 sound incomplete** is the real problem (via: Treat v1.0.0 as the stable core CLI baseline)

### Brief Assessment

Future work is now versioned as v1.1 inspect/query, v1.2 optional AI, v1.3 GUI, v1.4 migration/import, and v1.5 public packaging

### Known Debt

- [prudent-deliberate] migration helper for old projects is not implemented
  - Fix by: v0.5.0
- [prudent-deliberate] stable release packaging is pending
  - Fix by: v1.0.0

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

**Recommendation:** Build v1.1.0 inspect/query next if continuing feature work

### Milestone Timeline

- **2026-05-13** v1.1.0: Add inspect plus show/list/graph style read commands and plain-language tension summaries for humans reviewing agent state parent `milestone-2026-05-13-v1-0-0-final`
- **2026-05-13** v1.2.0: Add ai_provider config for anthropic, openai, or ollama; use AI only for tension overlap and natural-language ask, with deterministic keyword fallback parent `milestone-2026-05-13-v1-1-0`
- **2026-05-13** v1.3.0: Add devlog gui command that starts a local web server and renders .devlog/tension.yaml as a D3 force-directed graph parent `milestone-2026-05-13-v1-2-0`
- **2026-05-13** v1.4.0: Add migration helper for old devlog projects and import paths from legacy project notes into local .devlog YAML parent `milestone-2026-05-13-v1-3-0`
- **2026-05-13** v1.5.0: Finish release packaging, publishing workflow, and public distribution metadata after the stable core API parent `milestone-2026-05-13-v1-4-0`

## 📋 Agent Instructions

- Run `devlog orient` at session start for full orientation.
- Use `devlog note "..."` to record milestones (`--type shipped|learning`).
- Use `devlog call "..."` to log architectural decisions.
- Use `devlog snag "..."` to log blockers.
- Use `devlog clear "..."` once a blocker is fixed.
- Use `devlog goal --done` to complete the current goal.
- Use `devlog brief --situation "..."` before ending your session.
- Never edit `.devlog/` files directly — always use the devlog CLI.
