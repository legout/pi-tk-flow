---
name: tk-workflow
description: Bootstrap and run the tk planning -> ticketization -> implementation workflow with subagents, persistent research, progress tracking, and lessons learned.
---

# TK Workflow

Use this workflow for end-to-end delivery:
1) optional brainstorming
2) planning docs
3) ticket creation
4) ticket implementation

Implementation chain presets include a final `tk-closer` step for commit + ticket close/status gating.

## Setup

Install/update subagent templates and reusable chain presets:

```bash
/tk-bootstrap --scope user
```

Optional project-local agents (trusted repos only):

```bash
/tk-bootstrap --scope project
```

## Run workflow

### 0) Optional brainstorm

```bash
/tk-brainstorm <topic>
/tk-brainstorm <topic> --mode feature|refactor|simplify --research
```

### 1) Plan

```bash
/tk-plan <topic>
/tk-plan <topic> --mode feature|refactor|simplify
/tk-plan <topic> --from .tf/plans/<plan-dir>/design.md
```

### 2) Ticketize

```bash
/tk-ticketize .tf/plans/<plan-dir>/03-implementation-plan.md --dry-run
/tk-ticketize .tf/plans/<plan-dir>/03-implementation-plan.md --create
```

### 3) Implement

```bash
/tk-implement <ticket-id>
/tk-implement <ticket-id> --async
/tk-implement <ticket-id> --clarify
```

## Expected artifacts

- `.tf/plans/<date>-<topic>/00-brainstorm.md`
- `.tf/plans/<date>-<topic>/design.md`
- `.tf/plans/<date>-<topic>/01-prd.md`
- `.tf/plans/<date>-<topic>/02-spec.md`
- `.tf/plans/<date>-<topic>/03-implementation-plan.md`
- `.tf/plans/<date>-<topic>/04-ticket-breakdown.md`
- `.tf/plans/<date>-<topic>/tickets.yaml`
- `.subagent-runs/*` chain artifacts
- `.tf/knowledge/` reusable research cache
- `.tf/progress.md` appended progress entries
- `.tf/AGENTS.md` updated only with new, useful lessons

## Notes

- Default agent scope for safety is `user`.
- If you bootstrap with `--scope project`, align prompt agent scope accordingly (`project` or `both`).
- `tk-ticketize` defaults to dry-run unless `--create` is explicitly passed.
