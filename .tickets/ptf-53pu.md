---
id: ptf-53pu
status: closed
deps: []
links: []
created: 2026-03-04T11:02:41Z
type: epic
priority: 1
assignee: legout
tags: [planning, tk-implement, interactive, ralph]
---
# Interactive execution modes for /tk-implement

Add supervised, hands-free, and dispatch execution paths to /tk-implement while keeping legacy async/clarify flows stable and ensuring artifacts land under the usual .subagent-runs/<ticket>/ directories.

## Design

PRD Solution & User Stories; Spec Architecture + Testing Strategy; Implementation Plan Tasks 1-5.

## Acceptance Criteria

- [ ] Interactive, hands-free, and dispatch flags route through fast anchoring without breaking Path A/B/C.
- [ ] Interactive runs persist session metadata and console breadcrumbs for /sessions and /attach.
- [ ] README + tk-workflow skill document the new modes and troubleshooting tips.
- [ ] Flag matrix checklist + model-test-output entries cover valid/invalid combos and session lifecycle.


## Notes

**2026-03-04T12:46:52Z**

Implementation complete: interactive, hands-free, dispatch modes added

Summary:
- Added 3 new flags: --interactive, --hands-free, --dispatch
- Flag validation matrix with proper error messages
- Interactive router with recursion guard (PI_TK_INTERACTIVE_CHILD)
- Session metadata persistence (.subagent-runs/<ticket>/session.json)
- Full documentation: README Execution Modes, skills/tk-workflow/SKILL.md

Files changed:
- prompts/tk-implement.md
- README.md
- skills/tk-workflow/SKILL.md
- tests/tk-implement/flag-matrix.md (new)

Tests: 15/15 passed
Commit: 3c2b9d7
