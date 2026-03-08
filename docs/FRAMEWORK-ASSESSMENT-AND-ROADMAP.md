# pi-tk-flow Framework Assessment and Roadmap

This document captures the major findings from the original repository analysis and turns them into a concrete remediation plan.

It intentionally separates:
- the **shipped pi-tk-flow framework surface**
- the **self-hosting workflow artifacts** used while developing `pi-tk-flow`
- the **optional UI/TUI layer**

This distinction matters because the repository is both:
1. the source code of the `pi-tk-flow` package, and
2. a live user of `pi-tk-flow` for its own development.

---

## 1. Scope legend

### Framework surface
Files and behaviors that are part of the shipped package:
- `README.md`
- `PROJECT.md`
- `AGENTS.md`
- `MODEL-CONFIGURATION.md`
- `CONTEXT-GUIDE.md`
- `REFACTOR-SIMPLIFY-SPEC.md`
- `prompts/`
- `assets/agents/`
- `assets/chains/`
- `extensions/`
- `package.json`
- `pyproject.toml`
- package-facing tests

### Self-hosting artifacts
Not package source; these are runtime/project artifacts for developing `pi-tk-flow` itself:
- `.tf/`
- `.tickets/`
- `.subagent-runs/`

### UI/TUI layer
Optional Python/Textual-based tooling under:
- `python/`

---

## 2. Executive summary

### Original high-level conclusion
The original analysis found that `pi-tk-flow` had:
- strong workflow concepts
- good building blocks
- meaningful subagent specialization
- promising context-engineering ideas

But it also had significant maturity problems in:
- naming and command-surface coherence
- package-vs-self-hosting boundaries
- context architecture consistency
- knowledge storage conventions
- prompt/chain/doc drift
- packaging assumptions
- test coverage for workflow semantics

### Current status summary
A substantial subset of the **framework-level** issues has already been addressed:
- `tf-*` vs `tk` command boundary has been normalized in package files
- `/tf-bootstrap` is the package command surface
- package docs now distinguish shipped framework files from self-hosting artifacts
- package-level `PROJECT.md` now exists
- downstream context conventions are documented in `CONTEXT-GUIDE.md`
- model behavior is documented in `MODEL-CONFIGURATION.md`
- `planner` was removed
- `/tf-refactor` and `/tf-simplify` were added as package prompts
- `tf-refactor` / `tf-simplify` chain presets were added
- package-surface tests now guard naming drift and manifest drift

However, several issues remain open or only partially addressed.

---

## 3. Original findings and remediation plans

## Finding A — Command boundary confusion (`tf-*` vs `tk`)

### Original problem
The repository mixed:
- `tf-*` as pi-tk-flow workflow commands/agents
- `tk` as the ticket CLI
- legacy `tk-*` pi workflow names from older releases

This produced real contract drift in prompts, docs, and agents.

### Why it mattered
Without a hard boundary:
- users get inconsistent instructions
- agents mutate tickets using the wrong namespace
- docs and runtime behavior drift over time

### Current status
**Mostly resolved on the framework surface.**

Completed:
- normalized package docs/prompts/assets to use `tk` for ticket CLI operations
- normalized package workflow surface to `tf-*`
- renamed bootstrap surface to `/tf-bootstrap`
- added tests to detect:
  - wrong `tf add-note` / `tf close` / `tf status`
  - legacy `/tk-*` workflow command references in package files

### Remaining work
- keep regression tests in place and extend them when new commands are added
- explicitly decide whether any compatibility aliases should ever exist

### Plan
1. Keep the current no-alias package stance.
2. Extend package tests whenever a new workflow command is introduced.
3. If compatibility aliases are ever added, document them explicitly rather than allowing accidental drift.

### Priority
**Done for current framework surface; maintain via tests.**

---

## Finding B — Package source vs self-hosting artifact confusion

### Original problem
The repo mixed package-facing truth with self-hosting workflow artifacts.
That made it unclear whether `.tf/` and `.tickets/` were:
- part of the product contract, or
- merely the package using itself.

### Why it mattered
This muddied:
- source-of-truth boundaries
- context engineering
- maintenance decisions
- documentation strategy

### Current status
**Resolved conceptually for the framework surface.**

Completed:
- `PROJECT.md` now documents the distinction
- `AGENTS.md` now documents the distinction operationally
- package docs no longer treat self-hosting artifacts as package source of truth

