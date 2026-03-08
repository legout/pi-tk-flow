---
id: ptf-leyd
status: open
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

