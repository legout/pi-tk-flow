---
id: ptf-wvze
status: closed
deps: [ptf-1q8n, ptf-bv4b]
links: []
created: 2026-03-01T11:18:37Z
type: feature
priority: 2
assignee: legout
parent: ptf-21fw
tags: [ui, filters, keybindings, vertical-slice, tui]
---
# S6 Deliver filtering and keyboard productivity actions

Implement search/tag/assignee filtering and keyboard shortcuts (q/r/o/e/1-4) across ticket/topic workflows.

## Design

Refs: PRD US-3, US-4; Spec C-2, C-3, D-3, D-4, E-7; Plan Task 5.

## Acceptance Criteria

- [x] Search filters title/description with immediate updates
- [x] Tag and assignee filters apply and clear independently
- [x] q,r,o,e shortcuts behave as specified
- [x] 1-4 open expected plan docs for current context
- [x] Pager/editor failures are handled without crashing


## Notes

**2026-03-04T15:47:50Z**

Implementation completed:
- Fixed missing-file early check in TicketBoard._open_file() for error handling
- Improved action_open_in_editor() fallback with clear "No plan documents found" warning
- Fixed duplicate test method test_open_plan_doc_no_selection_shows_warning
- Strengthened weak assertion in test_tag_filter_is_case_insensitive
- Added test_no_plan_documents_shows_warning for fallback branch coverage

All 42 tests pass. Post-fix review confirmed no new issues.
Commit: b67f06f