### Remaining work
- self-hosting artifacts themselves still contain historical drift and should be cleaned separately, outside package-surface refactoring

### Plan
1. Keep package docs and package tests strictly framework-facing.
2. Handle self-hosting cleanup in a separate workstream.
3. Never use `.tf/...` as the canonical package documentation layer again.

### Priority
**Framework resolved; self-hosting cleanup deferred.**

---

## Finding C — Missing stable project context model (`PROJECT.md` / `AGENTS.md` split)

### Original problem
The framework had durable memory concepts, but no strong package-level story for:
- project truth
- agent operating instructions
- retrieval order
- downstream adoption patterns

### Why it mattered
Without this split, downstream projects had no clean model for:
- what the project is
- how agents should behave
- where durable knowledge should live

### Current status
**Largely addressed.**

Completed:
- added package `PROJECT.md`
- rewrote package `AGENTS.md`
- added `CONTEXT-GUIDE.md`
- updated prompts/chains/agents to acknowledge:
  - `PROJECT.md`
  - `AGENTS.md`
  - `.tf/knowledge/...`

### Remaining work
- package docs could still make retrieval order even more explicit in command-specific sections
- some prompts still rely heavily on prose rather than machine-verifiable retrieval contracts

### Plan
1. Add small “Context sources” subsections to major command docs in `README.md`.
2. Add prompt-surface tests asserting that core context-aware prompts reference:
   - `PROJECT.md`
   - `AGENTS.md`
   - `.tf/knowledge/...`
3. Consider a future package-level `CONTEXT-CONTRACT.md` if command-specific context rules grow further.

### Priority
**Mostly addressed; low/medium remaining work.**

---

## Finding D — Knowledge layer was inconsistent and only half formalized

### Original problem
The original analysis found incompatible or drifting storage assumptions for knowledge:
- flat topic files in some places
- per-topic directories in others
- unclear durable vs transient boundaries

### Why it mattered
This weakened context engineering because the system could not clearly answer:
- where durable knowledge goes
- what is reusable
- what is just a run artifact

### Current status
**Largely addressed.**

Completed:
- package now recommends directory-based topic knowledge:
  - `.tf/knowledge/topics/<topic-slug>/summary.md`
  - `.tf/knowledge/topics/<topic-slug>/research.md`
  - `.tf/knowledge/topics/<topic-slug>/library-research.md`
- package docs now distinguish durable topic/ticket knowledge from transient runtime artifacts
- research persistence in planning/brainstorm prompts now uses canonical topic filenames:
  - `research.md`
  - `library-research.md`
- refinement persistence now uses clearer canonical snapshot names:
  - `implementation-plan.md`
  - `refinement-summary.md`

### Remaining work
The framework still needs stronger automated coverage for the persistence contract, especially to prevent reintroduction of deprecated names or flat topic-file paths.

### Plan
1. Keep the canonical topic directory model centered on:
   - `summary.md`
   - `research.md`
   - `library-research.md`
2. Allow well-scoped optional topic artifacts when needed, using stable names such as:
   - `anchor-context.md`
   - `plan-gaps.md`
   - `plan-review.md`
   - `implementation-plan.md`
   - `refinement-summary.md`
3. Add tests that fail if deprecated names reappear in package prompts or docs.
4. Add tests that fail if flat topic paths like `.tf/knowledge/topics/<topic-slug>.md` reappear in package files.

### Priority
**Low/medium — mostly normalized, but should be guarded by tests.**

---

## Finding E — Too much critical workflow behavior lives only in prose

### Original problem
A large amount of framework behavior is defined in long prompt documents using natural-language protocol descriptions.

### Why it mattered
This makes the framework:
- flexible
- expressive

but also:
- hard to test semantically
- easy to drift
- difficult to validate mechanically

### Current status
**Still open.**

Completed:
- package-surface tests now catch naming/manifest/surface drift
- some prompt/chain alignment issues were fixed

Not yet done:
- no deep semantic tests for prompt flags, branching, or artifact contracts
- no mechanical validation of required sections or expected runtime structures

### Plan
1. Add semantic prompt tests for every major command.

Examples:
- `tf-implement` includes all supported interactive flags
- `tf-refactor` and `tf-simplify` include both ticket mode and goal mode
- `tf-bootstrap` docs/command names remain aligned
- required artifact names remain stable (`anchor-context.md`, `close-summary.md`, etc.)

