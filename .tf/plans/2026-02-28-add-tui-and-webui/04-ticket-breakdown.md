# Ticket Breakdown

## Parent Epic
- Title: Add TUI and optional web UI for pi-tk-flow
- Goal: Deliver a Textual-based ticket management UI (terminal first, optional web serve mode) that works with pi-tk-flow’s YAML plans and knowledge topics, while keeping UI dependencies optional.

## Proposed Slices
1. S1 — Bootstrap optional UI runtime package
   - Type: AFK
   - Blocked by: none
   - Scope: Create the Python package skeleton and entrypoint for `pi_tk_flow_ui`, including optional `[ui]` dependencies and clear startup/install error guidance.
   - Acceptance:
     - [ ] `python/pyproject.toml` exists with `requires-python >=3.10` and optional `[ui]` dependencies (`textual`, `pyyaml`).
     - [ ] `python/pi_tk_flow_ui/__init__.py` and `__main__.py` exist and support `python -m pi_tk_flow_ui`.
     - [ ] Launch without UI dependencies shows actionable guidance (`pip install -e ./python[ui]`) instead of a traceback.
     - [ ] Core repo workflows still work without installing UI extras.
   - Source links:
     - PRD: US-6 Optional Installation, ID-6 Optional `[ui]` Extra
     - Spec: C-8 Package Configuration, E-1/E-2
     - Plan: Task 1

2. S2 — Build multi-plan ticket loading + status/classification backbone
   - Type: AFK
   - Blocked by: S1
   - Scope: Implement `YamlTicketLoader` and `BoardClassifier` so tickets from `.tf/plans/*/tickets.yaml` are normalized and classified into Ready/Blocked/In Progress/Closed using dependency-aware rules.
   - Acceptance:
     - [ ] Loader aggregates slices from all plan `tickets.yaml` files and maps YAML fields to ticket model fields.
     - [ ] Status lookup uses `tk show <id> --format json` with safe fallback to `open` on failures.
     - [ ] Malformed/missing YAML is skipped with warning logs; app remains functional.
     - [ ] Classifier puts tickets in CLOSED/BLOCKED/IN_PROGRESS/READY according to spec rules.
     - [ ] Blocking dependency calculation ignores unknown deps safely and handles mixed dependency states correctly.
   - Source links:
     - PRD: US-1 Visual Kanban, ID-2 YAML Ticket Loader, ID-4 tk CLI status source, ID-5 Multi-plan Aggregation
     - Spec: C-5 YamlTicketLoader, C-6 BoardClassifier, E-3/E-4/E-5
     - Plan: Tasks 2–3

3. S3 — Ship terminal Kanban board core (read-only with refresh)
   - Type: AFK
   - Blocked by: S2
   - Scope: Adapt `TicketflowApp`/`TicketBoard` to render four columns, ticket cards, and a detail panel in terminal mode with refresh wiring.
   - Acceptance:
     - [ ] Running `python -m pi_tk_flow_ui` renders a Tickets tab with 4 columns: Ready, Blocked, In Progress, Closed.
     - [ ] Cards are grouped by classifier output and show enough metadata to identify plan + ticket.
     - [ ] Selecting a card updates the detail panel with title, description, dependencies, and status.
     - [ ] Pressing `r` triggers status refresh and board reclassification.
     - [ ] Empty-state messaging is shown when no tickets exist.
   - Source links:
     - PRD: US-1 Visual Kanban
     - Spec: C-2 TicketflowApp, C-3 TicketBoard, D-1/D-2
     - Plan: Task 5 (tickets tab parts), Task 9 (launch/refresh verification)

4. S4 — Expose `/tf ui` terminal launch command in pi extension
   - Type: AFK
   - Blocked by: S3
   - Scope: Add `extensions/tf-ui.ts` command wiring so users can launch the TUI directly from pi and receive clear runtime error messages.
   - Acceptance:
     - [ ] `/tf ui` is registered and appears in extension command help.
     - [ ] `/tf ui` starts `python -m pi_tk_flow_ui` in terminal mode when environment is valid.
     - [ ] Missing Python or missing UI package/deps returns actionable guidance.
     - [ ] Process lifecycle is handled cleanly (exit/error propagated without hanging pi session).
   - Source links:
     - PRD: Solution > Extension Command
     - Spec: C-1 Extension Command, E-1/E-2
     - Plan: Task 6

