# pi-tf-flow

A reusable pi package for tf-driven planning + ticket implementation workflows.

## Includes

- Prompt templates:
  - `/tf-init`
  - `/tf-brainstorm`
  - `/tf-plan`
  - `/tf-plan-check`
  - `/tf-plan-refine`
  - `/tf-ticketize`
  - `/tf-implement`
  - `/tf-refactor`
  - `/tf-simplify`
- Bootstrap command extension: `/tf-bootstrap`
- Subagent templates under `assets/agents/`:
  - default workflow agents: context-builder, scout, context-merger, researcher, librarian, plan-fast, plan-deep, worker, reviewer, tester, fixer
  - default workflow support agents: plan-gap-analyzer, plan-reviewer, documenter, tf-closer, ticketizer
  - auxiliary agents: refactorer, simplifier
- Reusable chain presets under `assets/chains/`:
  - `tf-brainstorm.chain.md`
  - `tf-plan.chain.md`
  - `tf-plan-thorough.chain.md`
  - `tf-plan-check.chain.md`
  - `tf-plan-refine.chain.md`
  - `tf-ticketize.chain.md`
  - `tf-refactor.chain.md`
  - `tf-simplify.chain.md`
  - `tf-path-a.chain.md`
  - `tf-path-b.chain.md`
  - `tf-path-c.chain.md`

Prompt templates are the authoritative top-level workflow surface.
Chain presets are reusable static building blocks that mirror the intended flow shape, but prompt commands may add dynamic routing, optional research decisions, preflight logic, or parallel execution around them.

Not every shipped agent is used by the default `/tf-*` prompts. Some are auxiliary building blocks that can support specialized workflows outside the default planning and implementation paths.

`tf-path-a`, `tf-path-b`, and `tf-path-c` are post-anchor execution presets: they assume `anchor-context.md` already exists for the current run.
`tf-refactor` and `tf-simplify` chain presets are static representative workflows; the top-level prompt commands add dynamic ticket-vs-goal finalization and runtime flag handling.

Implementation presets include a final `tf-closer` step for commit + `tk add-note` + tk close/status gating, plus a compact durable ticket artifact under `.tf/tickets/<ticket-id>/close-summary.md`.

## Install

```bash
# latest main
pi install git:github.com/legout/pi-tf-flow

# or pin a release tag
pi install git:github.com/legout/pi-tf-flow@v0.7.0
```

## Repository context

This repository is both:
1. the source code for the `pi-tk-flow` package, and
2. a live user of `pi-tk-flow` for its own development.

Package source-of-truth files live at the repo root and in shipped folders such as `prompts/`, `assets/`, `extensions/`, and `python/`. Root markdown docs are also mirrored under `docs/` for easier browsing.
Self-hosting workflow artifacts live under `.tf/`, `.tickets/`, and `.subagent-runs/`.

For the package/project distinction, see [`PROJECT.md`](docs/PROJECT.md).
For recommended `PROJECT.md` / `AGENTS.md` / `.tf/knowledge` conventions in downstream repos, see [`CONTEXT-GUIDE.md`](docs/CONTEXT-GUIDE.md).
For the project-aware refactor/simplify workflow design, see [`REFACTOR-SIMPLIFY-SPEC.md`](docs/REFACTOR-SIMPLIFY-SPEC.md).
For the full framework assessment and remediation roadmap, see [`FRAMEWORK-ASSESSMENT-AND-ROADMAP.md`](docs/FRAMEWORK-ASSESSMENT-AND-ROADMAP.md).

For best results in projects using `pi-tk-flow`, create both:
- `PROJECT.md` for durable project/product/system context
- `AGENTS.md` for repo-specific agent operating guidance

You can create these manually, or use `/tf-init` to generate them together with `.tf/knowledge/baselines/...` starter files.

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
| `/tf-bootstrap` | `minimax/m2.5` | `low` |
| `/tf-init` | `glm-5` | `medium` |
| `/tf-brainstorm` | `glm-5` | `medium` |
| `/tf-implement` | `glm-5` | `medium` |
| `/tf-plan` | `glm-5` | `medium` |
| `/tf-plan-check` | `glm-5` | `medium` |
| `/tf-plan-refine` | `glm-5` | `medium` |
| `/tf-ticketize` | `glm-5` | `medium` |
| `/tf-refactor` | `glm-5` | `medium` |
| `/tf-simplify` | `glm-5` | `medium` |

> **Note:** This mapping table is the **canonical source** for prompt and documentation alignment. When updating model assignments, update this table first.

