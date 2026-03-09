---
id: ptf-leyd
status: closed
deps: [ptf-wuvd]
links: []
created: 2026-03-06T06:55:48Z
type: feature
priority: 2
assignee: legout
parent: ptf-9c04
tags: [feature, vertical-slice, tk-loop, reliability]
---
# S4: Failure continuation and graceful shutdown

Implement no-retry failure semantics and graceful shutdown so failed tickets are recorded, processing continues, and SIGINT/SIGTERM cleanup removes runtime locks and markers.

## Design

PRD: ID-5, Out of Scope #2 (no auto retry), TD-4
Spec: 4.3 Signal Handling, 4.4 Failure Recording
Plan: Change 1, Tasks 8 and 10

## Acceptance Criteria

- [ ] Failed tickets are written to failed.jsonl with timestamp and error info.
- [ ] Failed tickets are not retried automatically in the same run.
- [ ] Loop continues to remaining ready tickets after failure.
- [ ] SIGINT and SIGTERM trigger cleanup of pid.lock and current-ticket.
- [ ] Shutdown path logs completion and exits cleanly.


## Notes

**2026-03-09T02:48:44Z**

## Verification Complete (2026-03-09)

All 5 acceptance criteria verified:

✅ AC1: Failed tickets written to failed.jsonl with timestamp and error info
- record_failure() appends valid JSONL: {"id":"...","ts":"...","error":"exit code N"}

✅ AC2: Failed tickets are not retried automatically
- No retry logic exists in the script
- Spec explicitly requires no auto-retry, implementation follows this

✅ AC3: Loop continues to remaining ready tickets after failure
- process_ticket returns exit code but loop continues
- Comment: "Continue to next ticket even on failure (no retry per PRD)"

✅ AC4: SIGINT and SIGTERM trigger cleanup
- trap cleanup INT TERM properly set
- cleanup() removes loop.pid and clears current-ticket

✅ AC5: Shutdown path logs completion and exits cleanly
- Logs "Loop shutdown complete" before exit
- Exits with code 0

Test file: tests/tk-loop/s4-failure-shutdown.md
