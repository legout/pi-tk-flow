# /tk-implement Flag Parser Verification Runs

**Ticket:** ptf-niv3  
**Date:** 2026-03-04  
**Version:** Parser verification for interactive mode flags

---

## A.1 Valid Single Flags

### A.1.1: No flags (default Path A/B/C execution)
```bash
/tk-implement TICKET-123
```
**Expected:** Runs Path A/B/C (no interactive mode, no session.json created)  
**Result:** PASS  
**Notes:** Parser correctly identifies no interactive flags, routes to standard path execution.

---

### A.1.2: --interactive
```bash
/tk-implement TICKET-123 --interactive
```
**Expected:** Interactive mode overlay (supervised, blocking)  
**Result:** PASS  
**Notes:** Parser sets RUN_INTERACTIVE=true, routes through interactive_shell with mode="interactive".

---

### A.1.3: --hands-free
```bash
/tk-implement TICKET-123 --hands-free
```
**Expected:** Hands-free monitored overlay (polling, non-blocking)  
**Result:** PASS  
**Notes:** Parser sets RUN_HANDS_FREE=true, routes through interactive_shell with mode="hands-free" and handsFree config.

---

### A.1.4: --dispatch
```bash
/tk-implement TICKET-123 --dispatch
```
**Expected:** Dispatch background mode (fire-and-forget)  
**Result:** PASS  
**Notes:** Parser sets RUN_DISPATCH=true, routes through interactive_shell with mode="dispatch" and background=true.

---

### A.1.5: --async (legacy)
```bash
/tk-implement TICKET-123 --async
```
**Expected:** Legacy async mode (background subagent, no session tracking)  
**Result:** PASS  
**Notes:** Parser sets RUN_ASYNC=true, executes Path A/B/C with async: true on subagent calls.

---

### A.1.6: --clarify
```bash
/tk-implement TICKET-123 --clarify
```
**Expected:** Chain clarification TUI opens before execution  
**Result:** PASS  
**Notes:** Parser sets RUN_CLARIFY=true, clarify TUI presented before path execution.

---

## A.2 Invalid Flag Combinations (Error Cases)

### A.2.1: --interactive + --hands-free
```bash
/tk-implement TICKET-123 --interactive --hands-free
```
**Expected Error:** "Cannot combine --interactive with --hands-free"  
**Result:** PASS  
**Notes:** Parser detects mutual exclusivity violation between interactive flags.

---

### A.2.2: --interactive + --dispatch
```bash
/tk-implement TICKET-123 --interactive --dispatch
```
**Expected Error:** "Cannot combine --interactive with --dispatch"  
**Result:** PASS  
**Notes:** Parser detects mutual exclusivity violation between interactive flags.

---

### A.2.3: --hands-free + --dispatch
```bash
/tk-implement TICKET-123 --hands-free --dispatch
```
**Expected Error:** "Cannot combine --hands-free with --dispatch"  
**Result:** PASS  
**Notes:** Parser detects mutual exclusivity violation between interactive flags.

---

### A.2.4: --interactive + --async
```bash
/tk-implement TICKET-123 --interactive --async
```
**Expected Error:** "Interactive modes cannot be used with --async"  
**Result:** PASS  
**Notes:** Parser detects conflict between interactive mode and legacy async flag.

---

### A.2.5: --hands-free + --async
```bash
/tk-implement TICKET-123 --hands-free --async
```
**Expected Error:** "Interactive modes cannot be used with --async"  
**Result:** PASS  
**Notes:** Parser detects conflict between interactive mode and legacy async flag.

---

### A.2.6: --dispatch + --async
```bash
/tk-implement TICKET-123 --dispatch --async
```
**Expected Error:** "Interactive modes cannot be used with --async"  
**Result:** PASS  
**Notes:** Parser detects conflict between interactive mode and legacy async flag.

---

### A.2.7: --interactive + --clarify
```bash
/tk-implement TICKET-123 --interactive --clarify
```
**Expected Error:** "--interactive and --clarify are mutually exclusive (overlay conflict)"  
**Result:** PASS  
**Notes:** Parser detects overlay conflict - both flags want to control the UI.

---

### A.2.8: Unknown flag
```bash
/tk-implement TICKET-123 --unknown-flag
```
**Expected Error:** 
```
Unknown flag: --unknown-flag

Usage: /tk-implement <TICKET_ID> [flags]

Flags:
  --interactive    Run with interactive overlay (supervised, blocking)
  --hands-free     Run with agent-monitored overlay (polling, non-blocking)
  --dispatch       Run headless background with notification (fire-and-forget)
  --async          Legacy background mode (no session tracking)
  --clarify        Open chain clarification TUI

Use /tk-implement --help for full documentation.
```
**Result:** PASS  
**Notes:** Parser correctly identifies unknown flag and displays help message with all supported flags.

---

## A.3 Valid Flag Combinations

### A.3.1: --hands-free + --clarify
```bash
/tk-implement TICKET-123 --hands-free --clarify
```
**Expected:** Clarify TUI runs first, then hands-free overlay starts  
**Result:** PASS  
**Notes:** Parser allows combination. Clarify runs before hands-free overlay is initiated.

---

### A.3.2: --dispatch + --clarify
```bash
/tk-implement TICKET-123 --dispatch --clarify
```
**Expected:** Clarify TUI runs first, then dispatch proceeds  
**Result:** PASS  
**Notes:** Parser allows combination. Clarify runs before dispatch is initiated.

---

### A.3.3: --async + --clarify (legacy behavior)
```bash
/tk-implement TICKET-123 --async --clarify
```
**Expected:** Legacy: async wins, clarify=false (silently ignores clarify)  
**Result:** PASS  
**Notes:** Parser applies legacy rule: when both --async and --clarify are set, async takes precedence and clarify is disabled.

---

## Summary

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| A.1 Valid Single Flags | 6 | 6 | 0 |
| A.2 Invalid Combinations | 8 | 8 | 0 |
| A.3 Valid Combinations | 3 | 3 | 0 |
| **Total** | **17** | **17** | **0** |

---

## Validation Order Verified

The parser validates flags in the correct order:

1. ✅ Unknown flags first (A.2.8)
2. ✅ Mutual exclusivity among --interactive, --hands-free, --dispatch (A.2.1-A.2.3)
3. ✅ Interactive flags against --async (A.2.4-A.2.6)
4. ✅ --interactive against --clarify (A.2.7)
5. ✅ Legacy rule: --async wins over --clarify (A.3.3)

---

## Files Referenced

- `prompts/tk-implement.md` - Flag parsing section (lines 13-66)
- `tests/tk-implement/flag-matrix.md` - Test specification
