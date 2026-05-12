# devlog: The Agent-Aware Project Manager

`devlog` is a CLI tool designed to act as a **shared state engine** between a developer and their AI agents. It bridges the gap between active development sessions and a long-term professional portfolio.

## The Core Philosophy
AI agents (Claude, Gemini, etc.) often lack continuity between sessions. `devlog` provides:
1.  **Working Memory**: A local `AGENTS.md` file that agents read to understand the current goal, blockers, decisions, and handoff instructions.
2.  **Project State**: Local YAML files under `.devlog/`, plus a generated `.devlog/index.json` for tools and portfolio consumers.
3.  **Automatic Audit Trail**: Every significant update is automatically committed to git when the project is inside a git repo.

## Installation

```bash
# Install globally via pipx (recommended)
pipx install -e .
```

For local development:

```bash
uv run devlog --help
uv run pytest
```

## Usage

### 1. Orientation
When an agent (or you) enters a project directory, run:
```bash
devlog status
```
This reads the local `AGENTS.md` and provides immediate context on what to do next.

### 2. Initialising a Project
To start tracking a new or existing folder:
```bash
devlog init
```
This creates `.devlog/`, `AGENTS.md`, and `.devlog/index.json`.

### 3. During Development
*   **Set a Goal**: `devlog goal "Optimize NPU inference"`
*   **Summarize Standup**: `devlog standup`
*   **Log a Blocker**: `devlog snag "ISP driver buffer timeout" --internal`
*   **Log a Breakthrough**: `devlog note "Reached 5.0 FPS on DI1 hardware"`
*   **Log a Decision**: `devlog call "Use git-backed YAML as storage" --context "offline-friendly audit trail"`
*   **Handoff**: `devlog brief --situation "Fixed the memory leak, but need to check thermal throttling."`
*   **View Activity**: `devlog log`
*   **Validate State**: `devlog validate`
*   **Export JSON**: `devlog export`

### 4. Visibility Control
Use the `--internal` flag for raw technical details, error codes, or NDA-sensitive data. Internal notes and blockers are filtered out of the generated public export.

## For AI Agents
Agents are instructed via `AGENTS.md` to:
- Proactively read `AGENTS.md` at the start of a session.
- Update goals and blockers as they work.
- Leave a `brief` before the session ends.

---
*Built to make developer journeys durable and agent-friendly.*
