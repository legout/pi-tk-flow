---
id: ptf-wvze
status: open
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

- [ ] Search filters title/description with immediate updates\n- [ ] Tag and assignee filters apply and clear independently\n- [ ] q,r,o,e shortcuts behave as specified\n- [ ] 1-4 open expected plan docs for current context\n- [ ] Pager/editor failures are handled without crashing

