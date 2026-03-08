---
description: Initialize pi-tk-flow context for a greenfield or brownfield project
model: glm-5
thinking: medium
---

Initialize pi-tk-flow project context from `$@`.

This command creates or updates the baseline project context needed to use `pi-tk-flow` well:
- `PROJECT.md`
- `AGENTS.md`
- `.tf/AGENTS.md`
- `.tf/knowledge/README.md`
- `.tf/knowledge/baselines/coding-standards.md`
- `.tf/knowledge/baselines/testing.md`
- `.tf/knowledge/baselines/architecture.md`
- `.tf/plans/`
- `.tf/knowledge/topics/`
- `.tf/knowledge/tickets/`
- `.tickets/`

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--greenfield` initialize from a project interview / brief
- `--brownfield` initialize from existing repo evidence
- `--from <path>` optional seed brief / architecture note / product doc
- `--dry-run` analyze and propose file contents without writing
- `--no-overwrite` create missing files but do not replace existing files

Rules:
1. Remaining non-flag text is `PROJECT_BRIEF`.
2. If both `--greenfield` and `--brownfield` are present, STOP and ask the user to choose one.
3. If `--from` is provided, verify the file exists before continuing.
4. If neither `--greenfield` nor `--brownfield` is present:
   - choose **brownfield** when the repo already has strong project signals such as `README.md`, source directories, test directories, package manifests, CI config, or architecture docs
   - otherwise choose **greenfield**
5. In greenfield mode, if the brief plus `--from` content are not enough to produce credible drafts, ask a compact interview questionnaire and STOP until the user answers.
6. In brownfield mode, only ask follow-up questions when critical ambiguity would make the generated docs misleading.
7. In `--dry-run` mode, do not write files; instead, report what would be created/updated/skipped and summarize the proposed content for each file.

## 1) Required Paths and Directories

Target files:
- `PROJECT.md`
- `AGENTS.md`
- `.tf/AGENTS.md`
- `.tf/knowledge/README.md`
- `.tf/knowledge/baselines/coding-standards.md`
- `.tf/knowledge/baselines/testing.md`
- `.tf/knowledge/baselines/architecture.md`

Ensure directories exist:
- `.tf/`
- `.tf/knowledge/`
- `.tf/knowledge/baselines/`
- `.tf/knowledge/topics/`
- `.tf/knowledge/tickets/`
- `.tf/plans/`
- `.tickets/`

Optional hygiene:
- If `.gitignore` exists and does not already include `.subagent-runs/`, add it.
- Do **not** add `.tf/` or `.tickets/` to `.gitignore`; they are durable project artifacts.

## 2) File Ownership Model

### `PROJECT.md`
This is project truth.
It should contain:
- mission
- users / stakeholders
- goals
- non-goals
- domain model / glossary (when relevant)
- architecture overview
- stack
- constraints
- quality bar
- invariants
- current reality
- source-of-truth references
- links to baseline knowledge files:
  - `.tf/knowledge/baselines/coding-standards.md`
  - `.tf/knowledge/baselines/testing.md`
  - `.tf/knowledge/baselines/architecture.md`

### `AGENTS.md`
This should always include a **standard pi-tk-flow managed block** plus a **project-specific guidance** section.

Use these exact markers:

```md
<!-- PI-TK-FLOW:START -->
... managed block ...
<!-- PI-TK-FLOW:END -->
```

Rules:
- If `AGENTS.md` does not exist, create it with the managed block first, then a `## Project-specific guidance` section.
- If `AGENTS.md` exists and already contains the markers, replace only the managed block and preserve everything outside it.
- If `AGENTS.md` exists and does not contain the markers, prepend the managed block and retain existing content below a `## Project-specific guidance` heading when practical.
- The managed block should stay largely standardized across projects.
- The project-specific section should contain repo-local guidance inferred from the repo or provided by the user.

### `.tf/AGENTS.md`
Create an initial reusable lessons file with a concise lessons format and a warning not to store ticket-specific trivia.

### `.tf/knowledge/README.md`
Explain the durable knowledge model:
- baselines
- topics
- tickets
- durable vs transient
- `.subagent-runs/` is transient only

### Baseline files
Create all three baseline files and keep them separate from `PROJECT.md`.
`PROJECT.md` should link to them instead of embedding all baseline details directly.

## 3) Standard AGENTS Managed Block

Use this content for the managed block, adapting only tiny repo-specific wording where necessary:

```md
<!-- PI-TK-FLOW:START -->
## pi-tk-flow operating model
- `PROJECT.md` is the canonical source for project/product/system context.
- `tf-*` refers to pi-tk-flow prompts, agents, and workflow commands.
- `tk` refers to the external ticket CLI only.
- Legacy `tk-*` pi commands/agents should not be used for new work.

## Read order
Before non-trivial work, read in this order:
1. `AGENTS.md`
2. `PROJECT.md`
3. relevant architecture/stack docs and referenced project docs
4. relevant `.tf/knowledge/...`
5. relevant `.tf/plans/...` and `.tickets/...` when doing planned or ticketed work
6. transient `.subagent-runs/...` artifacts only for the current run

## Command boundary
- Use `/tf-bootstrap` to install/update shipped pi-tk-flow templates.
- Use `/tf-init` to initialize project context for pi-tk-flow adoption.
- Use `/tf-brainstorm`, `/tf-plan`, `/tf-plan-check`, `/tf-plan-refine`, `/tf-ticketize`, `/tf-implement`, `/tf-refactor`, and `/tf-simplify` for workflow execution.
- Use `tk` for ticket operations: `tk ready`, `tk show`, `tk add-note`, `tk status`, `tk close`, etc.

## Knowledge rules
- Keep durable reusable knowledge under `.tf/knowledge/...`.
- Keep transient runtime artifacts under `.subagent-runs/...` only.
- Prefer topic directories such as `.tf/knowledge/topics/<topic-slug>/summary.md`, `research.md`, and `library-research.md`.
- Use baseline files under `.tf/knowledge/baselines/` for coding standards, testing expectations, and architecture reference material.

## Guardrails
- Do not treat `.subagent-runs/...` as durable truth.
- Do not mix the `tf-*` workflow surface with the `tk` ticket CLI.
- Update `PROJECT.md` and `.tf/knowledge/baselines/...` when durable project understanding changes materially.
<!-- PI-TK-FLOW:END -->
```