2. Add command-contract tests for:
- supported flags
- required artifact outputs
- required agent references
- required `tk` operations in ticket-mode closers

3. Optionally introduce structured metadata blocks in prompts for:
- supported flags
- expected artifacts
- required agents

That would make validation much easier.

### Priority
**High — this is the biggest remaining framework maturity gap.**

---

## Finding F — Prompt/chain duplication creates future drift risk

### Original problem
The framework has both:
- prompt templates as the real top-level workflow logic
- chain presets as reusable but partly overlapping workflow descriptions

### Why it mattered
That duplication creates a structural risk of drift.

### Current status
**Improved but not solved.**

Completed:
- implementation path presets were aligned with current `/tf-implement`
- new refactor/simplify presets were added
- README now clarifies that prompts are authoritative and chains are static representative workflows

### Remaining work
There is still no single source of truth that generates both prompt contracts and chain presets.

### Plan
1. Keep the current model for now, but explicitly categorize chain presets as one of:
   - representative static presets
   - compatibility artifacts
   - supported reusable building blocks

2. Add README sections clarifying intended usage for each chain family.
3. Longer term, consider generating chain docs from structured prompt metadata or vice versa.

### Priority
**Medium.**

---

## Finding G — Package manifest and bootstrap assumptions were inconsistent

### Original problem
The package declared a `./skills` surface even though no bundled skills directory existed.
Bootstrap behavior also implied a package shape that was not actually shipped.

### Why it mattered
This created:
- manifest drift
- broken assumptions for installers
- package-surface confusion

### Current status
**Resolved for current package shape.**

Completed:
- removed nonexistent `./skills` registration from `package.json`
- made `/tf-bootstrap` safe when `--copy-skills` is requested in a release with no bundled skills
- updated docs accordingly

### Remaining work
- if bundled skills are added in the future, restore manifest registration intentionally and add coverage tests

### Plan
1. Keep the current no-skills package manifest until skills really ship.
2. If skills are introduced later, add tests for:
   - manifest registration
   - bootstrap copy behavior
   - README installation/copy docs

### Priority
**Resolved for now.**

---

## Finding H — Deprecated or stale surface area diluted the framework

### Original problem
Deprecated/stale assets existed in the shipped surface, especially `planner`.
Auxiliary specialist agents also lacked a clear product story.

### Why it mattered
This increased cognitive load and blurred what the supported framework actually was.

### Current status
**Partially addressed.**

Completed:
- removed `planner`
- clarified `refactorer` and `simplifier` as specialist agents behind workflow surfaces
- added `/tf-refactor` and `/tf-simplify`

### Remaining work
- decide how strongly `refactorer` / `simplifier` should be positioned as public building blocks vs internal specialists behind commands
- possibly review whether other auxiliary agents need similar explicit positioning

### Plan
1. Keep `refactorer` and `simplifier` as shipped specialist agents.
2. Treat `/tf-refactor` and `/tf-simplify` as the primary public API.
3. Update README language to reflect that distinction even more clearly if direct subagent use is not encouraged.
4. Audit whether any other auxiliary agents should be repositioned or removed.

### Priority
**Low/medium.**

---

## Finding I — Refactor/simplify workflows were missing from the framework surface

### Original problem
The original analysis noted that refactor/simplify intent existed at planning time (`--mode refactor|simplify`) but not as first-class execution workflows.

### Why it mattered
Without dedicated commands, users would rely on:
- ad hoc main-agent behavior
- or direct subagent usage

which weakens the value of the framework.

### Current status
**Addressed.**

Completed:
- added `REFACTOR-SIMPLIFY-SPEC.md`
- added `prompts/tf-refactor.md`
- added `prompts/tf-simplify.md`
- added chain presets for both
- updated README and tests

### Remaining work
- add deeper semantic tests for the new commands
- optionally document more examples in README

### Plan
1. Add semantic tests for the new prompts.
2. Add more README examples if adoption proves useful.
3. Decide whether to add specialized model mappings or keep the current `glm-5` defaults.

### Priority
**Implemented, but still needs stronger tests.**

---

## Finding J — Package docs relied too much on self-hosting knowledge artifacts

### Original problem
Model configuration and some framework guidance effectively lived in `.tf/knowledge/...`, which is the wrong layer for package truth.

### Why it mattered
It made framework docs depend on this repository’s self-hosted runtime artifacts.

### Current status
**Resolved for the framework surface.**

