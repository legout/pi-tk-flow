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

| Test ID | Command/Scenario | Expected Order | Status |
|---------|------------------|----------------|--------|
| TD-1.4.1 | `/tk-implement TICKET-123 --unknown-flag --interactive --hands-free` | Unknown flag error emitted before mutual exclusivity check | ✅ |
| TD-1.4.2 | `/tk-implement TICKET-123 --interactive --hands-free --async` | Mutual exclusivity (--interactive vs --hands-free) error before async check | ✅ |
| TD-1.4.3 | `/tk-implement TICKET-123 --interactive --async` | Interactive vs --async blocked after mutual exclusivity passes | ✅ |
| TD-1.4.4 | `/tk-implement TICKET-123 --interactive --clarify` | --interactive vs --clarify blocked after async check passes | ✅ |
| TD-1.4.5 | `/tk-implement TICKET-123 --async --clarify` | Legacy rule applied last: --async wins over --clarify (no error, clarify=false) | ✅ |

---

## TD-2: Mode Behavior Smoke Tests

> **Purpose:** Manual/integration runs verifying overlays, hands-free polling cadence, dispatch completion notifications, and Ctrl+T/B/Q behaviors per PRD ID-2, ID-4.

### TD-2.1 interactive_shell Parameter Construction

| Test ID | Command | Expected interactive_shell Parameters | Status |
|---------|---------|--------------------------------------|--------|
| TD-2.1.1 | `/tk-implement TICKET-123 --interactive` | `mode: "interactive"`, command nested without interactive flags | ✅ |
| TD-2.1.2 | `/tk-implement TICKET-123 --hands-free` | `mode: "hands-free"`, `handsFree: {updateMode: "on-quiet", quietThreshold: 8000, updateInterval: 60000, autoExitOnQuiet: false}` | ✅ |
| TD-2.1.3 | `/tk-implement TICKET-123 --dispatch` | `mode: "dispatch"`, `background: true`, `autoExitOnQuiet: true` (default) | ✅ |

### TD-2.2 Nested Command Construction

| Test ID | Command | Expected INNER_CMD | Status |
|---------|---------|-------------------|--------|
| TD-2.2.1 | `/tk-implement TICKET-123 --interactive` | `PI_TK_INTERACTIVE_CHILD=1 pi "/tk-implement TICKET-123"` | ✅ |
| TD-2.2.2 | `/tk-implement TICKET-123 --hands-free --clarify` | `PI_TK_INTERACTIVE_CHILD=1 pi "/tk-implement TICKET-123 --clarify"` | ✅ |
| TD-2.2.3 | `/tk-implement TICKET-123 --dispatch --clarify` | `PI_TK_INTERACTIVE_CHILD=1 pi "/tk-implement TICKET-123 --clarify"` | ✅ |
| TD-2.2.4 | `/tk-implement TICKET-123 --interactive` (no --clarify) | --clarify NOT passed to inner command | ✅ |

### TD-2.3 Recursion Guard

| Test ID | Command/Scenario | Expected Behavior | Status |
|---------|------------------|-------------------|--------|
| TD-2.3.1 | `PI_TK_INTERACTIVE_CHILD=1 /tk-implement TICKET-123 --interactive` | Skip interactive routing, run Path A/B/C directly | ✅ |
| TD-2.3.2 | `/tk-implement TICKET-123 --interactive` (nested call) | Inner command has `PI_TK_INTERACTIVE_CHILD=1` set in environment | ✅ |

### TD-2.4 Router Position in Execution Flow

| Test ID | Verification Point | Expected | Status |
|---------|-------------------|----------|--------|
| TD-2.4.1 | Run `/tk-implement TICKET-123 --interactive` | Router runs after fast anchoring (Section 1) | ✅ |
| TD-2.4.2 | Run `/tk-implement TICKET-123 --interactive` | Router runs before Path A/B/C selection (Section 3) | ✅ |
| TD-2.4.3 | Run `/tk-implement TICKET-123 --interactive` | When interactive flag set, SKIP Path A/B/C in outer call | ✅ |

### TD-2.5 Overlay Controls (Console Verification)

| Test ID | Command | Control | Expected Behavior | Status |
|---------|---------|---------|-------------------|--------|
| TD-2.5.1 | `/tk-implement TICKET-123 --interactive` | Ctrl+T | Transfer output to agent context and close overlay | ⬜ Manual |
| TD-2.5.2 | `/tk-implement TICKET-123 --interactive` | Ctrl+B | Background session (keep running, detach overlay) | ⬜ Manual |
| TD-2.5.3 | `/tk-implement TICKET-123 --interactive` | Ctrl+Q | Show detach menu (transfer/background/kill options) | ⬜ Manual |
| TD-2.5.4 | `/tk-implement TICKET-123 --hands-free` | Direct typing | In hands-free mode, user takeover by typing | ⬜ Manual |

