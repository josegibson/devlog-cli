# devlog: The Agent-Aware Project Manager

`devlog` is a CLI tool designed to act as a **shared state engine** between a developer and their AI agents. It bridges the gap between active development sessions and a long-term professional portfolio.

## 🚀 The Core Philosophy
AI agents (Claude, Gemini, etc.) often lack continuity between sessions. `devlog` provides:
1.  **Working Memory**: A local `AGENTS.md` file that agents read to understand the current goal, blockers, decisions, and handoff instructions.
2.  **Permanent Record**: A central repository of structured Markdown files that track your entire career journey.
3.  **Automatic Audit Trail**: Every significant update (milestones, blockers, decisions, logs) is automatically committed to git.

## 🛠 Installation

```bash
# Clone the index repository
cd developer-career-index

# Install globally via pipx (recommended)
pipx install -e .
```

## 📖 Usage

### 1. Orientation
When an agent (or you) enters a project directory, run:
```bash
devlog status
```
This reads the local `AGENTS.md` and provides immediate context on what to do next.

### 2. Linking a Project
To start tracking a new or existing folder:
```bash
devlog link <project-slug>
```
This creates the `AGENTS.md` and maps the current path to your career index.

### 3. During Development
*   **Set a Goal**: `devlog goal "Optimize NPU inference"`
*   **Summarize Standup**: `devlog standup`
*   **Log a Blocker**: `devlog block "ISP driver buffer timeout" --internal`
*   **Log a Breakthrough**: `devlog log "Reached 5.0 FPS on DI1 hardware"`
*   **Log a Decision**: `devlog decide "Use git-backed markdown as storage" --context "offline-friendly audit trail"`
*   **Handoff**: `devlog handoff "Fixed the memory leak, but need to check thermal throttling."`

### 4. Visibility Control
Use the `--internal` flag for raw technical details, error codes, or NDA-sensitive data. These are tagged `[INTERNAL]` in your logs, allowing the portfolio engine to filter them out for public views.

## 🤖 For AI Agents
Agents are instructed via `AGENTS.md` to:
- Proactively read `AGENTS.md` at the start of a session.
- Update goals and blockers as they work.
- Leave a `handoff` message before the session ends.

---
*Built to make developer journeys durable and agent-friendly.*
