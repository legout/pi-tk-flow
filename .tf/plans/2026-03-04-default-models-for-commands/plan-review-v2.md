# Plan Review

## Decision
- **Status:** NEEDS_REWORK
- **Ticketization:** NO-GO
- **Confidence:** High

## Scorecard (0-5)
- Requirement clarity: 3/5
- Architecture correctness: 3/5
- Task executability: 2/5
- Testing/verification quality: 2/5
- Rollout/operability readiness: 2/5
- **Overall:** 2.4/5

## Strengths
- Strong core approach: extension-based integration avoids risky TypeScript changes.
- Clear intent for graceful degradation when `pi-prompt-template-model` is not installed.
- Baseline command-to-model mapping is directionally sensible for cost vs quality tradeoffs.
- Rollback concept is simple (frontmatter/docs reversion).

## Findings
- **[Critical] GAP-001 remains unresolved: incomplete precedence ladder** (`02-spec.md` “Model Precedence” section; `00-design.md` key constraint).
  - Current docs do not provide a single explicit 5-level hierarchy that includes: subagent runtime `model` override, agent frontmatter `model`, main-loop prompt model, project defaults, and global defaults.
  - Result: ambiguous expected behavior in mixed main-loop + subagent scenarios.
- **[Critical] GAP-002 remains unresolved: `/tk-bootstrap` mapping missing** (`00-design.md` Component Contracts; `02-spec.md` Prompt Template Modifications; `03-implementation-plan.md` Task 2 file list).
  - Planning artifacts still cover only six prompt commands and do not explicitly include or exclude `/tk-bootstrap`.
  - Result: incomplete command-surface coverage and unclear rollout expectations.
- **[Major] Scope contradiction persists** (`01-prd.md` Out of Scope #3 vs `03-implementation-plan.md` Task 4).
  - PRD says agent-definition edits are out of scope; plan task proposes auditing/updating `assets/agents/*.md`.
  - Result: ticket authors cannot reliably split scope.
- **[Major] Validation protocol is still not ticket-ready** (`03-implementation-plan.md` Task 5).
  - Scenarios are listed, but concrete runnable commands, fixtures, and explicit pass/fail criteria are insufficiently specified for consistent execution.

## Required Changes Before GO (if any)
1. Add one canonical model-precedence ladder across artifacts (PRD + Spec + Knowledge guidance), explicitly covering main loop and subagent precedence levels.
2. Resolve `/tk-bootstrap` explicitly: add model mapping and verification steps, or mark out-of-scope with rationale and impact.
3. Reconcile scope conflict by aligning PRD Out-of-Scope with Implementation Plan Task 4 (remove Task 4 or move agent edits into scoped requirements).
4. Rewrite Task 5 as an executable validation checklist with exact commands, test inputs/fixtures, and objective pass/fail evidence.

## Suggested Improvements (non-blocking)
- Add a per-command `thinking` rationale table (why each level was chosen).
- Add operator-facing migration note for users who rely on manual `/model` switching.
- Add a short rollback runbook with git commands.

## Reconciliation with `plan-gaps.md`
- Decision is fully aligned with `plan-gaps.md`.
- **Critical gaps have not been addressed**: GAP-001 and GAP-002 are still present in current artifacts.
- Therefore ticketization remains **NO-GO** until required changes are applied.