### TD-2.6 Polling Cadence (Hands-Free Mode)

| Test ID | Command | Parameter | Expected Value | Status |
|---------|---------|-----------|----------------|--------|
| TD-2.6.1 | `/tk-implement TICKET-123 --hands-free` | `handsFree.updateMode` | "on-quiet" | ✅ |
| TD-2.6.2 | `/tk-implement TICKET-123 --hands-free` | `handsFree.quietThreshold` | 8000ms | ✅ |
| TD-2.6.3 | `/tk-implement TICKET-123 --hands-free` | `handsFree.updateInterval` | 60000ms | ✅ |
| TD-2.6.4 | `/tk-implement TICKET-123 --hands-free` | `handsFree.autoExitOnQuiet` | false | ✅ |

---

## TD-3: Session Lifecycle Testing

> **Purpose:** Validate `/sessions`, `/attach`, Ctrl+B backgrounding, Ctrl+Q detach flows, session ID surfacing, atomic session.json write, and cleanup semantics per PRD ID-3, ID-4.

### TD-3.1 Session Metadata Creation (session.json)

| Test ID | Command | Expected session.json Created | Status |
|---------|---------|------------------------------|--------|
| TD-3.1.1 | `/tk-implement TICKET-123 --interactive` | Yes, at `.subagent-runs/<ticket>/session.json` | ✅ |
| TD-3.1.2 | `/tk-implement TICKET-123 --hands-free` | Yes, at `.subagent-runs/<ticket>/session.json` | ✅ |
| TD-3.1.3 | `/tk-implement TICKET-123 --dispatch` | Yes, at `.subagent-runs/<ticket>/session.json` | ✅ |
| TD-3.1.4 | `/tk-implement TICKET-123` | **NO** session.json created (backward compatible) | ✅ |
| TD-3.1.5 | `/tk-implement TICKET-123 --async` | **NO** session.json created | ✅ |

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

| Test ID | Command | Field | Validation | Status |
|---------|---------|-------|------------|--------|
| TD-3.2.1 | `/tk-implement TICKET-123 --interactive` | `mode` | One of: interactive, hands-free, dispatch | ✅ |
| TD-3.2.2 | `/tk-implement TICKET-123 --interactive` | `sessionId` | Non-empty string, URL-safe format | ✅ |
| TD-3.2.3 | `/tk-implement TICKET-123 --interactive` | `startedAt` | Valid ISO8601 timestamp | ✅ |
| TD-3.2.4 | `/tk-implement TICKET-123 --interactive` | `command` | Contains ticket ID, properly escaped | ✅ |
| TD-3.2.5 | `/tk-implement TICKET-123 --hands-free --clarify` | `command` | --clarify present only if originally specified | ✅ |
| TD-3.2.6 | `/tk-implement TICKET-123 --interactive` | `status` | Starts as "pending" on creation | ✅ |

### TD-3.3 Atomic Write Semantics

| Test ID | Command | Scenario | Expected Behavior | Status |
|---------|---------|----------|-------------------|--------|
| TD-3.3.1 | `/tk-implement TICKET-123 --interactive` | Normal creation | Temp file (`session.json.tmp.$$`) written first | ✅ |
| TD-3.3.2 | `/tk-implement TICKET-123 --interactive` | Normal creation | `sync` called on temp file before rename | ✅ |
| TD-3.3.3 | `/tk-implement TICKET-123 --interactive` | Normal creation | Atomic `mv` from temp to final path | ✅ |
| TD-3.3.4 | Kill process during `/tk-implement TICKET-123 --interactive` | Crash during write | No partial/corrupt session.json exists | ⬜ Manual |
| TD-3.3.5 | Two concurrent `/tk-implement TICKET-123 --interactive` calls | Concurrent invocations | Unique PID suffix prevents collisions | ⬜ Manual |

### TD-3.4 Cleanup on Failure

