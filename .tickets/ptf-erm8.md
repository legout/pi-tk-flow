---
id: ptf-erm8
status: closed
deps: [ptf-1q8n]
links: []
created: 2026-03-01T11:18:29Z
type: feature
priority: 2
assignee: legout
parent: ptf-21fw
tags: [extension, ui, launch, vertical-slice, tui]
---
# S4 Expose /tf ui terminal launch command

Add extensions/tf-ui.ts so /tf ui launches the Python TUI with robust runtime error messages.

## Design

Refs: PRD Extension Command; Spec C-1, E-1, E-2; Plan Task 6.

## Acceptance Criteria

- [ ] /tf ui command is registered and discoverable\n- [ ] /tf ui launches python -m pi_tk_flow_ui in valid environments\n- [ ] Missing Python or missing deps returns actionable guidance\n- [ ] Process lifecycle is handled cleanly on exit/failure


## Notes

**2026-03-04T14:23:47Z**

Verification complete: All 4 acceptance criteria met for /tf ui command.

✅ Command registration and discoverability
✅ Launches python -m pi_tk_flow_ui in valid environments
✅ Actionable guidance for missing Python/deps
✅ Clean process lifecycle handling

No code changes required - existing implementation verified correct.
Verification artifacts: .subagent-runs/ptf-erm8/2a37a754/implementation.md