**Model Precedence (highest to lowest priority):**

1. Subagent tool call `model` parameter (runtime override)
2. Agent definition frontmatter `model`
3. Main loop model (prompt frontmatter via extension)
4. Project defaults (`.pi/settings.json`)
5. Global defaults (`~/.pi/agent/settings.json`)

For full details on model selection behavior and subagent handling, see [`MODEL-CONFIGURATION.md`](docs/MODEL-CONFIGURATION.md).

Commands continue to execute normally when the extension is not installed—no error or warning is emitted.

## Bootstrap templates

> **Migration note:** the bootstrap pi command is `/tf-bootstrap`. Any older `/tk-bootstrap` references are legacy and should be updated.


```bash
# install/update user-level agents + chain presets (~/.pi/agent/agents)
/tf-bootstrap --scope user

# install/update project-level agents + chain presets (.pi/agents)
/tf-bootstrap --scope project

# also materialize prompts (and any bundled skills) to local directories
# user scope: ~/.pi/agent/prompts + ~/.pi/agent/skills
/tf-bootstrap --scope user --copy-all

# project scope: .pi/prompts + .pi/skills
/tf-bootstrap --scope project --copy-all

# preview only
/tf-bootstrap --scope user --copy-all --dry-run

# preserve local edits (never overwrite changed files)
/tf-bootstrap --scope project --copy-all --no-overwrite
```

Flags:
- `--copy-prompts`: copy `prompts/*.md` into scope-local prompts directory
- `--copy-skills`: copy `skills/**` into scope-local skills directory when the package ships bundled skills
- `--copy-all` (alias `--materialize`): copy prompts and any bundled skills
- `--no-overwrite`: do not replace existing files when content differs (reported as `Skipped`)
- `--dry-run`: preview create/update/skip counts without writing

Existing file behavior:
- Missing file → `Created`
- Existing identical file → `Unchanged`
- Existing different file → `Updated` by default, or `Skipped` with `--no-overwrite`

Current package note:
- `pi-tk-flow` currently ships prompts, agents, chains, and extensions.
- If `--copy-skills` is requested in a release with no bundled skills, `/tf-bootstrap` reports that no bundled skills are shipped and continues safely.

## Project initialization

```bash
# analyze an existing repo and draft pi-tk-flow context files
/tf-init --brownfield

# initialize a new repo from a short brief or follow-up interview
/tf-init --greenfield "internal analytics platform for support teams"

# let the command auto-detect greenfield vs brownfield
/tf-init

# preview without writing
/tf-init --brownfield --dry-run

# create only missing files
/tf-init --brownfield --no-overwrite
```

`/tf-init` creates or updates:
- `PROJECT.md`
- `AGENTS.md` (with a standard pi-tk-flow managed block plus project-specific guidance)
- `.tf/AGENTS.md`
- `.tf/knowledge/README.md`
- `.tf/knowledge/baselines/coding-standards.md`
- `.tf/knowledge/baselines/testing.md`
- `.tf/knowledge/baselines/architecture.md`
- `.tf/plans/`, `.tf/knowledge/topics/`, `.tf/knowledge/tickets/`, and `.tickets/`

The command keeps baseline knowledge in dedicated `.tf/knowledge/baselines/...` files and links them from `PROJECT.md`.
In brownfield mode it synthesizes drafts from existing repo evidence.
In greenfield mode it uses the provided brief and asks a compact setup interview when necessary.

## Run

