# Plan Gaps: Default Models for Commands

## Verdict
- **Ready for ticketization:** no
- **Reason:** Two critical gaps (GAP-001, GAP-002) and a scope contradiction must be resolved before ticketization. Task 5 lacks concrete validation criteria.

## Gap Summary
- Critical: 2
- Major: 2
- Minor: 0

---

## Gaps

### 1. [Critical] GAP-001: Subagent Model Precedence Ladder Incomplete
- **Where:** `02-spec.md` (Model Precedence section in knowledge base documentation)
- **Issue:** The spec states "runtime overrides in subagent tool calls take precedence" but the precedence hierarchy between (a) subagent tool call `model` parameter, (b) agent definition frontmatter `model` field, (c) main loop model from extension switch, and (d) project/global defaults is not explicitly documented as a clear ladder.
- **Impact:** Implementers may misunderstand which model takes effect in complex scenarios (e.g., a subagent call with runtime override when the main loop was switched by the extension). This could lead to unexpected model selection and cost/quality issues.
- **Recommended fix:** Add explicit precedence ladder to spec:
  1. `subagent` tool call `model` parameter (runtime override) — highest
  2. Agent definition frontmatter `model` field
  3. Main loop model (from prompt frontmatter via extension)
  4. Project settings (`.pi/settings.json`)
  5. Global settings (`~/.pi/agent/settings.json`) — lowest
- **Blocks ticketization?:** yes

### 2. [Critical] GAP-002: Missing `/tk-bootstrap` Command Model Mapping
- **Where:** `00-design.md` (Component Contracts table), `02-spec.md` (Prompt Template Modifications table)
- **Issue:** All 6 commands have model mappings EXCEPT `/tk-bootstrap`. The Design doc and Spec list exactly 6 commands (tk-implement, tk-brainstorm, tk-plan, tk-plan-check, tk-plan-refine, tk-ticketize) but `/tk-bootstrap` is also a user-facing tk command that runs setup/installation.
- **Impact:** Inconsistent user experience—users running `/tk-bootstrap` won't benefit from model optimization even though it's part of the tk-flow command suite.
- **Recommended fix:** Add `/tk-bootstrap` to all model mapping tables. Suggested mapping: `claude-haiku-4-5` (fast, low-cost setup command). Add to Task 2 in implementation plan.
- **Blocks ticketization?:** yes

### 3. [Major] GAP-003: Scope Contradiction on Agent Definition Edits
- **Where:** `01-prd.md` (Out of Scope #3) vs `03-implementation-plan.md` (Task 4)
- **Issue:** PRD explicitly states "Modifying agent definition files" is Out of Scope, citing "per tk-implement guardrails." However, Implementation Plan Task 4 is "Audit and update agent definitions where clearly beneficial" with specific files listed (`assets/agents/planner.md`, etc.).
- **Impact:** Confusion for implementers about whether agent edits are in scope. If Task 4 proceeds, it violates PRD scope; if skipped, planned agent tuning doesn't happen.
- **Recommended fix:** Choose one:
  - **Option A:** Remove Task 4 from implementation plan and keep agent edits out of scope (remove from Files to Modify list)
  - **Option B:** Update PRD to bring agent definition edits into scope, with clear rationale for why this exception to tk-implement guardrails is acceptable
- **Blocks ticketization?:** no (can proceed with either resolution)

### 4. [Major] GAP-004: Task 5 Validation Not Ticket-Ready
- **Where:** `03-implementation-plan.md` (Task 5)
- **Issue:** Task 5 says "Run manual checks" but lacks:
  - Concrete shell commands to run for each scenario
  - Specific test fixtures or expected inputs
  - Explicit pass/fail criteria
  - How to verify "model restore after command completion"
- **Impact:** Implementers won't know exactly how to validate or what constitutes success. Task cannot be executed consistently.
- **Recommended fix:** Make Task 5 ticket-ready by adding:
  - Commands: `pi --version` (check extension installed), `/tk-implement TEST-123` (trigger model switch), etc.
  - Verification steps: check notification logs, verify model in status bar, etc.
  - Pass criteria: e.g., "Model switch notification appears within 2 seconds", "Previous model restored after command completion"
  - Test fixtures: create dummy ticket files for testing
- **Blocks ticketization?:** no (can refine during implementation, but should be improved)

---

## Quick Fix Plan

1. **Fix GAP-002 first** (easiest): Add `/tk-bootstrap` with `claude-haiku-4-5` to all model mapping tables in Design and Spec docs; update Task 2 file list

2. **Fix GAP-001**: Add explicit 5-level precedence ladder to `02-spec.md` Model Precedence section and knowledge base documentation

3. **Resolve GAP-003**: Decide on Option A or B and update PRD or Implementation Plan accordingly

4. **Improve GAP-004**: Add concrete validation commands and pass/fail criteria to Task 5

5. **Re-review**: After fixes, plan should be ready for ticketization

---

## Cross-Reference

| Gap | Affects Task | Priority |
|-----|--------------|----------|
| GAP-001 | Task 3 (knowledge docs) | Critical |
| GAP-002 | Task 2 (prompt updates) | Critical |
| GAP-003 | Task 4 (agent audit) | Major |
| GAP-004 | Task 5 (validation) | Major |
