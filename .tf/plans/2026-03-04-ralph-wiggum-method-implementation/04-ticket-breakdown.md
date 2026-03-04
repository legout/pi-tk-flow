# Ticket Breakdown

## Parent Epic
- Title: Interactive execution modes for `/tk-implement`
- Goal: Provide supervised, hands-free, and dispatch execution options that preserve legacy flows while recording session breadcrumbs and documenting the new flag matrix.

## Proposed Slices
1. Extend `/tk-implement` flag parsing for interactive modes
   - Type: AFK
   - Blocked by: none
   - Scope: Add `--interactive`, `--hands-free`, `--dispatch` parsing, enforce exclusivity with `--async`/`--clarify`, and update usage/help text plus parser tests.
   - Acceptance:
     - [ ] Parser recognizes the three new flags and surfaces them in usage/help text alongside existing options.
     - [ ] Mutually exclusive combinations (multiple interactive flags, any interactive flag with `--async`, and `--interactive + --clarify`) are rejected with actionable errors, while `--dispatch + --clarify` remains valid.
     - [ ] Unknown-flag rejection logic stays intact and default/`--async` flows parse exactly as before.
     - [ ] Parser verification runs (valid + invalid examples) are captured in `model-test-output.md`.
   - Source links:
     - PRD: Solution – Execution Modes table & User Story US-5
     - Spec: Architecture §1 "Entry Point"
     - Plan: Task 1 "Extend `/tk-implement` flag parsing and validation"

2. Route interactive modes through `interactive_shell` after fast anchoring
   - Type: AFK
   - Blocked by: S1
   - Scope: Introduce a post-anchoring router that builds the nested `pi "/tk-implement …"` command, invokes `interactive_shell` per mode, configures hands-free polling, and guards recursion before falling back to Path A/B/C.
   - Acceptance:
     - [ ] Routing block executes immediately after fast anchoring whenever an interactive flag is present, constructing the nested command with ticket ID and optional `--clarify`.
     - [ ] `interactive_shell` is called with the correct `mode`/`background`/`handsFree` options for interactive, hands-free, and dispatch flows.
     - [ ] Environment sentinel prevents recursive `/tk-implement` invocation loops.
     - [ ] When no interactive flag is set, the legacy Path A/B/C chain selection is unchanged (verified by smoke run).
     - [ ] Each interactive invocation returns control cleanly to subsequent prompt steps for logging.
   - Source links:
     - PRD: Solution – Mode behaviors & User Stories US-1..US-3
     - Spec: Architecture §2–3 "Fast Anchoring" & "Execution Router"
     - Plan: Task 2 "Add interactive execution router after fast anchoring"

3. Persist interactive session metadata and console breadcrumbs
   - Type: AFK
   - Blocked by: S2
   - Scope: Write `.subagent-runs/<ticket>/session.json` with `{mode, sessionId, startedAt, command, status}`, emit `/sessions` + `/attach` guidance, and handle failures without leaving partial files.
   - Acceptance:
     - [ ] Successful interactive, hands-free, and dispatch runs create `session.json` containing mode, sessionId, timestamps, command, and status fields under the ticket’s run directory.
     - [ ] Console/log output includes a standardized block with session ID, `/sessions` + `/attach <sessionId>` instructions, and Ctrl+T/B/Q keybinding reminders.
     - [ ] Failure paths clean up partial session files and surface remediation guidance without impacting legacy modes.
     - [ ] Legacy (non-interactive) executions do not create session artifacts or alter existing run logs.
   - Source links:
     - PRD: User Story US-4 "Session Management" & Problem Statement #3
     - Spec: Architecture §4 "Session Metadata Logging" & Observability section
     - Plan: Task 3 "Persist interactive session metadata and user breadcrumbs"

4. Document execution modes in `README.md` and `skills/tk-workflow/SKILL.md`
   - Type: AFK
   - Blocked by: S3
   - Scope: Add an Execution Modes section, compatibility matrix, keybinding instructions, `/sessions` & `/attach` guidance, and updated usage examples across both docs.
   - Acceptance:
     - [ ] README contains a dedicated Execution Modes section with flag descriptions, compatibility rules vs `--async`/`--clarify`, and overlay keybinding reminders.
     - [ ] README documents how session artifacts (`session.json`) and `/sessions`/`/attach` commands work for each mode.
     - [ ] `skills/tk-workflow/SKILL.md` teaches when to choose interactive vs hands-free vs dispatch vs async, including troubleshooting tips.
     - [ ] Updated examples include `--hands-free` and `--dispatch`, mirroring the implemented behaviors.
   - Source links:
     - PRD: Solution & User Stories US-1..US-4
     - Spec: Architecture §5 "Documentation Surfaces"
     - Plan: Task 4 "Document the new execution modes"

5. Capture flag matrix tests and logged evidence
   - Type: AFK
   - Blocked by: S4
   - Scope: Create `tests/tk-implement/flag-matrix.md`, cover TD-1..TD-4 scenarios, and append execution evidence to `model-test-output.md`.
   - Acceptance:
     - [ ] `tests/tk-implement/flag-matrix.md` enumerates valid/invalid flag combos, mode behaviors, session lifecycle checks, and regression steps for legacy async/clarify flows.
     - [ ] Each scenario lists concrete commands plus expected outcomes (accept/reject, overlay behavior, session file presence).
     - [ ] `model-test-output.md` is appended with timestamps or summaries showing the checklist was executed.
     - [ ] Checklist explicitly covers session cleanup and confirms `.subagent-runs/<ticket>/session.json` contents.
   - Source links:
     - PRD: Testing Decisions TD-1..TD-4
     - Spec: Testing Strategy §1–4
     - Plan: Task 5 "Capture test coverage for the flag matrix and session flows"

## Dependency Graph
- S1 → S2 → S3 → S4 → S5

## Review Questions
- Are the routing (S2) and session logging (S3) scopes sufficiently separated, or should any telemetry work move earlier?
- Do documentation updates (S4) need additional reviewers/approvals that could affect scheduling?
- Does the test slice (S5) require automation beyond the documented checklist, and if so should it be split out?
