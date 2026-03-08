# Context Guide for Projects Using pi-tk-flow

This guide describes the recommended context layout for projects that adopt `pi-tk-flow`.

It is intentionally separate from:
- `PROJECT.md` — the context for this repository itself
- `AGENTS.md` — the agent operating instructions for this repository
- `.tf/` — the self-hosting runtime artifacts used while developing `pi-tk-flow`

---

## 1. Core Model

Use the following split in any project that wants to use `pi-tk-flow` well:

- `PROJECT.md` = project truth
- `AGENTS.md` = agent operating instructions
- `.tf/knowledge/` = durable reusable learned context
- `.tf/plans/` = initiative planning artifacts
- `.tickets/` = execution units
- `.subagent-runs/` = transient runtime artifacts only

### Command Boundary
- `tf-*` = pi-tk-flow prompts, agents, and workflow commands
- `tk` = external ticket CLI only

Examples:
- `/tf-plan`, `/tf-ticketize`, `/tf-implement`
- `tk ready`, `tk show`, `tk add-note`, `tk status`, `tk close`

---

## 2. Responsibilities by File/Folder

## `PROJECT.md`
Use this for durable project/product/system context:
- mission
- users
- goals and non-goals
- domain model / glossary
- architecture summary
- stack summary
- constraints
- quality bar
- invariants
- current reality / known gaps

This answers:
> What is this project, and what matters here?

## `AGENTS.md`
Use this for repo-specific operating instructions:
- what to read first
- workflow expectations
- tf vs tk boundary
- research expectations
- knowledge storage rules
- repo-specific guardrails

This answers:
> How should an agent work here?

## `.tf/knowledge/`
Use this for durable reusable learned context.
Do not turn it into a dump of transient run logs.

## `.tf/plans/`
Use this for initiative-specific planning artifacts.

## `.tickets/`
Use this for execution units tracked by `tk`.

## `.subagent-runs/`
Use this for transient runtime artifacts only.
Never treat it as durable truth.

---

## 3. Recommended `.tf/knowledge/` Structure

Prefer a directory-based topic model.

```text
.tf/
  knowledge/
    README.md
    index.md                      # optional
    baselines/
      coding-standards.md
      testing.md
      architecture.md
    topics/
      <topic-slug>/
        summary.md
        research.md
        library-research.md
        anchor-context.md
        plan-gaps.md
        plan-review.md
        implementation-plan.md
        refinement-summary.md
        architecture-notes.md
        sources.md
    tickets/
      <ticket-id>/
        research.md
        implementation.md
        review.md
        fixes.md
        close-summary.md
```

## Durable vs transient

### Durable
Store in `.tf/knowledge/...`
- topic summaries
- architecture notes
- external research worth reusing
- library behavior worth reusing
- ticket-level durable summaries

### Transient
Store in `.subagent-runs/...`
- temporary anchor contexts
- chain scratch outputs
- intermediate merge artifacts
- ephemeral run-specific notes

---

## 4. Recommended Read Order

## For planning work
1. `AGENTS.md`
2. `PROJECT.md`
3. referenced architecture/stack docs
4. relevant `.tf/knowledge/...`
5. relevant prior plan artifacts

## For implementation work
1. `AGENTS.md`
2. `PROJECT.md`
3. relevant ticket file in `.tickets/`
4. relevant plan docs in `.tf/plans/`
5. relevant `.tf/knowledge/tickets/...`
6. relevant `.tf/knowledge/topics/...`
7. transient anchor context for the current run

## For research work
1. `AGENTS.md`
2. `PROJECT.md`
3. existing `.tf/knowledge/...`
4. external research only for real gaps

---

## 5. Greenfield Setup

For a new project adopting `pi-tk-flow`, create these early:

- `PROJECT.md`
- `AGENTS.md`
- `.tf/AGENTS.md`
- `.tf/knowledge/README.md`
- `.tf/knowledge/baselines/coding-standards.md`
- `.tf/knowledge/baselines/testing.md`
- `.tf/knowledge/baselines/architecture.md`

The recommended shortcut is to let `/tf-init --greenfield` create these for you.