| Test ID | Command | Failure Scenario | Expected Cleanup | Status |
|---------|---------|------------------|------------------|--------|
| TD-3.4.1 | `/tk-implement TICKET-123 --interactive` (force fail) | interactive_shell fails | Temp file removed if exists | ⬜ Manual |
| TD-3.4.2 | `/tk-implement TICKET-123 --interactive` (force fail) | interactive_shell fails | No session.json written | ⬜ Manual |
| TD-3.4.3 | `/tk-implement TICKET-123 --interactive` (force fail) | interactive_shell fails | Actionable error message emitted | ⬜ Manual |
| TD-3.4.4 | `/tk-implement TICKET-123 --interactive` (force fail) | Post-failure state | Existing artifacts preserved | ⬜ Manual |

### TD-3.5 Console Breadcrumbs Output

| Test ID | Command | Mode | Expected Console Output Contains | Status |
|---------|---------|------|---------------------------------|--------|
| TD-3.5.1 | `/tk-implement TICKET-123 --interactive` | All interactive | "Interactive Session Started" header | ✅ |
| TD-3.5.2 | `/tk-implement TICKET-123 --interactive` | All interactive | `Mode: <mode>` displayed | ✅ |
| TD-3.5.3 | `/tk-implement TICKET-123 --interactive` | All interactive | `Session ID: <sessionId>` displayed | ✅ |
| TD-3.5.4 | `/tk-implement TICKET-123 --interactive` | All interactive | `/attach <sessionId>` command shown | ✅ |
| TD-3.5.5 | `/tk-implement TICKET-123 --interactive` | All interactive | `/sessions` command shown | ✅ |
| TD-3.5.6 | `/tk-implement TICKET-123 --interactive` | All interactive | `Ctrl+T` keybinding documented | ✅ |
| TD-3.5.7 | `/tk-implement TICKET-123 --interactive` | All interactive | `Ctrl+B` keybinding documented | ✅ |
| TD-3.5.8 | `/tk-implement TICKET-123 --interactive` | All interactive | `Ctrl+Q` keybinding documented | ✅ |

### TD-3.6 Session Query Operations

| Test ID | Command | Expected | Status |
|---------|---------|----------|--------|
| TD-3.6.1 | `/sessions` | Lists all active interactive sessions | ⬜ Manual |
| TD-3.6.2 | `/attach <sessionId>` | Reattaches to specific session | ⬜ Manual |
| TD-3.6.3 | `/attach` (no arg) | Interactive selector for sessions | ⬜ Manual |
| TD-3.6.4 | `/dismiss <sessionId>` | Kills specific session and cleans up | ⬜ Manual |
| TD-3.6.5 | `/dismiss` (no arg) | Kills all sessions | ⬜ Manual |

### TD-3.7 Artifact Location Consistency

| Test ID | Command | Artifact | Expected Location | Interactive | Legacy |
|---------|---------|----------|-------------------|-------------|--------|
| TD-3.7.1 | `/tk-implement TICKET-123 --interactive` | anchor-context.md | `.subagent-runs/<ticket>/anchor-context.md` | ✅ | ✅ |
| TD-3.7.2 | `/tk-implement TICKET-123 --interactive` | plan.md | `.subagent-runs/<ticket>/plan.md` | ✅ | ✅ |
| TD-3.7.3 | `/tk-implement TICKET-123 --interactive` | implementation.md | `.subagent-runs/<ticket>/implementation.md` | ✅ | ✅ |
| TD-3.7.4 | `/tk-implement TICKET-123 --interactive` | session.json | `.subagent-runs/<ticket>/session.json` | ✅ (only) | ❌ |
| TD-3.7.5 | `/tk-implement TICKET-123 --interactive` | review.md | `.subagent-runs/<ticket>/review.md` | ✅ | ✅ |

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

| Test ID | Command | Path | Expected Chain Structure | Status |
|---------|---------|------|-------------------------|--------|
| TD-4.2.1 | `/tk-implement MINIMAL-TICKET` | A (Minimal) | worker→reviewer→fixer→reviewer(re-check)→tk-closer | ✅ |
| TD-4.2.2 | `/tk-implement STANDARD-TICKET` | B (Standard) | planner-b→worker→(review∥test)→fixer→(re-check∥re-test)→tk-closer | ✅ |
| TD-4.2.3 | `/tk-implement COMPLEX-TICKET` | C (Deep, no research) | planner-c→worker→(review∥test)→fixer→(re-check∥re-test)→tk-closer | ✅ |
| TD-4.2.4 | `/tk-implement RESEARCH-TICKET` | C (Deep, with research) | (research∥librarian)→planner-c→worker→(review∥test)→fixer→(re-check∥re-test)→tk-closer | ✅ |

### TD-4.3 Subagent Parameter Preservation

