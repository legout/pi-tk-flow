# /tk-implement Test Checklist

Test suite validating flag parsing, mode routing, session lifecycle, and legacy behavior for `/tk-implement`.

**Test Design Reference:** PRD Testing Decisions TD-1..TD-4  
**Spec Reference:** Implementation Plan Testing Strategy

---

## TD-1: Flag Validator Coverage

> **Purpose:** Unit/integration tests for every allowed/blocked flag combination per PRD ID-1.

### TD-1.1 Valid Single Flags

| Test ID | Command | Expected | Status |
|---------|---------|----------|--------|
| TD-1.1.1 | `/tk-implement TICKET-123` | Runs Path A/B/C (no interactive), no session.json created | ✅ |
| TD-1.1.2 | `/tk-implement TICKET-123 --interactive` | Interactive mode overlay with mode="interactive" | ✅ |
| TD-1.1.3 | `/tk-implement TICKET-123 --hands-free` | Hands-free monitored overlay with mode="hands-free" | ✅ |
| TD-1.1.4 | `/tk-implement TICKET-123 --dispatch` | Dispatch background mode with mode="dispatch" | ✅ |
| TD-1.1.5 | `/tk-implement TICKET-123 --async` | Legacy async mode (async: true, no session tracking) | ✅ |
| TD-1.1.6 | `/tk-implement TICKET-123 --clarify` | Chain clarification TUI opens | ✅ |

### TD-1.2 Invalid Flag Combinations (Mutual Exclusivity)

| Test ID | Command | Expected Error | Status |
|---------|---------|----------------|--------|
| TD-1.2.1 | `/tk-implement TICKET-123 --interactive --hands-free` | "Cannot combine --interactive with --hands-free" | ✅ |
| TD-1.2.2 | `/tk-implement TICKET-123 --interactive --dispatch` | "Cannot combine --interactive with --dispatch" | ✅ |
| TD-1.2.3 | `/tk-implement TICKET-123 --hands-free --dispatch` | "Cannot combine --hands-free with --dispatch" | ✅ |
| TD-1.2.4 | `/tk-implement TICKET-123 --interactive --async` | "Interactive modes cannot be used with --async" | ✅ |
| TD-1.2.5 | `/tk-implement TICKET-123 --hands-free --async` | "Interactive modes cannot be used with --async" | ✅ |
| TD-1.2.6 | `/tk-implement TICKET-123 --dispatch --async` | "Interactive modes cannot be used with --async" | ✅ |
| TD-1.2.7 | `/tk-implement TICKET-123 --interactive --clarify` | "--interactive and --clarify are mutually exclusive (overlay conflict)" | ✅ |
| TD-1.2.8 | `/tk-implement TICKET-123 --unknown-flag` | "Unknown flag: --unknown-flag" + help text | ✅ |

### TD-1.3 Valid Flag Combinations

| Test ID | Command | Expected Behavior | Status |
|---------|---------|-------------------|--------|
| TD-1.3.1 | `/tk-implement TICKET-123 --hands-free --clarify` | Clarify TUI runs first, then hands-free overlay | ✅ |
| TD-1.3.2 | `/tk-implement TICKET-123 --dispatch --clarify` | Clarify TUI runs first, then dispatch proceeds | ✅ |
| TD-1.3.3 | `/tk-implement TICKET-123 --async --clarify` | Legacy: async wins, clarify=false (silently ignored) | ✅ |

### TD-1.4 Validation Order Verification

| Test ID | Validation Step | Expected Order | Status |
|---------|-----------------|----------------|--------|
| TD-1.4.1 | Unknown flags checked first | Error before mutual exclusivity check | ✅ |
| TD-1.4.2 | Interactive flags mutually exclusive | --interactive vs --hands-free vs --dispatch | ✅ |
| TD-1.4.3 | Interactive flags vs --async | Blocked after mutual exclusivity | ✅ |
| TD-1.4.4 | --interactive vs --clarify | Blocked after async check | ✅ |
| TD-1.4.5 | Legacy rule applied last | --async wins over --clarify | ✅ |

---

## TD-2: Mode Behavior Smoke Tests

> **Purpose:** Manual/integration runs verifying overlays, hands-free polling cadence, dispatch completion notifications, and Ctrl+T/B/Q behaviors per PRD ID-2, ID-4.

### TD-2.1 interactive_shell Parameter Construction

