# PROJECT

## Mission
`pi-tk-flow` is a reusable pi package for planning, ticketizing, and implementing work with a structured tf-driven workflow. It provides prompt templates, subagent definitions, chain presets, and extensions that help projects move from idea → plan → tickets → implementation with durable context and reusable knowledge.

## Package Surface vs Self-Hosting Artifacts
This repository has two different layers that must not be mixed up:

### Package surface (the product)
These files define what `pi-tk-flow` ships to users and how it behaves:
- `README.md`
- `prompts/`
- `assets/agents/`
- `assets/chains/`
- `extensions/`
- `python/`
- `package.json`
- `pyproject.toml`

### Self-hosting development artifacts (this repo using pi-tk-flow on itself)
These files are runtime and workflow artifacts for developing `pi-tk-flow` itself:
- `.tf/`
- `.tickets/`
- `.subagent-runs/`

Treat the first group as product code and product documentation. Treat the second group as this repository's own usage of the product.

## Users / Stakeholders
- Developers using pi who want a reusable planning + ticket execution workflow
- Maintainers evolving prompt-driven and subagent-driven workflows
- Projects that want durable planning artifacts, ticket decomposition, and implementation orchestration

## Goals
- Provide a coherent tf workflow surface for pi commands and agents
- Keep ticket operations delegated to the external `tk` CLI
- Make planning and implementation context reusable across runs
- Support self-hosting: use pi-tk-flow to evolve pi-tk-flow itself without mixing shipped package logic and repo-local runtime artifacts

## Non-Goals
- Replacing the external `tk` ticket CLI
- Turning `.subagent-runs/` into durable knowledge storage
- Storing package source-of-truth documentation under `.tf/`
- Mixing legacy `tk-*` pi commands with the current `tf-*` workflow surface

## Command Boundary
- `tf-*` = pi-tk-flow prompts, agents, workflow commands, and shipped workflow concepts
- `tk` = external ticket CLI only (`tk ready`, `tk show`, `tk add-note`, `tk status`, `tk close`, ...)
- Legacy `tk-*` pi commands/agents are obsolete and should not be used for new work

## Architecture Overview
The package is organized into a few main layers:
- `prompts/`: top-level pi workflow entry points (`/tf-plan`, `/tf-ticketize`, `/tf-implement`, ...)
- `assets/agents/`: reusable subagent definitions used by prompts/chains
- `assets/chains/`: reusable chain presets
- `extensions/`: pi extension commands such as bootstrap / auxiliary tooling
- `python/`: optional Python-based tooling packaged alongside the workflow

During self-hosted development, `.tf/`, `.tickets/`, and `.subagent-runs/` act as the repo's own working memory and execution artifacts.

## Context Model
For projects using pi-tk-flow, the intended context stack is:
1. `AGENTS.md` — agent operating instructions for the repo
2. `PROJECT.md` — project/product/system truth
3. durable reusable knowledge in `.tf/knowledge/`
   - recommended topic layout: `.tf/knowledge/topics/<topic-slug>/summary.md`, `research.md`, `library-research.md`
   - common optional topic artifacts: `anchor-context.md`, `plan-gaps.md`, `plan-review.md`, `implementation-plan.md`, `refinement-summary.md`
   - recommended ticket layout: `.tf/knowledge/tickets/<ticket-id>/research.md`
4. initiative plans in `.tf/plans/`
5. tickets in `.tickets/`
6. transient run artifacts in `.subagent-runs/`

Within this repo, the same model applies — with the important distinction that `.tf/` and `.tickets/` are self-hosting artifacts, not package source.

## Quality Bar
Changes to the shipped package should preserve:
- clear `tf-*` vs `tk` boundary
- consistency across prompts, assets, extensions, and README
- durable context conventions that downstream projects can adopt
- minimal ambiguity about what is product code vs self-hosting runtime state

## Invariants
- Package-facing workflow definitions live at the repo root or in their designated product folders (`prompts/`, `assets/`, `extensions/`, `python/`)
- Self-hosting artifacts live under `.tf/`, `.tickets/`, and `.subagent-runs/`
- Ticket mutations and ticket status operations use the external `tk` CLI
- New pi workflow commands and agents use the `tf-*` naming surface

## Current Reality
This repository is both:
1. the source code for `pi-tk-flow`, and
2. a live user of `pi-tk-flow` for its own development

That makes naming, context routing, and artifact boundaries especially important. Drift between package docs/prompts/assets and self-hosting repo artifacts is the main structural risk.

## Source-of-Truth References
- `README.md` — package usage and shipped workflow overview
- `AGENTS.md` — repo operating instructions for agents
- `CONTEXT-GUIDE.md` — recommended project context conventions for greenfield/brownfield adopters
- `prompts/`, `assets/agents/`, `assets/chains/`, `extensions/` — shipped workflow surface
- `.tf/` — self-hosted workflow artifacts for this repo only
