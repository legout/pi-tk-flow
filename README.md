# pi-tf-flow

A reusable pi package for tf-driven planning + ticket implementation workflows.

## Includes

- Prompt templates:
  - `/tf-brainstorm`
  - `/tf-plan`
  - `/tf-plan-check`
  - `/tf-plan-refine`
  - `/tf-ticketize`
  - `/tf-implement`
- Bootstrap command extension: `/tk-bootstrap`
- Subagent templates under `assets/agents/`:
  - context-builder, scout, context-merger, researcher, librarian, plan-fast, plan-deep, worker, reviewer, tester, fixer
  - plan-gap-analyzer, plan-reviewer, documenter, refactorer, simplifier, tf-closer, ticketizer
- Reusable chain presets under `assets/chains/`:
  - `tf-brainstorm.chain.md`
  - `tf-plan.chain.md`
  - `tf-plan-thorough.chain.md`
  - `tf-plan-check.chain.md`
  - `tf-plan-refine.chain.md`
  - `tf-ticketize.chain.md`
  - `tf-path-a.chain.md`
  - `tf-path-b.chain.md`
  - `tf-path-c.chain.md`

Implementation presets include a final `tf-closer` step for commit + `tk add-note` + tk close/status gating, plus a compact durable ticket artifact at `.tf/tickets/<ticket-id>/close-summary.md`.

## Install

```bash
# latest main
pi install git:github.com/legout/pi-tf-flow

# or pin a release tag
pi install git:github.com/legout/pi-tf-flow@v0.4.1
```

### pi-subagents prerequisite

`pi-tf-flow` expects the `subagent`/`subagent_status` tools from `pi-subagents`, but does **not** load a bundled copy.
This avoids duplicate tool/command registration conflicts when `pi-subagents` is already installed globally.

Install once (if missing):

```bash
pi install npm:pi-subagents
```

### pi-prompt-template-model extension (optional)

The `pi-prompt-template-model` extension provides automatic model switching for tf commands based on authoritative mappings. When installed, commands automatically use optimized models without manual `--model` flags.

**Install:**

```bash
pi install npm:pi-prompt-template-model
```

**Behavior:**

| Aspect | Behavior |
|--------|----------|
| **Switch** | Commands automatically switch to their mapped model on invocation |
| **Fallback** | If a command has no mapping, it uses the default model (no change) |
| **Restore** | After command completes, the previous model is restored |
| **No extension** | Commands execute normally with whatever model is active |

**Authoritative Command→Model Mapping:**

| Command | Model | Thinking |
|---------|-------|----------|
| `/tk-bootstrap` | `minimax/m2.5` | `low` |
| `/tf-brainstorm` | `glm-5` | `medium` |
| `/tf-implement` | `glm-5` | `medium` |
| `/tf-plan` | `glm-5` | `medium` |
| `/tf-plan-check` | `glm-5` | `medium` |
| `/tf-plan-refine` | `glm-5` | `medium` |
| `/tf-ticketize` | `glm-5` | `medium` |

> **Note:** This mapping table is the **canonical source** for prompt and documentation alignment. When updating model assignments, update this table first.

**Model Precedence (highest to lowest priority):**

1. Subagent tool call `model` parameter (runtime override)
2. Agent definition frontmatter `model`
3. Main loop model (prompt frontmatter via extension)
4. Project defaults (`.pi/settings.json`)
5. Global defaults (`~/.pi/agent/settings.json`)

For full details on model selection behavior and subagent handling, see [`.tf/knowledge/topics/model-configuration.md`](.tf/knowledge/topics/model-configuration.md).

Commands continue to execute normally when the extension is not installed—no error or warning is emitted.

## Bootstrap templates

```bash
# install/update user-level agents + chain presets (~/.pi/agent/agents)
/tk-bootstrap --scope user

# install/update project-level agents + chain presets (.pi/agents)
/tk-bootstrap --scope project

# also materialize prompts + skills to local directories
# user scope: ~/.pi/agent/prompts + ~/.pi/agent/skills
/tk-bootstrap --scope user --copy-all

# project scope: .pi/prompts + .pi/skills
/tk-bootstrap --scope project --copy-all

# preview only
/tk-bootstrap --scope user --copy-all --dry-run

# preserve local edits (never overwrite changed files)
/tk-bootstrap --scope project --copy-all --no-overwrite
```

Flags:
- `--copy-prompts`: copy `prompts/*.md` into scope-local prompts directory
- `--copy-skills`: copy `skills/**` into scope-local skills directory
- `--copy-all` (alias `--materialize`): copy both prompts and skills
- `--no-overwrite`: do not replace existing files when content differs (reported as `Skipped`)
- `--dry-run`: preview create/update/skip counts without writing

Existing file behavior:
- Missing file → `Created`
- Existing identical file → `Unchanged`
- Existing different file → `Updated` by default, or `Skipped` with `--no-overwrite`

## Run

