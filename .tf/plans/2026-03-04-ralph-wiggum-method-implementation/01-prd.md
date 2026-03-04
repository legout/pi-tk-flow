# PRD: Ralph Wiggum Method Implementation
**Feature**: Interactive/Background Execution Modes for `/tk-implement`
**Date**: 2026-03-04
**Status**: Draft

---

## Problem Statement
1. `/tk-implement` provides only foreground or fire-and-forget (`--async`) execution, so users lack real-time visibility or the ability to intervene mid-run.
2. There is no way to background an in-flight session and later reattach, forcing users to babysit long tickets or lose context entirely.
3. Session artifacts produced by interactive runs are inconsistent today, complicating downstream workflows (`tk-close`, audits).
4. Flag semantics have grown organically; without strict validation the new modes could collide with `--async`/`--clarify`, producing confusing errors.

## Solution
Introduce three mutually exclusive execution flags that route `/tk-implement` through pi's `interactive_shell`, while preserving the existing async + clarify behaviors:

| Flag | Mode | Key Behavior |
| --- | --- | --- |
| `--interactive` | Live supervised overlay | User watches progress, can transfer output (Ctrl+T), background (Ctrl+B), or detach menu (Ctrl+Q).
| `--hands-free` | Agent-monitored overlay | Agent polls every ~60s, user can take over by typing; good for semi-attended runs.
| `--dispatch` | Background + notification | Runs headless, auto notifies on completion, still allows `/attach` or `/sessions` follow-up.

All interactive modes still perform fast anchoring/context build before launching `interactive_shell`. If none of the new flags are set, `/tk-implement` continues to execute the existing Path A/B/C chains exactly as today.

## User Stories
- **US-1 Interactive Supervision**: As a developer, I want to watch `/tk-implement` in real time so I can intervene quickly. *Acceptance*: `--interactive` opens an overlay, exposes Ctrl+T/B/Q affordances, and logs the session ID in `.subagent-runs/<ticket>/`.
- **US-2 Hands-Free Monitoring**: As a developer, I want the agent to monitor progress and ping me when attention is needed. *Acceptance*: `--hands-free` sets `interactive_shell` mode to hands-free, enforces ~60s polling cadence, and allows user takeover input.
- **US-3 Dispatch Execution**: As a developer, I want to dispatch work to the background and be notified once complete. *Acceptance*: `--dispatch` launches `interactive_shell` in dispatch mode, backgrounds automatically, and writes completion output into the ticket's run directory.
- **US-4 Session Management**: As a developer, I need consistent commands to list and reattach sessions. *Acceptance*: Documentation teaches `/sessions` + `/attach <sessionId>`, and dispatch/hands-free runs emit the session ID + instructions in both console output and run logs.
- **US-5 Backward Compatibility**: As a developer, I expect default, `--async`, and `--clarify` flows to behave unchanged. *Acceptance*: No regression in Path A/B/C chain selection, artifacts stay in `.subagent-runs/<ticket>/`, and existing docs remain accurate aside from the new additions.

## Implementation Decisions
- **ID-1 Flag Parsing Matrix**: Update `prompts/tk-implement.md` to define `--interactive`, `--hands-free`, and `--dispatch` as mutually exclusive with each other and with `--async`. Disallow `--interactive`+`--clarify`, but continue to allow `--dispatch`+`--clarify` (clarify happens before dispatch).
- **ID-2 Interactive Branching**: After fast anchoring, short-circuit chain execution whenever an interactive flag is present and call `interactive_shell` with `command: pi "/tk-implement <ID> ..."`, passing `mode` + optional `background` (for dispatch) parameters.
- **ID-3 Artifact Alignment**: Ensure interactive sessions read/write the same `.subagent-runs/<ticket>/` paths as non-interactive runs so auditors and `tk-close` behave identically (PRD requirement ID-4).
- **ID-4 Documentation Updates**: Add usage sections to `.tf/plans/.../00-design.md`, `README.md`, and `skills/tk-workflow/SKILL.md` describing mode semantics, keybindings, `/attach`, `/sessions`, and compatibility rules. Chain definition files remain untouched per guardrails.
- **ID-5 Guardrail Compliance**: No modifications to agent definitions or new TUIs; rely solely on the existing `interactive_shell` tool surface.

## Testing Decisions
- **TD-1 Flag Validator Coverage**: Unit tests for every allowed/blocked combination (`--interactive` vs `--hands-free`, `--dispatch`+`--clarify`, invalid combos emitting explicit error text).
- **TD-2 Mode Behavior Smoke Tests**: Manual/integration runs verifying overlays, hands-free polling cadence, dispatch completion notifications, and that Ctrl+T/B/Q behave as documented.
- **TD-3 Session Lifecycle Testing**: Validate `/sessions`, `/attach`, Ctrl+B backgrounding, and Ctrl+Q detach flows using the new modes; ensure session IDs surface in logs.
- **TD-4 Regression Suite**: Re-run baseline `/tk-implement`, `--async`, and `--clarify` flows to confirm Path A/B/C chains, outputs, and artifact layouts remain identical.

## Out of Scope
1. Creating new agents or modifying agent definition files.
2. Building custom TUIs or replacing pi's overlay/keybinding system.
3. Deprecating `--async` or altering legacy flag semantics beyond validation.
4. Cross-ticket session sharing or collaborative multi-user control.
5. Alternative notification channels beyond pi's default dispatch notifications.
6. Persisting interactive sessions across process restarts beyond existing artifact logging.
