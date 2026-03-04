# /tk-implement Flag Matrix Tests

Test suite for validating flag parsing, validation, and routing behavior in `/tk-implement`.

## A. Flag Combination Validation

### A.1 Valid Single Flags

| Test ID | Command | Expected | Status |
|---------|---------|----------|--------|
| A.1.1 | `/tk-implement TICKET-123` | Runs Path A/B/C (no interactive) | ✅ |
| A.1.2 | `/tk-implement TICKET-123 --interactive` | Interactive mode overlay | ✅ |
| A.1.3 | `/tk-implement TICKET-123 --hands-free` | Hands-free monitored overlay | ✅ |
| A.1.4 | `/tk-implement TICKET-123 --dispatch` | Dispatch background mode | ✅ |
| A.1.5 | `/tk-implement TICKET-123 --async` | Legacy async mode | ✅ |
| A.1.6 | `/tk-implement TICKET-123 --clarify` | Chain clarification TUI | ✅ |

### A.2 Invalid Flag Combinations (Should Error)

| Test ID | Command | Expected Error | Status |
|---------|---------|----------------|--------|
| A.2.1 | `/tk-implement TICKET-123 --interactive --hands-free` | "Cannot combine --interactive with --hands-free" | ✅ |
| A.2.2 | `/tk-implement TICKET-123 --interactive --dispatch` | "Cannot combine --interactive with --dispatch" | ✅ |
| A.2.3 | `/tk-implement TICKET-123 --hands-free --dispatch` | "Cannot combine --hands-free with --dispatch" | ✅ |
| A.2.4 | `/tk-implement TICKET-123 --interactive --async` | "Interactive modes cannot be used with --async" | ✅ |
| A.2.5 | `/tk-implement TICKET-123 --hands-free --async` | "Interactive modes cannot be used with --async" | ✅ |
| A.2.6 | `/tk-implement TICKET-123 --dispatch --async` | "Interactive modes cannot be used with --async" | ✅ |
| A.2.7 | `/tk-implement TICKET-123 --interactive --clarify` | "--interactive and --clarify are mutually exclusive" | ✅ |
| A.2.8 | `/tk-implement TICKET-123 --unknown-flag` | "Unknown flag: --unknown-flag" + help | ✅ |

### A.3 Valid Flag Combinations

| Test ID | Command | Expected Behavior | Status |
|---------|---------|-------------------|--------|
| A.3.1 | `/tk-implement TICKET-123 --hands-free --clarify` | Clarify TUI, then hands-free overlay | ✅ |
| A.3.2 | `/tk-implement TICKET-123 --dispatch --clarify` | Clarify TUI, then dispatch | ✅ |
| A.3.3 | `/tk-implement TICKET-123 --async --clarify` | Legacy: async wins, clarify=false | ✅ |

## B. Routing and Mode Behavior

### B.1 interactive_shell Parameters

| Test ID | Mode | Expected interactive_shell Call | Status |
|---------|------|--------------------------------|--------|
| B.1.1 | `--interactive` | `mode: "interactive"` | ⬜ |
| B.1.2 | `--hands-free` | `mode: "hands-free", handsFree: {updateMode: "on-quiet", ...}` | ⬜ |
| B.1.3 | `--dispatch` | `mode: "dispatch", background: true` | ⬜ |

### B.2 Nested Command Construction

| Test ID | Input Flags | Expected Inner Command | Status |
|---------|-------------|----------------------|--------|
| B.2.1 | `--interactive` | `pi "/tk-implement TICKET-123"` | ⬜ |
| B.2.2 | `--hands-free --clarify` | `pi "/tk-implement TICKET-123 --clarify"` | ⬜ |
| B.2.3 | `--dispatch --clarify` | `pi "/tk-implement TICKET-123 --clarify"` | ⬜ |

### B.3 Recursion Guard

| Test ID | Scenario | Expected | Status |
|---------|----------|----------|--------|
| B.3.1 | `PI_TK_INTERACTIVE_CHILD=1` set | Skip interactive routing, run Path A/B/C | ⬜ |

## C. Session Lifecycle and Artifacts

### C.1 Session Metadata Creation

| Test ID | Mode | Expected session.json | Status |
|---------|------|----------------------|--------|
| C.1.1 | `--interactive` | Created with mode="interactive" | ⬜ |
| C.1.2 | `--hands-free` | Created with mode="hands-free" | ⬜ |
| C.1.3 | `--dispatch` | Created with mode="dispatch" | ⬜ |
| C.1.4 | No interactive flags | **NO** session.json created | ⬜ |
| C.1.5 | Legacy `--async` | **NO** session.json created | ⬜ |

### C.2 Session Metadata Schema