### Greenfield sequence
1. Install `pi-tk-flow` and `pi-subagents`
2. Optionally run `/tf-bootstrap --scope project --copy-all`
3. Run `/tf-init --greenfield` with a short project brief
4. Review/refine the generated `PROJECT.md`, `AGENTS.md`, and baseline files
5. Use `/tf-brainstorm` or `/tf-plan`
6. Run `/tf-plan-check` when the work is non-trivial
7. Run `/tf-ticketize`
8. Execute with `/tf-implement <ticket-id>`

---

## 6. Brownfield Migration Plan

Brownfield adoption should stabilize context before optimizing workflow details.

## Phase 1 — Run `/tf-init --brownfield`
Let the command scan the existing repo and synthesize first-pass versions of:
- `PROJECT.md`
- `AGENTS.md`
- `.tf/AGENTS.md`
- `.tf/knowledge/README.md`
- `.tf/knowledge/baselines/coding-standards.md`
- `.tf/knowledge/baselines/testing.md`
- `.tf/knowledge/baselines/architecture.md`

It should derive these from:
- `README.md`
- existing architecture docs
- deployment docs
- CI/CD files
- code layout
- representative code and tests
- tribal knowledge or optional follow-up questions

Make sure `PROJECT.md` includes one explicit section:
- `Current Reality`

That prevents idealized docs from misleading agents.

## Phase 2 — Review the generated `AGENTS.md`
Keep the standard pi-tk-flow managed block intact.
Refine only the project-specific guidance beneath it.

Move out of `AGENTS.md` anything that belongs in `PROJECT.md`:
- product description
- long architecture narrative
- stack explanation
- business/domain summary

Keep in the project-specific part of `AGENTS.md`:
- read order adjustments
- workflow expectations
- repo guardrails
- knowledge rules
- concise reusable lessons policy

## Phase 3 — Normalize knowledge layout
Pick one topic storage model and standardize it.

Recommended target:
- `.tf/knowledge/topics/<topic-slug>/summary.md`
- `.tf/knowledge/topics/<topic-slug>/research.md`
- `.tf/knowledge/topics/<topic-slug>/library-research.md`

Avoid mixing:
- `.tf/knowledge/topics/foo.md`
- `.tf/knowledge/topics/foo/...`

## Phase 4 — Separate durable and transient artifacts
Document and enforce:
- durable → `.tf/knowledge/...`
- transient → `.subagent-runs/...`

## Phase 5 — Normalize vocabulary
- keep `tf-*` for pi-tk-flow workflow surface
- keep `tk` for ticket CLI only
- remove legacy `tk-*` pi commands/agents from active use

---

## 7. Minimal Templates

## Minimal `PROJECT.md`

```md
# PROJECT

## Mission

## Users / Stakeholders

## Goals

## Non-Goals

## Domain Model / Glossary

## Architecture Overview

## Stack

## Constraints

## Quality Bar

## Invariants

## Current Reality

## Source-of-Truth References
```

## Minimal `AGENTS.md`

```md
# AGENTS

## Working Model
- `PROJECT.md` is the canonical source for project context.
- `tf-*` = pi-tk-flow workflow commands and agents.
- `tk` = external ticket CLI only.

## Read Order
1. `AGENTS.md`
2. `PROJECT.md`
3. relevant `.tf/knowledge/...`
4. relevant `.tf/plans/...`
5. relevant `.tickets/...`

## Workflow Expectations
- Use `/tf-plan` for non-trivial work.
- Use `/tf-plan-check` before `/tf-ticketize` for larger changes.
- Use `/tf-implement <ticket-id>` for execution.

## Knowledge Rules
- Reuse `.tf/knowledge` before new research.
- Keep durable knowledge in `.tf/knowledge/...`.
- Keep `.subagent-runs/...` transient only.
```

---

## 8. Strong Recommendations

If you only do five things in a project adopting `pi-tk-flow`, do these:

1. create `PROJECT.md`
2. keep `AGENTS.md` operational, not descriptive
3. standardize `.tf/knowledge/topics/<topic-slug>/...`
4. enforce the `tf-*` vs `tk` boundary everywhere
5. treat `.subagent-runs/` as ephemeral only