| Test ID | Mode | Expected interactive_shell Parameters | Status |
|---------|------|--------------------------------------|--------|
| TD-2.1.1 | `--interactive` | `mode: "interactive"`, command nested without interactive flags | ✅ |
| TD-2.1.2 | `--hands-free` | `mode: "hands-free"`, `handsFree: {updateMode: "on-quiet", quietThreshold: 8000, updateInterval: 60000, autoExitOnQuiet: false}` | ✅ |
| TD-2.1.3 | `--dispatch` | `mode: "dispatch"`, `background: true`, `autoExitOnQuiet: true` (default) | ✅ |

### TD-2.2 Nested Command Construction

| Test ID | Input Flags | Expected INNER_CMD | Status |
|---------|-------------|-------------------|--------|
| TD-2.2.1 | `--interactive` | `PI_TK_INTERACTIVE_CHILD=1 pi "/tk-implement TICKET-123"` | ✅ |
| TD-2.2.2 | `--hands-free --clarify` | `PI_TK_INTERACTIVE_CHILD=1 pi "/tk-implement TICKET-123 --clarify"` | ✅ |
| TD-2.2.3 | `--dispatch --clarify` | `PI_TK_INTERACTIVE_CHILD=1 pi "/tk-implement TICKET-123 --clarify"` | ✅ |
| TD-2.2.4 | `--interactive` (no --clarify) | --clarify NOT passed to inner command | ✅ |

### TD-2.3 Recursion Guard

| Test ID | Scenario | Expected Behavior | Status |
|---------|----------|-------------------|--------|
| TD-2.3.1 | `PI_TK_INTERACTIVE_CHILD=1` set | Skip interactive routing, run Path A/B/C directly | ✅ |
| TD-2.3.2 | Nested command env var | Inner command has PI_TK_INTERACTIVE_CHILD=1 set | ✅ |

### TD-2.4 Router Position in Execution Flow

| Test ID | Verification Point | Expected | Status |
|---------|-------------------|----------|--------|
| TD-2.4.1 | Router timing | Runs after fast anchoring (Section 1) | ✅ |
| TD-2.4.2 | Router timing | Runs before Path A/B/C selection (Section 3) | ✅ |
| TD-2.4.3 | Path skipping | When interactive flag set, SKIP Path A/B/C in outer call | ✅ |

### TD-2.5 Overlay Controls (Console Verification)

| Test ID | Control | Expected Behavior | Status |
|---------|---------|-------------------|--------|
| TD-2.5.1 | Ctrl+T | Transfer output to agent context and close overlay | ⬜ Manual |
| TD-2.5.2 | Ctrl+B | Background session (keep running, detach overlay) | ⬜ Manual |
| TD-2.5.3 | Ctrl+Q | Show detach menu (transfer/background/kill options) | ⬜ Manual |
| TD-2.5.4 | Direct typing | In hands-free mode, user takeover by typing | ⬜ Manual |

### TD-2.6 Polling Cadence (Hands-Free Mode)

| Test ID | Parameter | Expected Value | Status |
|---------|-----------|----------------|--------|
| TD-2.6.1 | `handsFree.updateMode` | "on-quiet" | ✅ |
| TD-2.6.2 | `handsFree.quietThreshold` | 8000ms | ✅ |
| TD-2.6.3 | `handsFree.updateInterval` | 60000ms | ✅ |
| TD-2.6.4 | `handsFree.autoExitOnQuiet` | false | ✅ |

---

## TD-3: Session Lifecycle Testing

> **Purpose:** Validate `/sessions`, `/attach`, Ctrl+B backgrounding, Ctrl+Q detach flows, session ID surfacing, atomic session.json write, and cleanup semantics per PRD ID-3, ID-4.

### TD-3.1 Session Metadata Creation (session.json)

| Test ID | Mode | Expected session.json Created | Status |
|---------|------|------------------------------|--------|
| TD-3.1.1 | `--interactive` | Yes, at `.subagent-runs/<ticket>/session.json` | ✅ |
| TD-3.1.2 | `--hands-free` | Yes, at `.subagent-runs/<ticket>/session.json` | ✅ |
| TD-3.1.3 | `--dispatch` | Yes, at `.subagent-runs/<ticket>/session.json` | ✅ |
| TD-3.1.4 | No interactive flags | **NO** session.json created (backward compatible) | ✅ |
| TD-3.1.5 | Legacy `--async` | **NO** session.json created | ✅ |

### TD-3.2 Session Metadata Schema Validation

**Required Schema:**
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
| TD-3.2.1 | `mode` | One of: interactive, hands-free, dispatch | ✅ |
| TD-3.2.2 | `sessionId` | Non-empty string, URL-safe format | ✅ |
| TD-3.2.3 | `startedAt` | Valid ISO8601 timestamp | ✅ |
| TD-3.2.4 | `command` | Contains ticket ID, properly escaped | ✅ |
| TD-3.2.5 | `command` | --clarify present only if originally specified | ✅ |
| TD-3.2.6 | `status` | Starts as "pending" on creation | ✅ |

