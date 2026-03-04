---
id: ptf-vln5
status: closed
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

- [x] Router runs immediately after fast anchoring for any interactive flag and constructs the nested command (including optional --clarify).
- [x] interactive_shell is invoked with the correct mode/background/handsFree settings for interactive, hands-free, and dispatch runs.
- [x] Environment sentinel prevents recursive /tk-implement invocations.
- [x] Legacy Path A/B/C execution is untouched when no interactive flag is set.
- [x] Interactive branches return control cleanly for downstream logging.


## Notes

**2026-03-04T13:47:57Z**

Implementation complete: Section 2 interactive router added to prompts/tk-implement.md with recursion guard, mode routing (interactive/hands-free/dispatch), nested command builder, and session metadata persistence. All 5 routing tests pass (B.1-B.5). Blocked by ptf-102j for session metadata finalization.

**2026-03-04T15:15:00Z**

Verification complete via /tk-implement. All 5 acceptance criteria verified:
- AC1: Router correctly positioned post-anchoring, nested command includes --clarify passthrough
- AC2: All 3 modes (interactive, hands-free, dispatch) correctly configured per interactive_shell API
- AC3: Recursion guard with PI_TK_INTERACTIVE_CHILD sentinel properly implemented
- AC4: Legacy Path A/B/C preserved and fall-through documented
- AC5: Session metadata schema and breadcrumbs documented for clean control return

Verification results written to tests/tk-implement/routing-verification.md.
Implementation is complete and verified. Session metadata write implementation remains blocked by ptf-102j.

**2026-03-04T14:12:48Z**

Implementation verified: All 5 acceptance criteria met. Section 2 router correctly implements recursion guard, mode routing, and session metadata schema. Session metadata write remains blocked by ptf-102j. See tests/tk-implement/routing-verification.md for verification results.
