---
id: ptf-1q8n
status: closed
deps: [ptf-b8p5]
links: []
created: 2026-03-01T11:18:24Z
type: feature
priority: 1
assignee: legout
parent: ptf-21fw
tags: [ui, textual, kanban, vertical-slice, tui]
---
# S3 Ship terminal Kanban board core with refresh

Adapt TicketflowApp/TicketBoard to render Ready/Blocked/In Progress/Closed columns, ticket cards, and a detail pane in terminal mode.

## Design

Refs: PRD US-1; Spec C-2, C-3, D-1, D-2; Plan Task 5 (tickets tab).

## Acceptance Criteria

- [ ] python -m pi_tk_flow_ui renders Tickets tab with 4 columns\n- [ ] Tickets are grouped by classifier output and include plan context\n- [ ] Selecting a ticket updates detail pane content\n- [ ] r refreshes statuses and reclassifies the board\n- [ ] Empty-ticket state shows a clear message


## Notes

**2026-03-04T14:11:01Z**

Implementation completed:
- Added empty state handling in update_board() for all 4 columns (lines 406-412)
- Shows '[dim]No tickets[/dim]' when column is empty after filtering
- Verified 'r' refresh keybinding functional (Binding at line 575)
- All 58 tests pass
- Commit: f422741
