# AGENTS

## Working Model
- `PROJECT.md` is the canonical source for project/package/system context.
- `tf-*` refers to pi-tk-flow prompts, agents, and workflow commands.
- `tk` refers to the external ticket CLI only.
- Legacy `tk-*` pi commands/agents are obsolete and should not be used for new work.

## Package Surface vs Self-Hosting Artifacts
Do not mix these two layers up.

### Package surface (the shipped product)
Treat these as the source of truth for pi-tk-flow itself:
- `README.md`
- `PROJECT.md`
- `docs/`
- `prompts/`
- `assets/agents/`
- `assets/chains/`
- `extensions/`
- `python/`
- `package.json`
- `pyproject.toml`

### Self-hosting artifacts (this repo using pi-tk-flow on itself)
Treat these as runtime/project artifacts for developing `pi-tk-flow`, not as package source:
- `.tf/`
- `.tickets/`
- `.subagent-runs/`

Only modify `.tf/`, `.tickets/`, or `.subagent-runs/` when the task is explicitly about this repo's self-hosted workflow state, plans, tickets, or lessons learned.

## Read Order
Before non-trivial work, read in this order:
1. `AGENTS.md`
2. `PROJECT.md`
3. relevant package source files (`README.md`, `prompts/`, `assets/`, `extensions/`, `python/`)
4. if the task concerns self-hosting workflow behavior, then read relevant `.tf/...` and `.tickets/...` artifacts

## Command Boundary
- Use `tk` for ticket operations: `tk ready`, `tk blocked`, `tk show`, `tk add-note`, `tk status`, `tk close`, etc.
- Use `/tf-bootstrap` to install/update shipped pi-tk-flow templates.
- Use `/tf-init` to initialize project context for greenfield or brownfield adoption.
- Use `/tf-brainstorm`, `/tf-plan`, `/tf-plan-check`, `/tf-plan-refine`, `/tf-ticketize`, `/tf-implement`, `/tf-refactor`, and `/tf-simplify` for workflow execution.

## Workflow Expectations
- Keep product-level workflow definitions in the shipped package surface, not in `.tf/`.
- Keep self-hosting lessons in `.tf/AGENTS.md`.
- Keep reusable durable self-hosting knowledge in `.tf/knowledge/`.
- Prefer directory-based topic knowledge such as `.tf/knowledge/topics/<topic-slug>/summary.md`, `research.md`, and `library-research.md`.
- When workflow-specific topic snapshots are persisted, prefer canonical names like `anchor-context.md`, `plan-gaps.md`, `plan-review.md`, `implementation-plan.md`, and `refinement-summary.md`.
- Treat `.subagent-runs/` as transient runtime state only.

## Change Routing
- If the task is about package behavior, modify the shipped source in `prompts/`, `assets/`, `extensions/`, `python/`, and root docs.
- If the task is about this repo's current implementation work, plans, or tickets, modify `.tf/`, `.tickets/`, and related self-hosting artifacts as needed.
- Do not move package-facing behavior into self-hosting artifacts.
- Do not treat self-hosting artifacts as the product contract.

## Repo-Specific Guardrails
- Preserve the `tf-*` vs `tk` boundary consistently across docs, prompts, agents, and extensions.
- When examples mention ticket CLI operations, they must use `tk`, not `tf`.
- When examples mention pi workflow commands or agents, they must use `tf-*`, not legacy `tk-*` names.
- If a change affects both package docs and self-hosting artifacts, update the package surface first, then align the self-hosting layer intentionally.

## Additional Guidance
- Use `.tf/AGENTS.md` only for reusable lessons learned from self-hosted execution.
- See `CONTEXT-GUIDE.md` for the recommended `PROJECT.md` / `AGENTS.md` / `.tf/knowledge` conventions for projects adopting pi-tk-flow.
