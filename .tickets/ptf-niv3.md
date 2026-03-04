---
id: ptf-niv3
status: closed
deps: []
links: []
created: 2026-03-04T11:02:46Z
type: feature
priority: 1
assignee: legout
parent: ptf-53pu
tags: [interactive, tk-implement, vertical-slice, ralph]
---
# Extend /tk-implement flag parsing for interactive modes

Teach the prompt to parse --interactive/--hands-free/--dispatch, enforce exclusivity with --async/--clarify, and keep existing defaults untouched.

## Design

PRD Solution table & US-5; Spec Architecture §1; Implementation Plan Task 1.

## Acceptance Criteria

- [ ] Parser recognizes the new flags and documents them in usage/help output.
- [ ] Invalid combos (multiple interactive flags, interactive+--async, --interactive+--clarify) emit actionable errors while --dispatch+--clarify stays valid.
- [ ] Unknown-flag rejection rules and default/--async flows work as before.
- [ ] Parser verification runs are appended to model-test-output.md.


## Notes

**2026-03-04T13:19:20Z**

Implementation complete:

- Added explicit help/usage message for unknown flags in prompts/tk-implement.md (lines 24-36)
- Created tests/tk-implement/model-test-output.md with verification runs for all 17 test cases:
  - A.1: Valid single flags (6 tests) - PASS
  - A.2: Invalid combinations (8 tests) - PASS  
  - A.3: Valid combinations (3 tests) - PASS
- Updated tests/tk-implement/flag-matrix.md checkboxes for A.1, A.2, A.3

All AC verified:
✅ Parser recognizes new flags with usage/help output
✅ Invalid combos emit actionable errors
✅ Unknown-flag rejection and default/--async flows work
✅ Verification runs documented in model-test-output.md

Commit: 6200856
