# Implementation Plan

## Goal
Add a Textual-based `/tf ui` experience (terminal + optional web serve mode) to pi-tk-flow by adapting the reference UI and replacing its data layer with `tickets.yaml` + topic scanning.

## Tasks
1. **Scaffold the Python UI package and runtime entrypoints**
   - File: `python/pyproject.toml`
   - File: `python/pi_tk_flow_ui/__init__.py`
   - File: `python/pi_tk_flow_ui/__main__.py`
   - Changes: Create a new Python package with optional `[ui]` dependencies (`textual`, `pyyaml`), Python version constraint, package metadata, and `python -m pi_tk_flow_ui` entrypoint that handles startup/errors cleanly.
   - Acceptance: `python -m pi_tk_flow_ui --help` returns usage; missing dependency path prints actionable install guidance (`pip install -e ./python[ui]`).
   - Rollback: Remove `python/` directory and any command wiring referencing `pi_tk_flow_ui`.

2. **Implement ticket loading from `.tf/plans/*/tickets.yaml`**
   - File: `python/pi_tk_flow_ui/ticket_loader.py`
   - Changes: Add `Ticket` model + `YamlTicketLoader` to parse all plans, map slice fields (`key`, `title`, `description`, `blocked_by`, etc.), include `plan_name/plan_dir`, and query `tk show <id> --format json` for status with fallback behavior.
   - Acceptance: Loader returns aggregated tickets across plans; malformed YAML is skipped with warning; missing `tk` status defaults safely to `open`.
   - Rollback: Keep parser-only mode (without `tk` status refresh) if CLI integration proves unstable.

3. **Port/implement dependency-aware board classification logic**
   - File: `python/pi_tk_flow_ui/board_classifier.py`
   - Changes: Implement `BoardColumn`, `ClassifiedTicket`, and `BoardClassifier` with closed/blocked/in-progress/ready rules and unresolved dependency detection.
   - Acceptance: Unit tests cover each column rule and dependency edge cases (unknown dep, closed dep, mixed dep states).
   - Rollback: Temporarily classify by status only (without dependency blocking) behind a small adapter if blocker logic regresses.

4. **Implement on-the-fly knowledge topic scanning**
   - File: `python/pi_tk_flow_ui/topic_scanner.py`
   - Changes: Scan `.tf/knowledge/topics/*.md`, extract title from first `#` heading, classify by filename prefix (`seed|plan|spike|baseline|other`), and return grouped topic metadata.
   - Acceptance: Scanner handles empty/missing topic directories gracefully and produces stable grouped output.
   - Rollback: Fall back to flat filename list display if metadata extraction fails.

5. **Adapt the reference Textual UI into app + styling modules**
   - File: `python/pi_tk_flow_ui/app.py`
   - File: `python/pi_tk_flow_ui/styles.tcss`
   - Changes: Port `TicketflowApp`, `TicketBoard`, `TopicBrowser`, keyboard bindings (`q/r/o/e/1-4`), filters (search/tag/assignee), detail panes, refresh flow, and external doc opening via suspend/resume.
   - Acceptance: Running `python -m pi_tk_flow_ui` shows both tabs, board columns populate, filters narrow tickets, `r` refreshes status, and doc-open shortcuts resolve plan docs.
   - Rollback: Disable failing hotkeys first (doc-open/editor actions) while keeping read-only board/topic browsing available.

6. **Add pi extension command for launch + web mode**
   - File: `extensions/tf-ui.ts`
   - File: `package.json` (only if extension registration requires explicit entry; otherwise no-op)
   - Changes: Register `/tf ui`, parse `--web` (and optional host/port passthrough if included), launch `python -m pi_tk_flow_ui` for terminal mode, and print/guide `textual serve` command for web mode.
   - Acceptance: `/tf ui` launches app in a TTY; `/tf ui --web` prints a runnable serve command and security note for non-local host binding.
   - Rollback: Remove `extensions/tf-ui.ts` to instantly disable the feature without touching existing tk workflow commands.