```json
{
  "mode": "interactive|hands-free|dispatch",
  "sessionId": "string (e.g., calm-reef)",
  "startedAt": "ISO8601 timestamp",
  "command": "pi \"/tk-implement TICKET-123[ --clarify]\"",
  "status": "pending|completed|failed"
}
```

| Test ID | Field | Validation | Status |
|---------|-------|------------|--------|
| C.2.1 | `mode` | One of: interactive, hands-free, dispatch | ⬜ |
| C.2.2 | `sessionId` | Non-empty string | ⬜ |
| C.2.3 | `startedAt` | Valid ISO8601 timestamp | ⬜ |
| C.2.4 | `command` | Contains ticket ID | ⬜ |
| C.2.5 | `status` | Starts as "pending" | ⬜ |

### C.3 Breadcrumbs Output

| Test ID | Mode | Expected Console Output Contains | Status |
|---------|------|--------------------------------|--------|
| C.3.1 | All | "Session ID: <id>" | ⬜ |
| C.3.2 | All | "/attach <sessionId>" | ⬜ |
| C.3.3 | All | "/sessions" | ⬜ |
| C.3.4 | All | "Ctrl+T", "Ctrl+B", "Ctrl+Q" | ⬜ |

### C.4 Session Query Operations

| Test ID | Command | Expected | Status |
|---------|---------|----------|--------|
| C.4.1 | `/sessions` | Lists interactive sessions | ⬜ |
| C.4.2 | `/attach <sessionId>` | Reattaches to session | ⬜ |
| C.4.3 | `/dismiss <sessionId>` | Kills and cleans up | ⬜ |

## D. Regression Tests

### D.1 Legacy Behavior Preservation

| Test ID | Command | Expected (Unchanged) | Status |
|---------|---------|---------------------|--------|
| D.1.1 | `/tk-implement TICKET-123` | Runs Path A/B/C normally | ⬜ |
| D.1.2 | `/tk-implement TICKET-123 --async` | Background subagent execution | ⬜ |
| D.1.3 | `/tk-implement TICKET-123 --clarify` | Chain clarification TUI | ⬜ |
| D.1.4 | `/tk-implement TICKET-123 --async --clarify` | Async wins, clarify=false | ⬜ |

### D.2 Artifact Locations

| Test ID | Artifact | Expected Location | Status |
|---------|----------|------------------|--------|
| D.2.1 | anchor-context.md | `.subagent-runs/<ticket>/anchor-context.md` | ⬜ |
| D.2.2 | plan.md | `.subagent-runs/<ticket>/plan.md` | ⬜ |
| D.2.3 | implementation.md | `.subagent-runs/<ticket>/implementation.md` | ⬜ |
| D.2.4 | session.json | `.subagent-runs/<ticket>/session.json` (interactive only) | ⬜ |

### D.3 Path A/B/C Execution

| Test ID | Path | Expected Chain | Status |
|---------|------|---------------|--------|
| D.3.1 | A | worker→reviewer→fixer→reviewer→tk-closer | ⬜ |
| D.3.2 | B | planner→worker→(review+test)→fixer→(re-check)→closer | ⬜ |
| D.3.3 | C (no research) | planner→worker→(review+test)→fixer→(re-check)→closer | ⬜ |
| D.3.4 | C (with research) | (research)→planner→worker→(review+test)→fixer→(re-check)→closer | ⬜ |

## E. Error Handling

| Test ID | Scenario | Expected Behavior | Status |
|---------|----------|------------------|--------|
| E.1 | Missing ticket ID | "ERROR: ticket file not found" | ⬜ |
| E.2 | interactive_shell fails | Actionable error message, no partial session.json | ⬜ |
| E.3 | Invalid ticket ID | Clear error, suggest checking `.tickets/` | ⬜ |

## Test Execution Log

### Run 1: [Date]

```bash
# Example test execution
/tk-implement TEST-001 --interactive
# Result: [PASS/FAIL] - notes
```

| Test ID | Result | Notes |
|---------|--------|-------|
| | | |

### Run 2: [Date]

| Test ID | Result | Notes |
|---------|--------|-------|
| | | |

## Appendix: Quick Reference

### Flag Quick Reference

```
--interactive    Supervised overlay (blocking, no --clarify)
--hands-free     Agent-monitored overlay (polling, allows --clarify)
--dispatch       Headless background (notification, allows --clarify)
--async          Legacy background (no session tracking)
--clarify        Chain confirmation TUI
```

### Session Commands Quick Reference

```
/sessions                    List active sessions
/attach <sessionId>         Reattach to session
/attach                      Interactive selector
/dismiss <sessionId>        Kill specific session
/dismiss                     Kill all sessions
```

### Keybindings Quick Reference

```
Ctrl+T  Transfer output and close
Ctrl+B  Background (keep running)
Ctrl+Q  Detach menu
```