```bash
# 0) Initialize project context (recommended before planning)
/tf-init --brownfield

# 1) Optional brainstorming brief
/tf-brainstorm <topic>
/tf-brainstorm <topic> --mode feature|refactor|simplify
# researcher/librarian are auto-routed by the command when needed (no research flag)

# 1) Planning artifacts (PRD/spec/implementation plan)
/tf-plan <topic>                          # fast mode (default)
/tf-plan <topic> --thorough               # sequential synthesis mode
/tf-plan <topic> --mode feature|refactor|simplify
/tf-plan <topic> --from .tf/plans/<plan-dir>/00-design.md
# plan/brainstorm auto-route researcher/librarian when needed and persist findings under .tf/knowledge/topics/<topic-slug>/

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

# 5) Project-aware structural improvement workflows
/tf-refactor <goal-or-ticket-id>                    # behavior-preserving structural refactor
/tf-refactor <goal-or-ticket-id> --scope src/auth --thorough
/tf-simplify <goal-or-ticket-id>                    # behavior-preserving simplification
/tf-simplify <goal-or-ticket-id> --hotspots-only --fast
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
- `tf-refactor` and `tf-simplify` support ticket mode or freeform goal mode, and are project-aware via `PROJECT.md`, `AGENTS.md`, and `.tf/knowledge/...` when present.

### `/tf-refactor` and `/tf-simplify`

These commands are project-aware structural improvement workflows.

`/tf-refactor` is for behavior-preserving structural reorganization:
- improve module boundaries
- reduce duplication
- clarify naming and structure
- prepare code for future work

`/tf-simplify` is for behavior-preserving complexity reduction:
- reduce nesting and branching
- simplify control flow
- split long functions
- make code easier to understand and maintain

Shared behavior:
- supports **ticket mode** when the target resolves to `.tickets/<id>.md`
- supports **goal mode** for freeform project work
- reads `PROJECT.md`, `AGENTS.md`, and relevant `.tf/knowledge/...` when present
- uses scoped planning + specialist execution + review/test validation
- uses `tf-closer` only in ticket mode; goal mode writes a summary without mutating `tk`

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

## UI (Standalone CLI)

pi-tf-flow includes an optional standalone Textual TUI for browsing tickets and plans.
It is **not** exposed as a pi command anymore.

### Prerequisites

- Python 3.10+
- UI dependencies: `textual>=0.47.0`, `pyyaml>=6.0`
- `uv` recommended

### Install globally with `uv tool install`

From a published package or git source, install the standalone CLI:

```bash
uv tool install --from 'git+https://github.com/legout/pi-tk-flow[ui]' tf-ui
```

Then run:

```bash
tf-ui
```

### Install from a local checkout with `uv tool install`

From the repository root:

```bash
uv tool install --from '.[ui]' tf-ui
```

Then run:

```bash
tf-ui
```

### Run without installing via `uvx`

From the repository root:

```bash
uvx --from '.[ui]' tf-ui
```

From git directly:

```bash
uvx --from 'git+https://github.com/legout/pi-tk-flow[ui]' tf-ui
```

### Alternative local dev install

```bash
pip install -e '.[ui]'
tf-ui
```

### Web Mode

Print the browser serve command:

```bash
tf-ui --web
```

Example serve command:

```bash
textual serve "tf-ui" --host 127.0.0.1 --port 8000
```

⚠️ **Security Note**: When binding to `0.0.0.0`, ensure proper firewall rules are in place. The UI has no authentication.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh current tab |
| `Tab` | Move focus / switch tabs |
| `↑/↓` | Navigate lists |
| `Enter` | Select item |
| `o` | Open selected item in pager/editor |
| `e` | Expand/collapse ticket description |
| `1` | Open PRD (01-prd.md) |
| `2` | Open Spec (02-spec.md) |
| `3` | Open Plan (03-implementation-plan.md) |
| `4` | Open Ticket Breakdown (04-ticket-breakdown.md) |
| `?` | Show help |

### Features
- **Tickets Tab**: Kanban board with 4 columns (Ready, Blocked, In Progress, Closed)
  - Search filter (title, description)
  - Tag filter
  - Assignee filter
  - Ticket detail panel with dependencies
- **Plans Tab**: Plan browser for `.tf/plans/*`
  - Search by title, topic, plan ID, or date
  - Document availability summary
  - Quick-open PRD/spec/implementation plan/ticket breakdown
  - Legacy compatibility for older `03-plan.md` / `04-progress.md` plan layouts

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `Error: UI dependencies not installed` | Run `uv tool install --from '.[ui]' tf-ui` or `uvx --from '.[ui]' tf-ui` |
| `No tickets found` | Create tickets under `.tickets/` |
| `No plans found` | Create a plan with `/tf-plan` first |
| Editor doesn't open | Set `$EDITOR` or `$PAGER` environment variable |
| Colors look wrong | Ensure your terminal supports 256 colors |

### Environment Variables

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
- `.tf/knowledge/` persistent research cache
  - recommended topic layout: `.tf/knowledge/topics/<topic-slug>/summary.md`, `research.md`, `library-research.md`
  - common optional topic artifacts: `anchor-context.md`, `plan-gaps.md`, `plan-review.md`, `implementation-plan.md`, `refinement-summary.md`
  - recommended ticket layout: `.tf/knowledge/tickets/<ticket-id>/research.md`
- `.tf/tickets/<ticket-id>/close-summary.md` durable ticket close artifact
- `.tf/progress.md` progress entries
- `.tf/AGENTS.md` lessons learned (new + useful only)