Completed:
- added `MODEL-CONFIGURATION.md`
- README now points to package docs, not self-hosting knowledge, for model behavior

### Remaining work
- keep future package docs in root/package-facing locations, not `.tf/...`

### Plan
1. Continue treating `.tf/...` as repo-local self-hosting context only.
2. Add package docs in root/package-facing locations whenever new framework-level behavior is introduced.

### Priority
**Resolved.**

---

## Finding K — Runtime workflow testing was thin

### Original problem
Most tests covered utilities and UI-adjacent code rather than the workflow framework semantics themselves.

### Why it mattered
A workflow package is mature only when its command contracts are tested, not just its helper modules.

### Current status
**Improved but still incomplete.**

Completed:
- added `tests/test_package_surface.py`
- package-surface tests now cover:
  - prompt existence
  - chain existence
  - manifest registration
  - README command references
  - removal of `planner`
  - project-context references in new prompts
  - wrong namespace regression checks
  - model mapping coverage references

### Remaining work
The package still lacks tests for actual workflow semantics such as:
- required flag presence in prompt files
- ticket-mode vs goal-mode branch guarantees
- artifact naming and role consistency across prompts
- agent/chain parity where intended

### Plan
1. Add semantic prompt tests, for example:
   - `tf-implement` includes expected flags and artifacts
   - `tf-refactor` and `tf-simplify` include both ticket and goal mode logic
   - `tf-bootstrap` surface remains aligned with extension registration
2. Add tests that verify required agent references per command.
3. Add tests that verify knowledge persistence paths follow the supported package contract.

### Priority
**High.**

---

## Finding L — Optional UI/TUI docs and implementation drift existed

### Original problem
The original analysis found drift between:
- UI docs
- implemented tabs/features
- topic scanning assumptions

### Why it mattered
This affected optional UI coherence, but not the core workflow framework.

### Current status
**Intentionally deferred.**

### Plan
1. Treat UI/TUI as a separate cleanup workstream.
2. Do not let UI/TUI drift distract from workflow framework maturity.
3. Revisit only after the workflow semantics and package contracts are stable enough.

### Priority
**Deferred.**

---

## 4. Prioritized roadmap

## Phase 1 — Already completed or mostly completed
- normalize `tf-*` vs `tk`
- separate package docs from self-hosting artifacts
- add package-level `PROJECT.md`
- add `CONTEXT-GUIDE.md`
- add `MODEL-CONFIGURATION.md`
- remove `planner`
- add `/tf-refactor` and `/tf-simplify`
- add package-surface regression tests

## Phase 2 — Highest-value remaining work

### 2.1 Add semantic prompt-contract tests
Add tests for:
- required supported flags
- required artifact names
- required mode branches
- required `tk` operations in ticket-mode closers
- prompt/README/model mapping consistency

### 2.2 Decide and normalize topic artifact naming
Choose whether topic directories use:
- a canonical minimal schema, or
- workflow-specific canonical filenames

Then align prompts, agents, docs, and tests.

### 2.3 Clarify chain preset support level
Decide and document whether chain presets are:
- fully supported reusable API artifacts, or
- representative/static reference artifacts

## Phase 3 — Medium-term improvement
- introduce more structured metadata in prompts
- reduce reliance on prose-only protocol sections
- consider generation or stronger validation for prompt/chain consistency

## Phase 4 — Separate deferred workstream
- self-hosting artifact cleanup under `.tf/`, `.tickets/`, `.subagent-runs/`
- optional UI/TUI cleanup under `python/`

---

## 5. Recommended next implementation tickets

### Ticket 1 — Semantic prompt contract tests
Add tests covering:
- flags
- branches
- artifacts
- required agents
- namespace rules

### Ticket 2 — Knowledge persistence normalization
Choose and implement the canonical topic directory naming model.

### Ticket 3 — Chain preset policy and docs
Document the exact support level of chain presets and tighten docs accordingly.

### Ticket 4 — Prompt metadata hardening
Investigate a structured metadata convention for shipped prompts to reduce prose-only drift.

---

## 6. Closing assessment

### Framework state before remediation
- strong concept
- medium coherence
- medium-low maturity

### Framework state now
- strong concept
- good coherence
- medium maturity moving toward medium-high

### Biggest remaining issue
The single most important remaining framework issue is:

> too much workflow behavior is still encoded only as prose, with limited semantic test coverage.

That is the best place to focus next.
