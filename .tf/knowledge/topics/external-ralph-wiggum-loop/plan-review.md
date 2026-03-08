# Plan Review

## Decision
- **Status:** APPROVED_WITH_CONDITIONS
- **Ticketization:** GO
- **Confidence:** Medium

## Scorecard (0-5)
- Requirement clarity: 3/5
- Architecture correctness: 3/5
- Task executability: 4/5
- Testing/verification quality: 3/5
- Rollout/operability readiness: 3/5
- **Overall:** 3.2/5

## Strengths
- Clear problem framing and user stories in `01-prd.md`.
- Implementation plan is sequenced and executable with explicit dependencies (`03-implementation-plan.md`).
- Core operational safeguards are present: recursion guard, PID lock, retries, graceful shutdown (`00-design.md`, `02-spec.md`).
- Rollback is low risk (no migrations/external irreversible changes).

## Findings
- **[Major] Requirement contradiction on retries** (`01-prd.md` Out of Scope #2 vs `02-spec.md` §4.2 and `03-implementation-plan.md` Task 9): PRD says no in-run retries, while spec/plan implement exponential retry. This must be resolved to avoid implementation drift.
- **[Major] Test plan is incomplete at integration level** (`03-implementation-plan.md` Task 11): no explicit end-to-end flow validation across parsing → command build → execution → state recording (aligns with `plan-gaps.md` GAP-001).
- **[Major] Mocking contract under-specified** (`03-implementation-plan.md` Task 11, `02-spec.md` §6.4): mock `tk`/`pi` location, PATH injection, and behavior controls are not concretely defined (aligns with `plan-gaps.md` GAP-002).
- **[Minor] Artifact path inconsistency** (`01-prd.md` ID-1/plan tasks use `.tf/scripts/tk-loop.sh`; `02-spec.md` §2.1/Appendix uses `scripts/tk-loop.sh`).
- **[Minor] State model inconsistency** (JSONL files in design/implementation plan vs JSON arrays and different filenames in spec §2.5/§4.4), increasing ambiguity for tests and observability tooling.
- **[Minor] Operational hardening gaps** (env var validation, exit code map, writable-state-dir checks, explicit `--version` verification) as captured in `plan-gaps.md` GAP-004..GAP-008.

## Required Changes Before GO (if any)
1. Resolve retry-policy conflict by updating either PRD out-of-scope or removing Task 9/Spec retry behavior; keep one authoritative rule.
2. Expand Task 11 with a mandatory end-to-end integration test scenario and pass criteria.
3. Specify mock infrastructure contract (directory, activation method, configurable responses) and include it in Task 11 deliverables.
4. Normalize script path + state-file schema across Design/PRD/Spec/Implementation Plan to a single canonical definition.

## Suggested Improvements (non-blocking)
- Add explicit exit code table and reference in help text.
- Add env var range validation (`TK_LOOP_POLL_INTERVAL`, `TK_LOOP_MAX_RETRIES`) and state-dir writability precheck.
- Document log growth handling (rotation or explicit limitation statement).
- Break Task 8 into subtasks for easier ticket sizing.

