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
  - `tk-ticketize.chain.md`
  - `tk-path-a.chain.md`
  - `tk-path-b.chain.md`
  - `tk-path-c.chain.md`

Implementation presets include a final `tk-closer` step for commit + `tk add-note` + tk close/status gating.
- Skill: `tk-workflow`

## Install

```bash
pi install /Users/volker/coding/libs/pi-tk-flow
# or later via npm/git
```

### pi-subagents dependency

`pi-tk-flow` includes `pi-subagents` as a package dependency and loads its extensions automatically.

- **npm/git install**: dependency is installed automatically by `pi install`.
- **local path install**: run `npm install` once in this repo so `node_modules/pi-subagents` exists.

## Bootstrap agents and chains

```bash
# install/update user-level agents + chain presets (~/.pi/agent/agents)
/tk-bootstrap --scope user

# install/update project-level agents + chain presets (.pi/agents)
/tk-bootstrap --scope project

# preview only
/tk-bootstrap --scope user --dry-run
```

## Run

```bash
# 0) Optional brainstorming brief
/tk-brainstorm <topic>
/tk-brainstorm <topic> --mode feature|refactor|simplify --research

# 1) Planning artifacts (PRD/spec/implementation plan)
/tk-plan <topic>
/tk-plan <topic> --mode feature|refactor|simplify
/tk-plan <topic> --from docs/plans/<plan-dir>/design.md

# 2) Ticket decomposition (safe default: dry-run)
/tk-ticketize docs/plans/<plan-dir>/03-implementation-plan.md --dry-run
/tk-ticketize docs/plans/<plan-dir>/03-implementation-plan.md --create

# 3) Implementation of a ticket
/tk-implement <ticket-id>
/tk-implement <ticket-id> --async
/tk-implement <ticket-id> --clarify
```

Flag behavior:
- `--async`: background mode (`async: true`)
- `--clarify`: open chain clarify TUI (`clarify: true`)
- If both are passed, async wins and clarify is disabled for deterministic background execution.
- `tk-ticketize` defaults to dry-run unless `--create` is explicitly passed.

## Scope behavior

- If project bootstrap marker `.pi/agents/.tk-bootstrap.json` exists, tk prompts should use `agentScope: "project"`.
- Otherwise they should use `agentScope: "user"`.
- Use `"both"` only when intentionally allowing project agents to override user agents.

## Workflow artifacts

- `docs/plans/<date>-<topic>/00-brainstorm.md`
- `docs/plans/<date>-<topic>/design.md`
- `docs/plans/<date>-<topic>/01-prd.md`
- `docs/plans/<date>-<topic>/02-spec.md`
- `docs/plans/<date>-<topic>/03-implementation-plan.md`
- `docs/plans/<date>-<topic>/04-ticket-breakdown.md`
- `docs/plans/<date>-<topic>/tickets.yaml`
- `.subagent-runs/*` chain artifacts
- `.tf/knowledge/*` persistent research cache
- `.tf/progress.md` progress entries
- `.tf/AGENTS.md` lessons learned (new + useful only)
