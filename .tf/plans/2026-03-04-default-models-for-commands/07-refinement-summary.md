# Refinement Summary: Default Models for Commands

**Date:** 2026-03-04
**Feature:** Per-Command Model Configuration via `pi-prompt-template-model`
**Status:** REFINED — Ready for Ticketization

---

## Overview

This document summarizes the refinement process for the "Default Models for Commands" implementation plan. The plan underwent gap analysis, review, and refinement to address critical issues before ticketization.

---

## Major Changes Made

### 1. Explicit 5-Level Model Precedence Ladder (GAP-001)

**Problem:** The spec stated that "runtime overrides in subagent tool calls take precedence" but did not provide a complete precedence hierarchy covering all model selection scenarios.

**Resolution:** Added canonical precedence ladder to implementation plan Task 3:

```
1. subagent tool call `model` parameter (runtime override)     — HIGHEST
2. Agent definition frontmatter `model`
3. Main loop model (prompt frontmatter via extension)
4. Project defaults (.pi/settings.json)
5. Global defaults (~/.pi/agent/settings.json)                — LOWEST
```

**Impact:** Implementers can now unambiguously determine which model takes effect in any scenario involving main loop commands and subagent calls.

**Files affected:**
- `03-implementation-plan.md` — Task 3 now specifies the ladder verbatim
- `.tf/knowledge/topics/model-configuration.md` — will contain canonical text

---

### 2. `/tk-bootstrap` Command Model Mapping (GAP-002)

**Problem:** The plan covered 6 tk commands but omitted `/tk-bootstrap`, leaving inconsistent coverage of the tk-flow command suite.

**Resolution:** Added explicit mapping:

| Command | Model |
|---------|-------|
| `/tk-bootstrap` | `claude-haiku-4-5` |

**Rationale:** Bootstrap is a fast setup/installation command that benefits from cost optimization but doesn't require strong reasoning.

**Note:** `/tk-bootstrap` is an extension command (not prompt-backed), so it appears in documentation only — no frontmatter changes required.

**Files affected:**
- `README.md` — command-to-model mapping table now includes `/tk-bootstrap`
- `03-implementation-plan.md` — Task 1 acceptance criteria updated

---

### 3. Scope Reconciliation (GAP-003)

**Problem:** PRD stated "Modifying agent definition files" was out of scope, but implementation plan Task 4 proposed auditing/updating `assets/agents/*.md`.

**Resolution:** Chose Option A — removed agent definition edits from scope.

**Changes:**
- Removed Task 4 ("Audit and update agent definitions") from implementation plan
- Removed `assets/agents/*.md` from "Files to Modify" list
- Added explicit statement: "agent definition changes are out of scope for this feature iteration"

**Rationale:** Keeps implementation focused and aligned with PRD constraints. Agent model tuning can be addressed in a follow-up feature.

**Files affected:**
- `03-implementation-plan.md` — Task 4 removed, scope statement added

---

### 4. Executable Validation Protocol (GAP-004)

**Problem:** Task 5 said "Run manual checks" but lacked concrete commands, fixtures, and pass/fail criteria.

**Resolution:** Rewrote Task 5 as an executable validation checklist with three sections:

**A. Static file checks** — grep commands to verify frontmatter in all prompt files:
```bash
grep -n '^model:' prompts/tk-implement.md prompts/tk-brainstorm.md ...
grep -n '/tk-bootstrap' README.md
grep -n 'subagent tool call `model` parameter' .tf/knowledge/topics/model-configuration.md
```

**B. Runtime checks with extension installed:**
```bash
pi install npm:pi-prompt-template-model
# Start pi, run commands, verify model switch/restore
/tk-plan default-models-smoke
/tk-plan-check .tf/plans/2026-03-04-default-models-for-commands
/tk-bootstrap --scope project --dry-run
```

**C. Graceful degradation checks (extension disabled):**
- Disable/uninstall extension
- Run tk commands
- Verify no regression

**Pass/Fail criteria:**
- PASS if all six prompt files include expected `model:` values
- PASS if README mapping includes `/tk-bootstrap` → `claude-haiku-4-5`
- PASS if precedence ladder includes all 5 levels in correct order
- PASS if extension-on run shows expected switch/restore behavior
- PASS if extension-off run still executes tk commands without regression

**Files affected:**
- `03-implementation-plan.md` — Task 5 completely rewritten

---

## Gap Resolution Summary

| Gap ID | Priority | Description | Status |
|--------|----------|-------------|--------|
| GAP-001 | Critical | Incomplete precedence ladder | ✅ RESOLVED |
| GAP-002 | Critical | Missing `/tk-bootstrap` mapping | ✅ RESOLVED |
| GAP-003 | Major | Scope contradiction (agent edits) | ✅ RESOLVED |
| GAP-004 | Major | Validation not ticket-ready | ✅ RESOLVED |

---

## Unresolved Items

### None blocking ticketization.

### Deferred to follow-up (optional improvements from review):

1. **Per-command `thinking` rationale table** — Could add documentation explaining why each command uses its specific thinking level (low/medium/high).

2. **Operator-facing migration note** — Document behavior change for users who manually use `/model` switching before running tk commands.

3. **Rollback runbook** — Add git commands for quick frontmatter reversion:
   ```bash
   git checkout HEAD~1 -- prompts/*.md README.md
   ```

These are non-blocking and can be addressed during implementation or as documentation polish.

---

## Ticketization Decision

### ✅ GO

**Rationale:**
- All 4 gaps (2 critical, 2 major) have been resolved
- Implementation plan has explicit, executable tasks
- Validation protocol provides clear pass/fail criteria
- Scope is unambiguous (agent edits explicitly excluded)
- Precedence ladder is canonical and complete
- `/tk-bootstrap` is explicitly documented

**Recommendation:** Proceed with ticket split using the refined implementation plan.

---

## Files Modified During Refinement

| File | Change |
|------|--------|
| `03-implementation-plan.md` | Added precedence ladder, `/tk-bootstrap` mapping, removed agent edit task, rewrote validation checklist |

## Files Created During Refinement

| File | Purpose |
|------|---------|
| `05-plan-gaps.md` | Gap analysis |
| `06-plan-review.md` | Review decision |
| `plan-gaps-v2.md` | Updated gap analysis |
| `plan-review-v2.md` | Updated review |
| `07-refinement-summary.md` | This document |

---

## Next Steps

1. **Ticket Split:** Break refined implementation plan into tickets:
   - Ticket 1: README updates (extension docs + command mapping table)
   - Ticket 2: Prompt frontmatter additions (6 files)
   - Ticket 3: Knowledge base documentation (precedence ladder + patterns)
   - Ticket 4: Validation execution and evidence capture

2. **Implementation:** Execute tickets in dependency order (1 → 2 → 3 → 4)

3. **Documentation Polish:** Address optional improvements during or after implementation