After the managed block, include:

```md
## Project-specific guidance
```

Populate that section with concise repo-local notes when known.
If little is known yet, add a short placeholder telling future maintainers to capture repo-specific guardrails there.

## 4) Brownfield Evidence Collection

In **brownfield** mode, gather evidence from the existing repo before writing anything.
Use `bash` for discovery and `read` for files.
Do not use broad blind scans when a focused scan is enough.

Prioritize evidence sources like:
- `README.md`
- `docs/` and architecture docs
- package manifests: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.
- lockfiles and workspace config
- lint / format / typecheck config
- test config and representative tests
- CI files
- deployment or infra docs
- top-level source directories

Infer and document:
- mission and current reality
- major subsystems and architecture boundaries
- main languages, frameworks, and tooling
- coding conventions visible from config and representative code
- testing strategy visible from config, CI, and test layout
- repo-specific agent guidance worth putting in `AGENTS.md`

Brownfield writing rules:
- Clearly distinguish **confirmed facts**, **reasonable inferences**, and **open questions**.
- Do not fabricate certainty.
- If a major unknown would make the docs misleading, ask a compact follow-up question before writing.
- Otherwise, write useful first-pass docs and include an `Open Questions` section where needed.

## 5) Greenfield Interview Workflow

In **greenfield** mode, use `PROJECT_BRIEF` and optional `--from` content first.
If that is insufficient, ask one compact interview that covers the essentials.

Preferred question set:
1. What is the project trying to achieve?
2. Who are the main users or stakeholders?
3. What are the most important goals and explicit non-goals?
4. What stack or platform constraints already exist?
5. What high-level architecture do you expect?
6. What coding standards or style preferences matter most?
7. What testing expectations should be enforced from the start?
8. Are there special delivery, security, data, or compliance constraints?
9. What should agents be especially careful about in this repo?

Greenfield writing rules:
- Prefer concrete, practical defaults over vague placeholders.
- If the user does not specify something, state a clearly labeled assumption.
- Include `Open Questions` only where the choice is important and unresolved.
- Keep the initial docs lean but genuinely usable.

## 6) Content Requirements by File

### `PROJECT.md`
Create a project-specific document with this shape:

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

## Baseline Guides
- [Coding Standards](.tf/knowledge/baselines/coding-standards.md)
- [Testing](.tf/knowledge/baselines/testing.md)
- [Architecture](.tf/knowledge/baselines/architecture.md)

## Source-of-Truth References
```

Requirements:
- In brownfield mode, ensure `Current Reality` reflects real repo state, technical debt, or known migration constraints.
- In greenfield mode, `Current Reality` should explicitly say that this is an initial planned state.
- Link the baseline files exactly as shown above.

### `.tf/knowledge/baselines/coding-standards.md`
Include sections such as:
- Summary
- Confirmed Conventions / Planned Conventions
- Naming and Structure
- Error Handling and Logging
- API / Interface Stability Expectations
- Code Review Expectations
- Open Questions

### `.tf/knowledge/baselines/testing.md`
Include sections such as:
- Summary
- Test Pyramid / Strategy
- Required Checks
- Test Organization
- Regression Policy
- Definition of Done for Changes
- Open Questions

### `.tf/knowledge/baselines/architecture.md`
Include sections such as:
- Summary
- System Shape
- Major Boundaries
- Data / Integration Considerations
- Deployment / Runtime Considerations
- Known Risks or Constraints
- Open Questions

### `.tf/knowledge/README.md`
Explain:
- what belongs in `baselines/`
- what belongs in `topics/`
- what belongs in `tickets/`
- durable vs transient storage
- recommended filenames for topic knowledge

### `.tf/AGENTS.md`
Seed with a reusable lessons template like:

```md
# Lessons Learned (Reusable)

Add lessons here only when they are:
1. New (not already documented), and
2. Useful for later work.

Avoid ticket-specific trivia and duplicates.

## Format

### <Short lesson title>
- **When to apply:** <situation>
- **Lesson:** <concise reusable guidance>
- **Source:** <ticket/plan/context>
```

## 7) Overwrite Rules

- `--no-overwrite`:
  - create missing files and directories
  - do not replace existing files
  - report skipped files clearly
- default behavior without `--no-overwrite`:
  - update or create the target files
  - preserve non-managed portions of `AGENTS.md` whenever possible
- `--dry-run`:
  - never write
  - show which files would be created, updated, or skipped

## 8) Final Response

When finished:
1. Report the detected or chosen mode: `greenfield` or `brownfield`.
2. List every file/directory created, updated, or skipped.
3. Summarize the most important inferred assumptions.
4. Call out any open questions that should be answered next.
5. Recommend the next command, usually one of:
   - `/tf-bootstrap --scope project --copy-all`
   - `/tf-plan <topic>`
   - `/tf-brainstorm <topic>`
