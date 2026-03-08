# Ticket Breakdown

## Parent Epic
- Title: External Ralph Wiggum Loop
- Ticket ID: ptf-9c04
- Goal: Deliver a safe external `tk-loop` that processes ready tickets sequentially via `/tk-implement`, supports all execution modes, and includes robust state/observability/test coverage.

## Proposed Slices
1. Script shell and safe startup contract
   - Slice: S1
   - Ticket ID: ptf-3nor
   - Type: AFK
   - Blocked by: none
   - Scope: Build `.tf/scripts/tk-loop.sh` scaffold with help/version output, mode parsing + mutex validation, recursion guard, and dependency checks.
   - Acceptance:
     - [ ] `--help` prints usage with all four modes and env vars.
     - [ ] Multiple mode flags fail with a clear validation error.
     - [ ] Unknown flags fail fast with non-zero exit.
     - [ ] `PI_TK_INTERACTIVE_CHILD=1` blocks nested invocation.
     - [ ] Missing `tk` or `pi` is detected before loop execution starts.
   - Source links:
     - PRD: US-4 Recursion Safety; US-5 Multiple Execution Modes; ID-3 Recursion Guard
     - Spec: 2.1 Core Script; 2.2 Flag Parser
     - Plan: Task 1; Task 2; Task 3; Task 4

2. Queue polling and sequential ticket dispatch
   - Slice: S2
   - Ticket ID: ptf-gg6c
   - Type: AFK
   - Blocked by: S1
   - Scope: Implement `tk ready` parsing, mode-aware command building, sequential processing, dry-run behavior, and clean queue-empty exit.
   - Acceptance:
     - [ ] Ticket IDs parse from first column of `tk ready` output.
     - [ ] Command builder emits correct `/tk-implement <ID> --<mode>` command.
     - [ ] Tickets process one-at-a-time in queue order.
     - [ ] `--dry-run` logs planned commands without invoking `pi`.
     - [ ] Empty queue exits status 0 with completion log.
   - Source links:
     - PRD: US-1 Batch Ticket Processing; US-2 Clarify Mode Integration; US-3 Clean Exit on Empty Queue
     - Spec: 2.3 Ticket Parser; 2.4 Command Builder; 3.1 Main Loop Flow
     - Plan: Task 5; Task 6; Task 8

3. State directory and structured observability
   - Slice: S3
   - Ticket ID: ptf-wuvd
   - Type: AFK
   - Blocked by: S2
   - Scope: Add normalized `.tk-loop-state/` management with PID locking, `current-ticket`, JSONL success/failure logs, structured loop log, and `metrics.json` updates.
   - Acceptance:
     - [ ] Startup initializes required state files (`pid.lock`, `current-ticket`, `processed.jsonl`, `failed.jsonl`, `loop.log`, `metrics.json`).
     - [ ] Active PID lock prevents concurrent runs; stale lock cleanup is safe.
     - [ ] `processed.jsonl` and `failed.jsonl` append valid JSONL records.
     - [ ] `metrics.json` remains valid JSON and updates processed/failed counters.
     - [ ] `loop.log` contains structured entries aligned with loop events.
   - Source links:
     - PRD: ID-4 State Management; US-1 logging acceptance
     - Spec: 2.5 State Manager; 5.1 Structured Logging; 5.2 Metrics
     - Plan: Task 7; Task 9; Change 4

4. Failure continuation and graceful shutdown
   - Slice: S4
   - Ticket ID: ptf-leyd
   - Type: AFK
   - Blocked by: S3
   - Scope: Implement no-retry failure semantics and signal-driven cleanup.
   - Acceptance:
     - [ ] Failed tickets are recorded in `failed.jsonl` with timestamp and error details.
     - [ ] Failed tickets are not automatically retried in-run.
     - [ ] Loop continues processing remaining tickets after a failure.
     - [ ] SIGINT/SIGTERM cleanup removes `pid.lock` and clears `current-ticket`.
     - [ ] Shutdown path logs completion and exits cleanly.
   - Source links:
     - PRD: ID-5 Error Handling; Out of Scope #2 (no automatic retry); TD-4 Failure Recovery
     - Spec: 4.3 Signal Handling; 4.4 Failure Recording
     - Plan: Change 1; Task 8; Task 10

5. End-to-end tests and mock infrastructure contract
   - Slice: S5
   - Ticket ID: ptf-ucgi
   - Type: AFK
   - Blocked by: S4
   - Scope: Deliver integration test harness plus deterministic `tk`/`pi` mocks and mock contract doc.
   - Acceptance:
     - [ ] `test-tk-loop.sh` executes all planned scenarios (empty/single/multi/failure/guard/mutex/schema/pid/signal).
     - [ ] Mock CLIs match the documented contract and env-var behavior.
     - [ ] Test harness exits non-zero when any scenario fails.
     - [ ] `MOCK_CONTRACT.md` defines preconditions, behavior rules, and post-conditions.
     - [ ] Test run is deterministic in local development.
   - Source links:
     - PRD: TD-1 through TD-6
     - Spec: 6.2 Integration Tests; 6.4 Mock Infrastructure; 6.5 Test Scenarios
     - Plan: Task 11; Task 11.5; Change 2; Change 3

6. Usage documentation and troubleshooting runbook
   - Slice: S6
   - Ticket ID: ptf-7vl1
   - Type: AFK
   - Blocked by: S5
   - Scope: Publish `.tf/scripts/README.md` with setup, mode usage, state-file semantics, troubleshooting, and test instructions.
   - Acceptance:
     - [ ] README includes copy/paste examples for clarify, hands-free, dispatch, and interactive.
     - [ ] Env vars and `.tk-loop-state/` schema are documented accurately.
     - [ ] Troubleshooting covers stale lock, recursion guard, and failed-ticket handling.
     - [ ] Testing section explains integration test execution.
     - [ ] Documentation matches final no-auto-retry behavior.
   - Source links:
     - PRD: US-5 Multiple Execution Modes; ID-4 State Management; Out of Scope
     - Spec: 7.2 Installation; 7.3 Configuration; 7.5 Rollback Plan
     - Plan: Task 12

## Dependency Graph
- S1 (ptf-3nor) -> S2 (ptf-gg6c)
- S2 (ptf-gg6c) -> S3 (ptf-wuvd)
- S3 (ptf-wuvd) -> S4 (ptf-leyd)
- S4 (ptf-leyd) -> S5 (ptf-ucgi)
- S5 (ptf-ucgi) -> S6 (ptf-7vl1)

## Review Questions
- Granularity right?
- Any slice to split/merge?
- Dependency corrections?