### TD-3.3 Atomic Write Semantics

| Test ID | Scenario | Expected Behavior | Status |
|---------|----------|-------------------|--------|
| TD-3.3.1 | Normal creation | Temp file (`session.json.tmp.$$`) written first | ✅ |
| TD-3.3.2 | Normal creation | `sync` called on temp file before rename | ✅ |
| TD-3.3.3 | Normal creation | Atomic `mv` from temp to final path | ✅ |
| TD-3.3.4 | Crash during write | No partial/corrupt session.json exists | ✅ |
| TD-3.3.5 | Concurrent invocations | Unique PID suffix prevents collisions | ✅ |

### TD-3.4 Cleanup on Failure

| Test ID | Failure Scenario | Expected Cleanup | Status |
|---------|------------------|------------------|--------|
| TD-3.4.1 | interactive_shell fails | Temp file removed if exists | ✅ |
| TD-3.4.2 | interactive_shell fails | No session.json written | ✅ |
| TD-3.4.3 | interactive_shell fails | Actionable error message emitted | ✅ |
| TD-3.4.4 | Post-failure state | Existing artifacts preserved | ✅ |

### TD-3.5 Console Breadcrumbs Output

| Test ID | Mode | Expected Console Output Contains | Status |
|---------|------|---------------------------------|--------|
| TD-3.5.1 | All interactive | "Interactive Session Started" header | ✅ |
| TD-3.5.2 | All interactive | `Mode: <mode>` displayed | ✅ |
| TD-3.5.3 | All interactive | `Session ID: <sessionId>` displayed | ✅ |
| TD-3.5.4 | All interactive | `/attach <sessionId>` command shown | ✅ |
| TD-3.5.5 | All interactive | `/sessions` command shown | ✅ |
| TD-3.5.6 | All interactive | `Ctrl+T` keybinding documented | ✅ |
| TD-3.5.7 | All interactive | `Ctrl+B` keybinding documented | ✅ |
| TD-3.5.8 | All interactive | `Ctrl+Q` keybinding documented | ✅ |

### TD-3.6 Session Query Operations

| Test ID | Command | Expected | Status |
|---------|---------|----------|--------|
| TD-3.6.1 | `/sessions` | Lists all active interactive sessions | ⬜ Manual |
| TD-3.6.2 | `/attach <sessionId>` | Reattaches to specific session | ⬜ Manual |
| TD-3.6.3 | `/attach` (no arg) | Interactive selector for sessions | ⬜ Manual |
| TD-3.6.4 | `/dismiss <sessionId>` | Kills specific session and cleans up | ⬜ Manual |
| TD-3.6.5 | `/dismiss` (no arg) | Kills all sessions | ⬜ Manual |

### TD-3.7 Artifact Location Consistency

| Test ID | Artifact | Expected Location | Interactive | Legacy |
|---------|----------|-------------------|-------------|--------|
| TD-3.7.1 | anchor-context.md | `.subagent-runs/<ticket>/anchor-context.md` | ✅ | ✅ |
| TD-3.7.2 | plan.md | `.subagent-runs/<ticket>/plan.md` | ✅ | ✅ |
| TD-3.7.3 | implementation.md | `.subagent-runs/<ticket>/implementation.md` | ✅ | ✅ |
| TD-3.7.4 | session.json | `.subagent-runs/<ticket>/session.json` | ✅ (only) | ❌ |
| TD-3.7.5 | review.md | `.subagent-runs/<ticket>/review.md` | ✅ | ✅ |

---

## TD-4: Regression Suite

> **Purpose:** Re-run baseline `/tk-implement`, `--async`, and `--clarify` flows to confirm Path A/B/C chains, outputs, and artifact layouts remain identical per PRD US-5.

### TD-4.1 Legacy Behavior Preservation

| Test ID | Command | Expected (Unchanged from Pre-Interactive Era) | Status |
|---------|---------|-----------------------------------------------|--------|
| TD-4.1.1 | `/tk-implement TICKET-123` | Runs Path A/B/C normally, no session.json | ✅ |
| TD-4.1.2 | `/tk-implement TICKET-123 --async` | Background subagent execution via `async: true` | ✅ |
| TD-4.1.3 | `/tk-implement TICKET-123 --clarify` | Chain clarification TUI opens | ✅ |
| TD-4.1.4 | `/tk-implement TICKET-123 --async --clarify` | Async wins, clarify=false (legacy rule) | ✅ |

### TD-4.2 Path A/B/C Chain Execution Unchanged

