# Refactor / Simplify Command Spec

This document describes two project-aware workflow commands in `pi-tk-flow`:

- `/tf-refactor`
- `/tf-simplify`

These commands are implemented as first-class workflow surfaces built on top of the existing specialist agents:

- `assets/agents/refactorer.md`
- `assets/agents/simplifier.md`

## Why these commands should exist

`pi-tk-flow` already has strong planning and ticket execution workflows, and it already understands `feature | refactor | simplify` at planning time.

What is missing is an execution-level workflow for repository-aware structural improvements that are:
- explicitly scoped
- behavior-preserving
- validated
- project-context aware

The main agent alone can perform these tasks, but dedicated commands provide:
- a predictable user-facing API
- repeatable context loading
- explicit safety rules
- specialized validation behavior
- better reuse of `PROJECT.md`, `AGENTS.md`, `.tf/knowledge/...`, plans, and tickets

## Design principle

- **Commands** are the user-facing workflow API
- **Agents** are specialist execution roles inside those workflows

So users should run:
- `/tf-refactor ...`
- `/tf-simplify ...`

And those commands should delegate the implementation step to:
- `refactorer`
- `simplifier`

## Command semantics

## `/tf-refactor`
Use when the goal is to improve code structure **without changing external behavior**.

Typical use cases:
- extract helper functions or classes
- split large modules
- consolidate duplication
- improve naming
- improve boundaries and cohesion
- prepare a subsystem for upcoming feature work

Primary success criterion:
- behavior preserved, structure improved

## `/tf-simplify`
Use when the goal is to reduce complexity **without changing behavior**.

Typical use cases:
- reduce nesting / branching
- simplify control flow
- remove dead code
- reduce cyclomatic complexity
- split long functions
- clarify overly clever logic

Primary success criterion:
- behavior preserved, complexity reduced

## Input forms

Both commands should support the same input styles.

### 1. Freeform goal
```bash
/tf-refactor auth service boundaries
/tf-simplify order processing flow
```

### 2. Ticket-driven
```bash
/tf-refactor <ticket-id>
/tf-simplify <ticket-id>
```

### 3. Seed file driven
```bash
/tf-refactor --from docs/refactor-notes.md auth service cleanup
/tf-simplify --from docs/hotspots.md order validation
```

## Recommended flags

### Shared flags
- `--from <path>` optional seed doc / notes / hotspot report
- `--scope <path-or-glob>` constrain the operation to a file/dir area
- `--fast` default lighter planning / anchoring
- `--thorough` deeper planning / scouting
- `--async`
- `--clarify`
- `--interactive`
- `--hands-free`
- `--dispatch`

### Mode-specific optional flags

#### `/tf-refactor`
- `--preserve-api` explicitly emphasize public API stability
- `--prepare-for <goal>` frame the refactor as preparation for future work

#### `/tf-simplify`
- `--hotspots-only` focus only on the highest-complexity areas
- `--max-function-lines <n>` optional target heuristic

## Context loading contract

Both commands should follow the same context stack used elsewhere in the package:

1. `AGENTS.md`
2. `PROJECT.md`
3. relevant referenced architecture/stack docs
4. relevant `.tf/knowledge/...`
5. ticket / plan / seed docs when applicable
6. transient anchor context for the current run

### Ticket mode
If a ticket ID is provided:
- read `.tickets/<id>.md`
- inspect related plan docs if referenced
- inspect `.tf/knowledge/tickets/<id>/...` if present

### Goal mode
If freeform goal text is provided:
- derive a topic slug
- inspect `.tf/knowledge/topics/<topic-slug>/...` when present
- use `--from` material if supplied

## Workflow shape

## `/tf-refactor` default workflow

### Phase 1 — anchor
- build a scoped anchor context
- identify target files, boundaries, tests, and risk areas
- determine whether behavior preservation requires planning depth `fast` or `thorough`

### Phase 2 — plan
Use `plan-fast` or `plan-deep` depending on complexity.

Plan must include:
- target files
- structural changes only
- behavior-preservation assumptions
- validation steps
- rollback notes

### Phase 3 — execute
Run `refactorer` with:
- anchor context
- plan
- project constraints

### Phase 4 — validate
Run:
- `reviewer`
- `tester` (relevant tests/checks only)

### Phase 5 — fix once
Run `fixer` for critical/major issues only.

### Phase 6 — quick re-check
Run `reviewer` again with a narrow go/no-go scope.

### Phase 7 — finalize
If ticket-driven, use `tf-closer` semantics for notes/status/close gate.
If non-ticket-driven, still produce a close/summary artifact without ticket mutation.

