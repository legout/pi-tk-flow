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

Optional project-local templates (trusted repos only):

```bash
/tk-bootstrap --scope project
```

Materialize prompts + skills into local scope directories:

```bash
/tk-bootstrap --scope user --copy-all
/tk-bootstrap --scope project --copy-all
```

Preserve local edits (no overwrite when content differs):

```bash
/tk-bootstrap --scope user --copy-all --no-overwrite
```

## Run workflow

### 0) Optional brainstorm

```bash
/tk-brainstorm <topic>
/tk-brainstorm <topic> --mode feature|refactor|simplify --research
```

### 1) Plan

```bash
/tk-plan <topic>                          # fast mode (default) — parallel PRD/Spec/Design
/tk-plan <topic> --thorough               # sequential with full synthesis
/tk-plan <topic> --mode feature|refactor|simplify
/tk-plan <topic> --from .tf/plans/<plan-dir>/00-design.md
```

**Fast vs Thorough:**
- `--fast` (default): PRD, Spec, and Design created in parallel (~30% faster)
- `--thorough`: Sequential PRD → Spec → Design with full cross-synthesis (higher quality docs)

### 2) Ticketize

```bash
/tk-ticketize .tf/plans/<plan-dir>/03-implementation-plan.md           # create tickets (default)
/tk-ticketize .tf/plans/<plan-dir>/03-implementation-plan.md --dry-run # preview only
```

### 3) Implement

```bash
/tk-implement <ticket-id>         # main agent decides path after analysis
/tk-implement <ticket-id> --async # background execution
```

**How it works:**
1. Always runs `scout` → `context-builder` first
2. **YOU (the main agent)** analyze the ticket and anchor context
3. Choose the path:
   - **Path A (Minimal)**: Simple config/docs/fixes. No research. Review only.
   - **Path B (Standard)**: Features/integrations. Planner + sequential review→test.
   - **Path C (Deep)**: Complex/AI/novel work. Research (if needed) + parallel review+test.
4. Research is never skipped when context identifies knowledge gaps

## Expected artifacts

- `.tf/plans/<date>-<topic>/00-brainstorm.md`
- `.tf/plans/<date>-<topic>/00-design.md`
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
- `tk-ticketize` defaults to `--create` (creates tickets immediately). Use `--dry-run` to preview.
- `tk-plan` defaults to `--fast` (parallel documenters). Use `--thorough` for sequential synthesis.
- `tk-bootstrap` overwrites changed files by default; add `--no-overwrite` to keep local modifications (changed files are skipped).
- `tk-implement`: Main agent decides path after analyzing ticket. Research is never skipped when needed.