7. **Add automated tests + fixtures for the data layer**
   - File: `tests/fixtures/sample_project/.tf/plans/sample-plan/tickets.yaml`
   - File: `tests/fixtures/sample_project/.tf/knowledge/topics/*.md`
   - File: `tests/test_ticket_loader.py`
   - File: `tests/test_board_classifier.py`
   - File: `tests/test_topic_scanner.py`
   - Changes: Add deterministic fixtures and tests for YAML mapping, status query behavior (mocked subprocess), dependency classification, and topic parsing/grouping.
   - Acceptance: `pytest tests/test_ticket_loader.py tests/test_board_classifier.py tests/test_topic_scanner.py` passes locally.
   - Rollback: Keep parser/classifier tests only if subprocess mocking introduces flakiness.

8. **Document installation, usage, and conventions**
   - File: `README.md`
   - File: `.tf/knowledge/README.md`
   - Changes: Document optional UI install path, `/tf ui` and `/tf ui --web` usage, expected Python requirement, troubleshooting for missing deps, and topic naming conventions expected by scanner.
   - Acceptance: README contains copy-paste install/run snippets and troubleshooting section; knowledge README reflects `topics/*.md` grouping conventions used by UI.
   - Rollback: Remove/guard UI docs if feature is paused before release.

9. **Run end-to-end verification checklist before merge**
   - File: `.tf/plans/2026-02-28-add-tui-and-webui/04-progress.md` (or PR description checklist)
   - Changes: Record explicit pass/fail for launch, refresh, filtering, topic browsing, keybindings, web command output, and graceful handling of missing/corrupt inputs.
   - Acceptance: All PRD/spec success criteria are checked off with concrete evidence (command output/screenshots/log notes).
   - Rollback: If critical failures remain, disable extension command and ship without UI while keeping Python package in a feature branch.

## Files to Modify
- `extensions/tf-ui.ts` - new `/tf ui` command wiring
- `package.json` - optional extension registration adjustment (only if needed)
- `README.md` - UI install/usage/troubleshooting docs
- `.tf/knowledge/README.md` - topic naming/scanning conventions

## New Files (if any)
- `python/pyproject.toml` - Python package config + optional `[ui]` deps
- `python/pi_tk_flow_ui/__init__.py` - package metadata
- `python/pi_tk_flow_ui/__main__.py` - module entrypoint
- `python/pi_tk_flow_ui/app.py` - Textual app/widgets
- `python/pi_tk_flow_ui/styles.tcss` - TUI styling
- `python/pi_tk_flow_ui/ticket_loader.py` - YAML ticket ingestion + status refresh
- `python/pi_tk_flow_ui/board_classifier.py` - column classification logic
- `python/pi_tk_flow_ui/topic_scanner.py` - topic discovery/grouping
- `tests/fixtures/sample_project/.tf/plans/sample-plan/tickets.yaml` - fixture tickets
- `tests/fixtures/sample_project/.tf/knowledge/topics/seed-sample.md` - fixture topic
- `tests/test_ticket_loader.py` - loader tests
- `tests/test_board_classifier.py` - classifier tests
- `tests/test_topic_scanner.py` - topic scanner tests

## Dependencies
- Task 1 is prerequisite for Tasks 2–5.
- Task 2 must complete before Task 3 and Task 5.
- Task 4 must complete before Task 5 (topic tab wiring).
- Task 5 depends on Tasks 2–4 (all data contracts stable).
- Task 6 depends on Task 1 and Task 5 (launch target exists).
- Task 7 depends on Tasks 2–4 (testable logic finalized).
- Task 8 depends on Task 6 (final user command semantics).
- Task 9 depends on Tasks 5–8.

## Risks
- **Textual/runtime mismatch**: Pin versions in `pyproject.toml` and test in terminal + web serve contexts.
- **`tk` CLI status interface drift**: Isolate status query code and degrade gracefully to default `open`.
- **Performance with many tickets/plans**: Keep lazy body loading and avoid expensive per-render subprocess calls.
- **Command UX confusion (`/tf ui --web`)**: Provide explicit printed command + security note for host binding.

## Rollback Notes
- Primary rollback switch: remove/disable `extensions/tf-ui.ts` so core tk workflow remains unaffected.
- Secondary rollback: keep package skeleton but gate unstable features (status refresh, doc hotkeys) behind safe defaults.
- Full rollback: delete `python/pi_tk_flow_ui/` and revert docs, leaving existing `/tk-*` behavior unchanged.
