---
id: ptf-21fw
status: closed
deps: []
links: []
created: 2026-03-01T11:18:09Z
type: epic
priority: 1
assignee: legout
tags: [planning, ui, tui]
---
# Add TUI and optional web UI for pi-tk-flow

Deliver a Textual-based terminal UI with optional web mode for pi-tk-flow, backed by YAML plan tickets and knowledge topics, while keeping UI dependencies optional.

## Design

Source docs: .tf/plans/2026-02-28-add-tui-and-webui/{01-prd.md,02-spec.md,03-implementation-plan.md}.

## Acceptance Criteria

- [ ] /tf ui launches terminal UI\n- [ ] /tf ui --web provides web serve path\n- [ ] Ticket board and topic browser are both available\n- [ ] Optional dependency install path documented


## Notes

**2026-03-04T12:48:06Z**

Implementation complete. 8 slices delivered: Python package, data layer, TUI app, extension, topic browser, filters/actions, web mode, tests. All 47 tests pass.

Key files:
- python/pi_tk_flow_ui/ - Textual TUI package with TicketBoard, TopicBrowser
- extensions/tf-ui.ts - /tf ui command registration
- tests/ - 47 unit tests (loader, classifier, scanner)

Commit: d22a548