## `/tf-simplify` default workflow

### Phase 1 — anchor
- build a scoped anchor context
- identify complexity hotspots
- locate relevant tests and guardrails
- determine whether lighter or deeper planning is needed

### Phase 2 — plan
Use `plan-fast` or `plan-deep` depending on complexity.

Plan must include:
- hotspots to simplify
- explicit behavior-preservation assumptions
- simplification targets
- validation steps
- rollback notes

### Phase 3 — execute
Run `simplifier` with:
- anchor context
- plan
- project constraints

### Phase 4 — validate
Run:
- `reviewer`
- `tester` (relevant tests/checks only)

### Phase 5 — fix once
Run `fixer` for critical/major issues only.

### Phase 6 — quick re-check
Run `reviewer` again with a narrow go/no-go scope.

### Phase 7 — finalize
If ticket-driven, use `tf-closer` semantics for notes/status/close gate.
If non-ticket-driven, still produce a close/summary artifact without ticket mutation.

## Path selection

These commands likely need a lighter path model than `/tf-implement`.

Recommended execution classes:

### Path R1 / S1 — scoped and low-risk
Use when:
- small number of files
- obvious target area
- good test coverage already exists
- changes are mechanical or localized

Flow:
- anchor → plan-fast → specialist agent → review/test → fix → quick re-check

### Path R2 / S2 — medium complexity
Use when:
- multiple modules involved
- behavior-preservation risk is moderate
- stronger planning is needed

Flow:
- anchor → plan-deep → specialist agent → review/test → fix → quick re-check

### Path R3 / S3 — high-risk structural work
Use when:
- public APIs or system boundaries are involved
- changes span multiple major components
- partial work could destabilize the repo

Flow:
- deeper anchoring
- plan-deep
- stricter review/test gating
- likely ticket-driven only

## Validation rules

These commands should be stricter than generic feature execution about behavior preservation.

### Required review focus
- did behavior change unintentionally?
- were public contracts preserved?
- were assumptions about side effects safe?
- did simplification obscure intent?
- did refactoring accidentally widen scope?

### Required test focus
Run only the highest-signal checks available for the scoped area:
- direct unit/integration tests for touched modules
- relevant type checks / lint checks if already present
- no broad unrelated validation unless needed

### Close / pass gate
A successful run requires:
- no unresolved critical/major issues
- review does not indicate uncertain behavior preservation
- required relevant tests/checks pass

## Ticket integration

### Ticket-driven mode
If called with a ticket ID:
- use ticket context
- add notes via `tk add-note`
- update status via `tk status` or `tk close` when appropriate
- produce `.tf/tickets/<ticket-id>/close-summary.md`

### Non-ticket mode
If called without a ticket:
- do not mutate `tk`
- still write a run summary artifact under `.subagent-runs/...`
- optionally write reusable findings to `.tf/knowledge/...`

## Artifact expectations

### Shared artifacts
- `anchor-context.md`
- `plan.md`
- `implementation.md`
- `review.md`
- `test-results.md`
- `fixes.md`
- `review-post-fix.md`
- `close-summary.md`

### Optional durable knowledge
Only when genuinely reusable:
- `.tf/knowledge/topics/<topic-slug>/summary.md`
- `.tf/knowledge/topics/<topic-slug>/architecture-notes.md`

## Guardrails

### `/tf-refactor`
- never change intended behavior
- avoid changing public API unless explicitly requested or ticket-authorized
- prefer incremental structural improvements
- preserve existing style unless it harms clarity

### `/tf-simplify`
- never simplify into obscurity
- prefer clarity over clever terseness
- do not remove behavior under the guise of simplification
- avoid performance regressions in known hot paths unless explicitly accepted

## Why dedicated agents should remain

`refactorer` and `simplifier` should remain as shipped agents because they encode distinct execution intent:

### `refactorer`
- structure-oriented
- boundary-aware
- behavior-preserving reorganization

### `simplifier`
- complexity-oriented
- readability-oriented
- behavior-preserving reduction in mental load

Using the main agent alone would blur these roles and make outcomes less predictable.

## Recommendation

### Keep
- `refactorer`
- `simplifier`

### Add later
- `/tf-refactor`
- `/tf-simplify`

### Do not do
- do not expose the raw specialist agents as the primary user-facing workflow API
- do not collapse both tasks into generic `/tf-implement` behavior unless the ticket explicitly demands it

## Suggested implementation order

1. add `/tf-refactor` prompt
2. add `/tf-simplify` prompt
3. add README documentation for these commands only once implemented
4. reuse existing specialist agents rather than replacing them