5. S5 — Add knowledge topic browser tab with live scanning
   - Type: AFK
   - Blocked by: S3
   - Scope: Implement `TopicScanner` and Topic tab integration with grouped browsing (`seed|plan|spike|baseline|other`) and content detail rendering.
   - Acceptance:
     - [ ] `.tf/knowledge/topics/*.md` files are scanned on load without requiring `index.json`.
     - [ ] Topics are grouped by filename prefix with stable ordering.
     - [ ] Selecting a topic shows parsed content/title in the detail panel.
     - [ ] Missing/empty knowledge directory shows a non-crashing empty-state message.
   - Source links:
     - PRD: US-2 Knowledge Topic Browser, ID-3 Topic Scanner
     - Spec: C-4 TopicBrowser, C-7 TopicScanner, E-6, D-1
     - Plan: Task 4 + Task 5 (topics tab wiring)

6. S6 — Deliver filtering + keyboard productivity actions
   - Type: AFK
   - Blocked by: S3, S5
   - Scope: Implement search/tag/assignee filters and keyboard shortcuts (`q/r/o/e/1-4`) across board/topic workflows.
   - Acceptance:
     - [ ] Search filters tickets by title/description with immediate board updates.
     - [ ] Tag and assignee filters can be applied and cleared independently.
     - [ ] `q` quits, `r` refreshes, `e` opens in editor, and `o` opens primary doc/topic in pager.
     - [ ] `1-4` open expected plan docs for current ticket context with suspend/resume behavior.
     - [ ] Editor/pager failures show actionable errors instead of crashing.
   - Source links:
     - PRD: US-3 Ticket Filtering, US-4 Quick Actions
     - Spec: C-2 key bindings, C-3 filters, D-3/D-4, E-7
     - Plan: Task 5

7. S7 — Add web mode entry and user-facing docs
   - Type: AFK
   - Blocked by: S4
   - Scope: Support `/tf ui --web` command output and document install/run/troubleshooting conventions (including host-binding safety note).
   - Acceptance:
     - [ ] `/tf ui --web` prints a runnable `textual serve "python -m pi_tk_flow_ui"` command.
     - [ ] Output includes a security note for non-local host binding.
     - [ ] `README.md` includes copy-paste install and run instructions for terminal + web usage.
     - [ ] `.tf/knowledge/README.md` documents topic naming conventions expected by scanner.
   - Source links:
     - PRD: US-5 Web Access, US-6 Optional Installation
     - Spec: C-1 web behavior, roll-out/success criteria
     - Plan: Tasks 6 and 8

8. S8 — Lock in quality gates with fixtures, tests, and verification log
   - Type: AFK
   - Blocked by: S2, S5, S6, S7
   - Scope: Add deterministic fixtures and tests for loader/scanner/classifier plus a concrete end-to-end verification checklist record.
   - Acceptance:
     - [ ] Fixtures exist for sample plan tickets and sample topic markdown files.
     - [ ] Unit tests cover YAML mapping/status fallback, dependency classification, and topic parsing/grouping.
     - [ ] `pytest tests/test_ticket_loader.py tests/test_board_classifier.py tests/test_topic_scanner.py` passes locally.
     - [ ] Plan progress/PR checklist records pass/fail evidence for launch, refresh, filters, topic browsing, keybindings, and web command output.
   - Source links:
     - PRD: TD-1/TD-2/TD-3 Testing Decisions, Success Metrics
     - Spec: T-1/T-2/T-3/T-4, R-4 Success Criteria
     - Plan: Tasks 7 and 9

## Dependency Graph
- S1 -> S2
- S2 -> S3
- S3 -> S4
- S3 -> S5
- S3 -> S6
- S5 -> S6
- S4 -> S7
- S2 -> S8
- S5 -> S8
- S6 -> S8
- S7 -> S8

## Review Questions
- Granularity right?
- Any slice to split/merge?
- Dependency corrections?
