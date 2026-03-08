---
id: ptf-wuvd
status: open
deps: [ptf-gg6c]
links: []
created: 2026-03-06T06:55:48Z
type: feature
priority: 2
assignee: legout
parent: ptf-9c04
tags: [feature, vertical-slice, tk-loop, observability]
---
# S3: State directory and structured observability

Add normalized state and observability: PID lock management, current-ticket marker, JSONL success/failure logs, structured loop logs, and metrics.json updates.

## Design

PRD: ID-4, US-1 logging acceptance
Spec: 2.5 State Manager, 5.1 Structured Logging, 5.2 Metrics
Plan: Task 7, Task 9, Change 4

## Acceptance Criteria

- [ ] .tk-loop-state is initialized with required files.
- [ ] Active PID lock blocks concurrent loops; stale locks are handled safely.
- [ ] processed.jsonl and failed.jsonl append valid JSONL records.
- [ ] metrics.json stays valid JSON and updates counters on each ticket.
- [ ] loop.log captures structured entries aligned with console events.

