---
id: ptf-ucgi
status: open
deps: [ptf-leyd]
links: []
created: 2026-03-06T06:55:48Z
type: task
priority: 2
assignee: legout
parent: ptf-9c04
tags: [task, vertical-slice, tk-loop, testing]
---
# S5: End-to-end tests and mock infrastructure contract

Deliver an end-to-end integration test suite with deterministic tk/pi mocks and a documented mock contract covering expected interfaces, environment variables, and assertions.

## Design

PRD: TD-1 through TD-6
Spec: 6.2 Integration Tests, 6.4 Mock Infrastructure, 6.5 Test Scenarios
Plan: Tasks 11 and 11.5, Changes 2 and 3

## Acceptance Criteria

- [ ] test-tk-loop.sh runs all planned scenarios (empty/single/multi/failure/guard/mutex/schema/pid/signal).
- [ ] Mock tk and pi binaries satisfy the documented behavior contract.
- [ ] Test harness exits non-zero when any scenario fails.
- [ ] MOCK_CONTRACT.md defines preconditions, behaviors, and post-conditions.
- [ ] Test execution is deterministic in local development.

