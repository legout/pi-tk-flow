---
id: ptf-vln5
status: open
deps: [ptf-niv3]
links: []
created: 2026-03-04T11:02:50Z
type: feature
priority: 1
assignee: legout
parent: ptf-53pu
tags: [interactive, tk-implement, vertical-slice, ralph]
---
# Route interactive modes through interactive_shell after fast anchoring

Add a post-anchoring router that builds the nested pi "/tk-implement …" command, invokes interactive_shell per mode, and guards recursion before falling through to Path A/B/C.

## Design

PRD US-1..US-3; Spec Architecture §§2-3; Implementation Plan Task 2.

## Acceptance Criteria

- [ ] Router runs immediately after fast anchoring for any interactive flag and constructs the nested command (including optional --clarify).
- [ ] interactive_shell is invoked with the correct mode/background/handsFree settings for interactive, hands-free, and dispatch runs.
- [ ] Environment sentinel prevents recursive /tk-implement invocations.
- [ ] Legacy Path A/B/C execution is untouched when no interactive flag is set.
- [ ] Interactive branches return control cleanly for downstream logging.