```bash
# 0) Optional brainstorming brief
/tf-brainstorm <topic>
/tf-brainstorm <topic> --mode feature|refactor|simplify
# researcher/librarian are auto-routed by the command when needed (no research flag)

# 1) Planning artifacts (PRD/spec/implementation plan)
/tf-plan <topic>                          # fast mode (default)
/tf-plan <topic> --thorough               # sequential synthesis mode
/tf-plan <topic> --mode feature|refactor|simplify
/tf-plan <topic> --from .tf/plans/<plan-dir>/00-design.md
# plan/brainstorm auto-route researcher/librarian when needed and persist findings to .tf/knowledge/topics/<topic-slug>/

# 2) Optional plan quality gate + refinement
/tf-plan-check .tf/plans/<plan-dir>
/tf-plan-check .tf/plans/<plan-dir>/03-implementation-plan.md --thorough
/tf-plan-refine .tf/plans/<plan-dir>                  # applies refinements when needed (uses existing plan-check findings if present)
/tf-plan-refine .tf/plans/<plan-dir> --thorough

# 3) Ticket decomposition (default creates tickets)
/tf-ticketize .tf/plans/<plan-dir>/03-implementation-plan.md
/tf-ticketize .tf/plans/<plan-dir>/03-implementation-plan.md --dry-run

# 4) Implementation of a ticket (main agent chooses path)
/tf-implement <ticket-id>                           # auto-select Path A/B/C
/tf-implement <ticket-id> --async                   # background execution
/tf-implement <ticket-id> --clarify                 # chain clarification TUI
/tf-implement <ticket-id> --interactive             # supervised overlay (blocking)
/tf-implement <ticket-id> --hands-free              # agent-monitored overlay
/tf-implement <ticket-id> --dispatch                # background + notify
```

Flag behavior:
- `--async`: background mode (`async: true`)
- `--clarify`: open chain clarification TUI (`clarify: true`)
- `--interactive`: live supervised overlay (user controls session)
- `--hands-free`: agent-monitored overlay with periodic updates (~60s)
- `--dispatch`: headless background with notification on completion
- If `--async` and `--clarify` both passed, async wins (legacy behavior)
- `--interactive` is incompatible with `--async` and `--clarify`
- `--hands-free` and `--dispatch` can combine with `--clarify`
- `tf-plan`, `tf-plan-check`, and `tf-plan-refine` support `--fast` (default) and `--thorough`.
- `tf-ticketize` defaults to create mode. Use `--dry-run` to preview without creating tickets.

### `/tf-implement` workflow

`/tf-implement` now uses a leaner ticket lifecycle:

1. **Re-anchor** with `context-builder` only (no scout/merge phase)
2. **Implement** via `worker`
3. **Validate**
   - Path A: targeted review
   - Path B/C: targeted review + relevant ticket-scoped tests
4. **Fix** once via `fixer`
5. **Quick re-check** via `reviewer`
   - narrow go/no-go pass
   - reviews only changed files/hunks touched by implementation/fixes
   - if not a clear pass, the ticket stays `in_progress`
6. **Close or keep open** via `tf-closer`
   - `tk close` only on a clear pass
   - otherwise `tk status <ticket> in_progress`
   - always writes `.tf/tickets/<ticket-id>/close-summary.md`

Review policy:
- Reviews focus on **ticket-scoped implementation changes only**
- Unrelated pre-existing issues are ignored unless they directly block the ticket
- The post-fix step is intentionally a **quick re-check**, not a second full validation cycle

## Execution Modes

`/tf-implement` supports multiple execution modes for different workflows:

| Mode | Flag | Behavior | Use When |
|------|------|----------|----------|
| **Default** | (none) | Agent executes Path A/B/C directly | Routine implementations, batch processing |
| **Async** | `--async` | Background subagent execution | Non-blocking, check status later |
| **Interactive** | `--interactive` | Live supervised TUI overlay | You want to watch and control execution |
| **Hands-Free** | `--hands-free` | Agent-monitored overlay | You want oversight without full attention |
| **Dispatch** | `--dispatch` | Headless + notification | Fire-and-forget long-running tasks |

### Mode Details

**Interactive Mode** (`--interactive`)
- Opens TUI overlay showing real-time subagent output
- You can transfer output (Ctrl+T), background (Ctrl+B), or open detach menu (Ctrl+Q)
- Blocking — returns when session completes or you detach
- Cannot combine with `--clarify` (overlay conflict)

**Hands-Free Mode** (`--hands-free`)
- Opens overlay but agent polls for updates (~60s intervals)
- You can take over anytime by typing in the overlay
- Non-blocking for agent — continues with other work between polls
- Can combine with `--clarify`

**Dispatch Mode** (`--dispatch`)
- Runs headless in background without overlay
- Agent notified automatically when session completes
- Returns `sessionId` immediately for later `/attach`
- Can combine with `--clarify`

### Session Management

Interactive sessions are tracked in `.subagent-runs/<ticket>/session.json`:

```json
{
  "mode": "interactive|hands-free|dispatch",
  "sessionId": "calm-reef",
  "startedAt": "2026-03-04T12:34:56Z",
  "command": "pi \"/tf-implement TICKET-123\"",
  "status": "pending|completed|failed"
}
```

