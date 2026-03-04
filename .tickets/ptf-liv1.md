---
id: ptf-liv1
status: open
deps: [ptf-b8p5, ptf-bv4b, ptf-wvze, ptf-n5ir]
links: []
created: 2026-03-01T11:18:45Z
type: task
priority: 3
assignee: legout
parent: ptf-21fw
tags: [tests, qa, ui, vertical-slice, tui]
---
# S8 Add fixtures, tests, and end-to-end verification log

Add deterministic fixtures and tests for loader/scanner/classifier, then record E2E verification evidence for the UI workflows.

## Design

Refs: PRD TD-1/TD-2/TD-3 and success metrics; Spec T-1/T-2/T-3/T-4, R-4; Plan Tasks 7 and 9.

## Acceptance Criteria

- [ ] Fixture project includes representative tickets.yaml and topic markdown\n- [ ] Unit tests cover YAML mapping/status fallback, dependency classification, topic parsing/grouping\n- [ ] pytest tests/test_ticket_loader.py tests/test_board_classifier.py tests/test_topic_scanner.py passes\n- [ ] Progress/PR checklist captures pass/fail evidence for core UI scenarios

