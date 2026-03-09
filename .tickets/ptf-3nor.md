---
id: ptf-3nor
status: closed
deps: []
links: []
created: 2026-03-06T06:55:48Z
type: feature
priority: 1
assignee: legout
parent: ptf-9c04
tags: [feature, vertical-slice, tk-loop, ralph]
---
# S1: Script shell and safe startup contract

Create the tk-loop script scaffold with help/version output, mode parsing, mutual-exclusion validation, recursion guard, and dependency checks before execution.

## Design

PRD: US-4, US-5, ID-3
Spec: 2.1 Core Script, 2.2 Flag Parser
Plan: Tasks 1-4

## Acceptance Criteria

- [ ] --help prints usage with all supported modes and env vars.
- [ ] Combining multiple mode flags fails with a clear error.
- [ ] Unknown flags return non-zero and actionable output.
- [ ] PI_TK_INTERACTIVE_CHILD=1 prevents nested loop invocation.
- [ ] Missing tk or pi binaries are detected before loop start.


## Notes

**2026-03-09T01:39:28Z**

Implementation complete:
- Created .tf/scripts/tk-loop.sh with Tasks 1-4 bootstrap
- AC1-5 all verified: --help, mode mutual-exclusion, unknown flag handling, recursion guard, dependency checks
- Post-fix: resolved minor issue with --help/--version startup log pollution
- Commit: c137efa
