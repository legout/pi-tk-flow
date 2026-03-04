# Implementation Plan

## Goal
Add interactive, hands-free, and dispatch execution modes to `/tk-implement` while preserving legacy flows, persisting session metadata, and documenting/testing the new flag matrix.

## Tasks
1. **Extend `/tk-implement` flag parsing and validation**
   - File: `prompts/tk-implement.md`
   - Changes: Add `--interactive`, `--hands-free`, and `--dispatch` to the supported flag list; codify mutual exclusivity with one another and `--async`; explicitly block `--interactive + --clarify` while allowing `--dispatch + --clarify`; surface precise error/help text and usage examples; keep unknown-flag rejection logic intact.
   - Verification: Run `/tk-implement TEST-123 --interactive`, `--hands-free`, `--dispatch`, and invalid mixes (`--interactive --dispatch`, `--interactive --clarify`) to confirm the parser accepts/ rejects as expected; ensure default/`--async` invocations still parse; capture outputs in `model-test-output.md`.
   - Rollback: Revert the parsing section of `prompts/tk-implement.md` to the previous commit and remove any new help text references.

2. **Add interactive execution router after fast anchoring**
   - File: `prompts/tk-implement.md`
   - Changes: Insert a routing block immediately after fast anchoring that (a) builds the nested `pi "/tk-implement <ticket> [--clarify]"` command, (b) calls `interactive_shell` with `mode` set per flag (`interactive`, `hands-free`, `dispatch` + `background: true`), (c) configures hands-free polling (`updateMode`, `updateInterval`, `quietThreshold`), (d) guards against recursive invocation via an env sentinel, and (e) falls through to the existing Path A/B/C chain logic when no interactive flag is present.
   - Verification: Trigger each mode on a sample ticket and confirm overlays open with the expected behavior (hands-free emits periodic updates, dispatch backgrounds and returns immediately); confirm legacy runs still launch Path A/B/C chains.
   - Rollback: Delete the new routing block and env sentinel instructions, restoring the direct jump from anchoring to chain selection.

3. **Persist interactive session metadata and user breadcrumbs**
   - File: `prompts/tk-implement.md`
   - Changes: After a successful `interactive_shell` call, write `.subagent-runs/<ticket>/session.json` with `{mode, sessionId, startedAt, command, status}`; append a short console/log block describing `/sessions`, `/attach <sessionId>`, and keybindings; add failure handling so partially created files are cleaned up and the user sees remediation guidance.
   - Verification: Run `--interactive` and `--dispatch` modes, then inspect `.subagent-runs/<ticket>/session.json` and the run log to ensure the metadata and instructions exist; simulate an `interactive_shell` failure (e.g., invalid command) to confirm graceful messaging.
   - Rollback: Remove the session logging snippets and delete any new helper text inserted into the prompt.

4. **Document the new execution modes**
   - Files: `README.md`, `skills/tk-workflow/SKILL.md`
   - Changes: Add a dedicated “Execution Modes” section describing each flag, compatibility rules, keyboard shortcuts (Ctrl+T/B/Q), `/sessions`, `/attach`, and contrasts vs `--async`; update existing examples to include `--hands-free` and `--dispatch`; ensure troubleshooting tips cover overlay controls.
   - Verification: Render or preview the markdown to ensure tables and code blocks format correctly; cross-check that every rule mentioned in the prompt is reflected in both docs.
   - Rollback: Revert doc sections and remove added tables/examples.

5. **Capture test coverage for the flag matrix and session flows**
   - Files: `tests/tk-implement/flag-matrix.md` (new), `model-test-output.md`
   - Changes: Create a test checklist detailing TD-1..TD-4 scenarios (valid/invalid combos, mode behaviors, session lifecycle, regressions); include command snippets and expected outcomes; log execution evidence in `model-test-output.md` once tests run.
   - Verification: Walk through the checklist after implementation, confirming each scenario passes and is recorded.
   - Rollback: Delete the new test checklist file and remove related log entries if this feature is backed out.

## Files to Modify
- `prompts/tk-implement.md` – add flag parsing, routing, session logging, and error handling instructions.
- `README.md` – document execution modes, shortcuts, and compatibility matrix.
- `skills/tk-workflow/SKILL.md` – teach tk practitioners how/when to use the new modes.
- `model-test-output.md` – append evidence that the new tests/checklists were executed.

## New Files (if any)
- `tests/tk-implement/flag-matrix.md` – detailed checklist covering flag validation, interactive mode behaviors, session management, and regression steps.

## Dependencies
- Task 2 depends on Task 1 (router needs parsed flags).
- Task 3 depends on Task 2 (session logging requires router outputs and `sessionId`).
- Task 4 depends on Tasks 1–3 so documentation matches the implemented behavior.
- Task 5 depends on Tasks 1–4, because tests/checklists must reflect the final UX and docs.

## Risks
- **Recursive invocation loops**: Mitigate by setting/ checking an env sentinel before launching `interactive_shell`.
- **Session artifact drift**: Centralize `.subagent-runs/<ticket>/session.json` writes and reuse existing run directories to avoid breaking `tk-close`.
- **User confusion between `--async` and new modes**: Use explicit docs + console breadcrumbs that compare behaviors and keyboard shortcuts.
- **Unverified flag matrix**: Require the new checklist to be run and logged; failing cases should block release until resolved.