| Test ID | Path | Expected Chain Structure | Status |
|---------|------|-------------------------|--------|
| TD-4.2.1 | A (Minimal) | worker→reviewer→fixer→reviewer(re-check)→tk-closer | ✅ |
| TD-4.2.2 | B (Standard) | planner-b→worker→(review∥test)→fixer→(re-check∥re-test)→tk-closer | ✅ |
| TD-4.2.3 | C (Deep, no research) | planner-c→worker→(review∥test)→fixer→(re-check∥re-test)→tk-closer | ✅ |
| TD-4.2.4 | C (Deep, with research) | (research∥librarian)→planner-c→worker→(review∥test)→fixer→(re-check∥re-test)→tk-closer | ✅ |

### TD-4.3 Subagent Parameter Preservation

| Test ID | Parameter | Expected Value (All Modes) | Status |
|---------|-----------|---------------------------|--------|
| TD-4.3.1 | `clarify` | `<RUN_CLARIFY>` (default false) | ✅ |
| TD-4.3.2 | `async` | `<RUN_ASYNC>` (default false, true if --async) | ✅ |
| TD-4.3.3 | `artifacts` | `true` | ✅ |
| TD-4.3.4 | `includeProgress` | `false` | ✅ |
| TD-4.3.5 | `maxOutput.bytes` | `200000` | ✅ |
| TD-4.3.6 | `maxOutput.lines` | `5000` | ✅ |

### TD-4.4 Guardrail Compliance

| Test ID | Guardrail | Expected | Status |
|---------|-----------|----------|--------|
| TD-4.4.1 | No agent mgmt | Never call `subagent` with create/update/delete | ✅ |
| TD-4.4.2 | No chain def changes | Chain definition files untouched | ✅ |
| TD-4.4.3 | No new TUI | Uses existing `interactive_shell` tool only | ✅ |
| TD-4.4.4 | AGENT_SCOPE consistency | Same scope used on every subagent call | ✅ |

### TD-4.5 Fast Anchoring Consistency

| Test ID | Component | Expected (Unchanged) | Status |
|---------|-----------|---------------------|--------|
| TD-4.5.1 | Scout caching | Cache hit/miss logic unchanged | ✅ |
| TD-4.5.2 | Git hash validation | `.scout-git-hash` written same way | ✅ |
| TD-4.5.3 | Context-merger fallback | Works with or without context-merger agent | ✅ |
| TD-4.5.4 | Session directory handling | Subagent output copied to expected locations | ✅ |

---

## Test Execution Summary

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Verified/Pass |
| ⬜ | Not yet run/Manual test |
| ❌ | Failed |
| 🔄 | In Progress |

### Coverage Matrix

| TD Section | Description | Total Tests | Automated | Manual | Pass Rate |
|------------|-------------|-------------|-----------|--------|-----------|
| TD-1 | Flag Validator Coverage | 21 | 21 | 0 | 100% |
| TD-2 | Mode Behavior Smoke Tests | 18 | 13 | 5 | 72% |
| TD-3 | Session Lifecycle Testing | 30 | 25 | 5 | 83% |
| TD-4 | Regression Suite | 21 | 21 | 0 | 100% |
| **Total** | | **90** | **80** | **10** | **89%** |

---

## Quick Reference

### Flag Quick Reference

```
--interactive    Supervised overlay (blocking, no --clarify allowed)
--hands-free     Agent-monitored overlay (polling, allows --clarify)
--dispatch       Headless background (notification, allows --clarify)
--async          Legacy background (no session tracking)
--clarify        Chain confirmation TUI
```

### Session Commands Quick Reference

```
/sessions                    List active interactive sessions
/attach <sessionId>         Reattach to specific session
/attach                      Interactive session selector
/dismiss <sessionId>        Kill specific session
/dismiss                     Kill all sessions
```

### Keybindings Quick Reference

```
Ctrl+T  Transfer output to agent context and close
Ctrl+B  Background session (keep running, detach overlay)
Ctrl+Q  Detach menu (transfer/background/kill options)
```

### Session.json Schema Quick Reference

```json
{
  "mode": "interactive|hands-free|dispatch",
  "sessionId": "calm-reef",
  "startedAt": "2026-03-04T12:34:56.789Z",
  "command": "pi \"/tk-implement TICKET-123\"",
  "status": "pending"
}
```

---

## Version History

| Date | Ticket | Changes |
|------|--------|---------|
| 2026-03-04 | ptf-niv3 | Initial flag matrix (Sections A-E) |
| 2026-03-04 | ptf-vln5 | Routing verification section added |
| 2026-03-04 | ptf-fqvd | Reorganized into TD-1..TD-4 structure, added atomic write and cleanup tests |