| Test ID | Command | Parameter | Expected Value (All Modes) | Status |
|---------|---------|-----------|---------------------------|--------|
| TD-4.3.1 | `/tk-implement TICKET-123` | `clarify` | `<RUN_CLARIFY>` (default false) | ✅ |
| TD-4.3.2 | `/tk-implement TICKET-123 --async` | `async` | `<RUN_ASYNC>` (default false, true if --async) | ✅ |
| TD-4.3.3 | `/tk-implement TICKET-123` | `artifacts` | `true` | ✅ |
| TD-4.3.4 | `/tk-implement TICKET-123` | `includeProgress` | `false` | ✅ |
| TD-4.3.5 | `/tk-implement TICKET-123` | `maxOutput.bytes` | `200000` | ✅ |
| TD-4.3.6 | `/tk-implement TICKET-123` | `maxOutput.lines` | `5000` | ✅ |

### TD-4.4 Guardrail Compliance

| Test ID | Command | Guardrail | Expected | Status |
|---------|---------|-----------|----------|--------|
| TD-4.4.1 | `/tk-implement TICKET-123` | No agent mgmt | Never call `subagent` with create/update/delete | ✅ |
| TD-4.4.2 | `/tk-implement TICKET-123` | No chain def changes | Chain definition files untouched | ✅ |
| TD-4.4.3 | `/tk-implement TICKET-123 --interactive` | No new TUI | Uses existing `interactive_shell` tool only | ✅ |
| TD-4.4.4 | `/tk-implement TICKET-123` | AGENT_SCOPE consistency | Same scope used on every subagent call | ✅ |

### TD-4.5 Fast Anchoring Consistency

| Test ID | Command | Component | Expected (Unchanged) | Status |
|---------|---------|-----------|---------------------|--------|
| TD-4.5.1 | `/tk-implement TICKET-123` | Scout caching | Cache hit/miss logic unchanged | ✅ |
| TD-4.5.2 | `/tk-implement TICKET-123` | Git hash validation | `.scout-git-hash` written same way | ✅ |
| TD-4.5.3 | `/tk-implement TICKET-123` | Context-merger fallback | Works with or without context-merger agent | ✅ |
| TD-4.5.4 | `/tk-implement TICKET-123` | Session directory handling | Subagent output copied to expected locations | ✅ |

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
| TD-1 | Flag Validator Coverage | 22 | 22 | 0 | 100% |
| TD-2 | Mode Behavior Smoke Tests | 20 | 16 | 4 | 80% |
| TD-3 | Session Lifecycle Testing | 38 | 29 | 9 | 76% |
| TD-4 | Regression Suite | 22 | 22 | 0 | 100% |
| **Total** | | **102** | **89** | **13** | **87%** |

### ID-to-Evidence Reconciliation

| TD Section | Test IDs | Evidence in model-test-output.md |
|------------|----------|----------------------------------|
| TD-1 | TD-1.1.1–TD-1.1.6, TD-1.2.1–TD-1.2.8, TD-1.3.1–TD-1.3.3, TD-1.4.1–TD-1.4.5 | Sections A.1, A.2, A.3, TD-1.4 |
| TD-2 | TD-2.1.1–TD-2.1.3, TD-2.2.1–TD-2.2.4, TD-2.3.1–TD-2.3.2, TD-2.4.1–TD-2.4.3, TD-2.5.1–TD-2.5.4, TD-2.6.1–TD-2.6.4 | Sections B.1, B.2, B.3, B.4, TD-2.5 (Manual), TD-2.6 |
| TD-3 | TD-3.1.1–TD-3.1.5, TD-3.2.1–TD-3.2.6, TD-3.3.1–TD-3.3.5, TD-3.4.1–TD-3.4.4, TD-3.5.1–TD-3.5.8, TD-3.6.1–TD-3.6.5, TD-3.7.1–TD-3.7.5 | Sections TD-3.1, TD-3.2, TD-3.3, TD-3.4, TD-3.5, TD-3.6 (Manual), TD-3.7 |
| TD-4 | TD-4.1.1–TD-4.1.4, TD-4.2.1–TD-4.2.4, TD-4.3.1–TD-4.3.6, TD-4.4.1–TD-4.4.4, TD-4.5.1–TD-4.5.4 | Sections TD-4.1, TD-4.2, TD-4.3, TD-4.4, TD-4.5 |

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
| 2026-03-04 | ptf-fqvd-fix | Added Command column to all test tables, fixed coverage totals (22/20/38/22=102), added ID-to-Evidence reconciliation table |