**Commands:**
- `/attach <sessionId>` — Reattach to a background session
- `/sessions` — List all active sessions
- `interactive_shell({ sessionId: "..." })` — Query session status programmatically

### Compatibility Matrix

| Flags | Valid | Notes |
|-------|-------|-------|
| `--interactive` | ✅ | Standalone only; cannot combine with `--hands-free`, `--dispatch`, or `--clarify` |
| `--hands-free` | ✅ | Can add `--clarify` |
| `--dispatch` | ✅ | Can add `--clarify` |
| `--interactive` + `--clarify` | ❌ | Overlay conflict |
| `--interactive` + `--async` | ❌ | Use `--hands-free` or `--dispatch` instead |
| `--hands-free` + `--dispatch` | ❌ | Mutually exclusive |
| Any new flag + `--async` | ❌ | Interactive modes replace `--async` |
| `--hands-free` + `--clarify` | ✅ | Clarify runs first, then hands-free |
| `--dispatch` + `--clarify` | ✅ | Clarify runs first, then dispatch |

## Scope behavior

- If project bootstrap marker `.pi/agents/.tf-bootstrap.json` exists, tk prompts should use `agentScope: "project"`.
- Otherwise they should use `agentScope: "user"`.
- Use `"both"` only when intentionally allowing project agents to override user agents.

## UI (Optional Terminal/Web Interface)

pi-tf-flow includes an optional Textual-based TUI for browsing tickets and knowledge topics.

### Prerequisites

- Python 3.10+
- Optional UI dependencies: `textual>=0.47.0`, `pyyaml>=6.0`

### Installation

```bash
# Install the Python package with UI dependencies
cd python
pip install -e '.[ui]'
# or with uv:
uv pip install -e '.[ui]'
```

### Terminal Mode

Launch the interactive terminal UI:

```bash
# Via pi extension (recommended)
/tf ui

# Direct Python execution
python -m pi_tk_flow_ui

# From project root
python -m pi_tk_flow_ui
```

**Keyboard Shortcuts:**

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh current tab |
| `Tab` | Switch between tabs (Tickets/Topics) |
| `↑/↓` | Navigate lists |
| `Enter` | Select item |
| `o` | Open selected item in pager/editor |
| `e` | Expand/collapse ticket description |
| `1` | Open PRD (01-prd.md) |
| `2` | Open Spec (02-spec.md) |
| `3` | Open Plan (03-implementation-plan.md) |
| `4` | Open Progress (04-progress.md) |
| `?` | Show help |

**Features:**
- **Tickets Tab**: Kanban board with 4 columns (Ready, Blocked, In Progress, Closed)
  - Search filter (title, description)
  - Tag filter
  - Assignee filter
  - Live status refresh from `tk` CLI
  - Ticket detail panel with dependencies
- **Topics Tab**: Knowledge base browser
  - Grouped by type (plan, spike, seed, baseline)
  - Search functionality
  - Topic content preview

### Web Mode

Serve the UI in a web browser (requires `textual` CLI):

```bash
# Get the serve command
/tf ui --web

# Run the printed command (customize host/port as needed)
textual serve "python -m pi_tk_flow_ui" --host 127.0.0.1 --port 8000

# Bind to all interfaces (allows external access)
textual serve "python -m pi_tk_flow_ui" --host 0.0.0.0 --port 8000
```

⚠️ **Security Note**: When binding to `0.0.0.0`, ensure proper firewall rules are in place. The UI has no authentication.

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `Error: UI dependencies not installed` | Run `pip install -e './python[ui]'` |
| `tk CLI not found` | Status defaults to "open"; install `tk` for live status |
| `No tickets found` | Create a plan with `/tf-plan` first |
| `No topics found` | Add markdown files to `.tf/knowledge/topics/` |
| Editor doesn't open | Set `$EDITOR` or `$PAGER` environment variable |
| Colors look wrong | Ensure your terminal supports 256 colors |

### Environment Variables

- `TF_KNOWLEDGE_DIR`: Override knowledge directory path
- `EDITOR`: Preferred editor for opening files
- `PAGER`: Preferred pager for viewing files

## Workflow artifacts

- `.tf/plans/<date>-<topic>/00-brainstorm.md`
- `.tf/plans/<date>-<topic>/00-design.md`
- `.tf/plans/<date>-<topic>/01-prd.md`
- `.tf/plans/<date>-<topic>/02-spec.md`
- `.tf/plans/<date>-<topic>/03-implementation-plan.md`
- `.tf/plans/<date>-<topic>/04-ticket-breakdown.md`
- `.tf/plans/<date>-<topic>/05-plan-gaps.md` (optional quality gate)
- `.tf/plans/<date>-<topic>/06-plan-review.md` (optional quality gate)
- `.tf/plans/<date>-<topic>/07-refinement-summary.md` (optional refine step)
- `.tf/plans/<date>-<topic>/tickets.yaml`
- `.subagent-runs/*` chain artifacts
- `.tf/knowledge/*` persistent research cache
- `.tf/progress.md` progress entries
- `.tf/AGENTS.md` lessons learned (new + useful only)
