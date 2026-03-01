# pi-tk-flow

A reusable pi package for tk-driven planning + ticket implementation workflows.

## Includes

- Prompt templates:
  - `/tk-brainstorm`
  - `/tk-plan`
  - `/tk-ticketize`
  - `/tk-implement`
- Bootstrap command extension: `/tk-bootstrap`
- Subagent templates under `assets/agents/`:
  - context-builder, scout, researcher, librarian, planner, worker, reviewer, tester, fixer
  - documenter, refactorer, simplifier, tk-closer, ticketizer
- Reusable chain presets under `assets/chains/`:
  - `tk-brainstorm.chain.md`
  - `tk-plan.chain.md`
  - `tk-plan-thorough.chain.md`
  - `tk-ticketize.chain.md`
  - `tk-path-a.chain.md`
  - `tk-path-b.chain.md`
  - `tk-path-c.chain.md`

Implementation presets include a final `tk-closer` step for commit + `tk add-note` + tk close/status gating.
- Skill: `tk-workflow`

## Install

```bash
# latest main
pi install git:github.com/legout/pi-tk-flow

# or pin a release tag
pi install git:github.com/legout/pi-tk-flow@v0.1.5
```

### pi-subagents prerequisite

`pi-tk-flow` expects the `subagent`/`subagent_status` tools from `pi-subagents`, but does **not** load a bundled copy.
This avoids duplicate tool/command registration conflicts when `pi-subagents` is already installed globally.

Install once (if missing):

```bash
pi install npm:pi-subagents
```

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
/tk-brainstorm <topic>
/tk-brainstorm <topic> --mode feature|refactor|simplify --research

# 1) Planning artifacts (PRD/spec/implementation plan)
/tk-plan <topic>                          # fast mode (default)
/tk-plan <topic> --thorough               # sequential synthesis mode
/tk-plan <topic> --mode feature|refactor|simplify
/tk-plan <topic> --from .tf/plans/<plan-dir>/00-design.md

# 2) Ticket decomposition (default creates tickets)
/tk-ticketize .tf/plans/<plan-dir>/03-implementation-plan.md
/tk-ticketize .tf/plans/<plan-dir>/03-implementation-plan.md --dry-run

# 3) Implementation of a ticket (main agent chooses path)
/tk-implement <ticket-id>
/tk-implement <ticket-id> --async
/tk-implement <ticket-id> --clarify
```

Flag behavior:
- `--async`: background mode (`async: true`)
- `--clarify`: open chain clarify TUI (`clarify: true`)
- If both are passed, async wins and clarify is disabled for deterministic background execution.
- `tk-plan` supports `--fast` (default) and `--thorough`.
- `tk-ticketize` defaults to create mode. Use `--dry-run` to preview without creating tickets.

## Scope behavior

- If project bootstrap marker `.pi/agents/.tk-bootstrap.json` exists, tk prompts should use `agentScope: "project"`.
- Otherwise they should use `agentScope: "user"`.
- Use `"both"` only when intentionally allowing project agents to override user agents.

## Workflow artifacts

- `.tf/plans/<date>-<topic>/00-brainstorm.md`
- `.tf/plans/<date>-<topic>/00-design.md`
- `.tf/plans/<date>-<topic>/01-prd.md`
- `.tf/plans/<date>-<topic>/02-spec.md`
- `.tf/plans/<date>-<topic>/03-implementation-plan.md`
- `.tf/plans/<date>-<topic>/04-ticket-breakdown.md`
- `.tf/plans/<date>-<topic>/tickets.yaml`
- `.subagent-runs/*` chain artifacts
- `.tf/knowledge/*` persistent research cache
- `.tf/progress.md` progress entries
- `.tf/AGENTS.md` lessons learned (new + useful only)
