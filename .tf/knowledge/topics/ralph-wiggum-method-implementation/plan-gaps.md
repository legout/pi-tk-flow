# Plan Gaps: Ralph Wiggum Method Implementation

## Verdict
- **Ready for ticketization:** PARTIAL
- **Reason:** Core implementation is complete in prompts/tf-implement.md with README updates, but two planned deliverables are missing: (1) skills/tk-workflow/SKILL.md documentation update, and (2) tests/tk-implement/flag-matrix.md test coverage. Also, naming discrepancy between "tk-implement" (plan) and "tf-implement" (actual implementation) needs reconciliation.

## Gap Summary
- Critical: 0
- Major: 2
- Minor: 1

## Gaps

1. **[Major] GAP-001: Missing skills/tk-workflow/SKILL.md Documentation**
   - **Where:** Implementation Plan Task 4, PRD ID-4, Spec section 5
   - **Issue:** The skills/ directory does not exist; tk-workflow/SKILL.md was never created. Implementation Plan explicitly lists this as a file to modify: "skills/tk-workflow/SKILL.md – teach tk practitioners how/when to use the new modes."
   - **Impact:** Users cannot learn about execution modes from the skill documentation. The tk-workflow skill is referenced in AGENTS.md as the primary workflow skill, but it lacks execution mode guidance.
   - **Recommended fix:** Create skills/tk-workflow/SKILL.md with: (a) execution mode semantics, (b) when to use each mode, (c) keyboard shortcuts reference, (d) /sessions and /attach usage, (e) compatibility matrix, (f) troubleshooting overlay controls.
   - **Blocks ticketization:** No - core functionality works without this, but it's a documented deliverable in the PRD/Spec.

2. **[Major] GAP-002: Missing tests/tk-implement/flag-matrix.md Test Coverage**
   - **Where:** Implementation Plan Task 5, PRD TD-1..TD-4, Spec Testing Strategy
   - **Issue:** The tests/ directory has no tk-implement subdirectory. The test file tests/tk-implement/flag-matrix.md was never created despite being listed as a new file in the Implementation Plan.
   - **Impact:** No structured test coverage for the 102-flag combination matrix mentioned in scout-context. Without this, regression testing relies on manual verification. PRD Testing Decisions TD-1..TD-4 require this coverage.
   - **Recommended fix:** Create tests/tk-implement/flag-matrix.md with: (a) TD-1 flag validator coverage (all valid/invalid combinations), (b) TD-2 mode behavior smoke tests, (c) TD-3 session lifecycle testing, (d) TD-4 regression suite for legacy flows.
   - **Blocks ticketization:** No - implementation is tested via scout verification, but formal test coverage is missing per plan requirements.

3. **[Minor] GAP-003: Command Naming Discrepancy (tk-implement vs tf-implement)**
   - **Where:** All planning documents vs prompts/tf-implement.md
   - **Issue:** Planning documents consistently reference `/tk-implement`, but the actual implementation file is `prompts/tf-implement.md` and the internal command references use `/tf-implement`. The scout-context confirms "The plan is ALREADY IMPLEMENTED in prompts/tf-implement.md."
   - **Impact:** Potential confusion for users expecting `/tk-implement` command. The AGENTS.md mentions `/tk-implement` in examples but the actual prompt is `/tf-implement`.
   - **Recommended fix:** Either (a) rename prompts/tf-implement.md to prompts/tk-implement.md to match planning docs, or (b) update all planning documents to reference `/tf-implement` consistently. Recommend option (b) since the implementation is already functional as `/tf-implement`.
   - **Blocks ticketization:** No - the implementation works; this is a documentation consistency issue.

## Quick Fix Plan

1. **Create skills/tk-workflow/SKILL.md** - Add execution mode documentation to teach practitioners when/how to use --interactive, --hands-free, --dispatch modes with keyboard shortcuts and session management.

2. **Create tests/tk-implement/flag-matrix.md** - Add structured test coverage for flag validation matrix (TD-1), mode behaviors (TD-2), session lifecycle (TD-3), and regression suite (TD-4).

3. **Reconcile naming** - Update planning documents or create symlink/alias so `/tk-implement` and `/tf-implement` resolve consistently.

## Additional Observations

### Implementation Status (Verified)
- ✅ Flag parsing and validation (Section 1 of prompts/tf-implement.md) - Complete with full validation matrix
- ✅ Interactive execution router (Section 2) - Complete with recursion guard, session metadata, atomic writes
- ✅ Session metadata persistence (Section 2d) - Complete with session.json schema
- ✅ README.md documentation - Complete with Execution Modes section, compatibility matrix, session management
- ❌ skills/tk-workflow/SKILL.md - Missing
- ❌ tests/tk-implement/flag-matrix.md - Missing

### Files That Exist
- prompts/tf-implement.md (570 lines, fully implemented)
- README.md (execution modes documented)
- .tf/knowledge/topics/interactive-shell-modes.md (integration pattern reference)

### Files That Do NOT Exist (Per Plan)
- skills/tk-workflow/SKILL.md
- tests/tk-implement/flag-matrix.md
- model-test-output.md (referenced in Implementation Plan but not required as a persistent file)

### Scout-Context Accuracy
The scout-context.md finding that "The plan is ALREADY IMPLEMENTED" is **partially correct** - the core functionality is implemented, but two documentation/testing deliverables from the Implementation Plan are missing.
