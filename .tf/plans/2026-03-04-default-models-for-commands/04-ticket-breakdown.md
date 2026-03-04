# Ticket Breakdown

## Parent Epic
- Title: Add per-command model configuration via pi-prompt-template-model
- Goal: Deliver documented, command-level default model behavior across tk-flow by aligning README guidance, prompt frontmatter defaults, and canonical precedence docs, then validating extension-on and extension-off behavior with recorded evidence.

## Proposed Slices
1. Canonical README mapping + optional extension guidance
   - Type: AFK
   - Blocked by: none
   - Scope: Update README with one authoritative command→model table (including `/tk-bootstrap`) and clear optional-extension behavior (switch, restore, fallback, graceful degradation).
   - Acceptance:
     - [ ] README includes `pi-prompt-template-model` install and behavior notes (switch, restore, fallback).
     - [ ] README contains one canonical command→model table with all required commands, including `/tk-bootstrap` → `claude-haiku-4-5`.
     - [ ] README explicitly states tk commands still run normally when the extension is not installed.
     - [ ] README wording is positioned as canonical source for downstream prompt/docs alignment.
   - Source links:
     - PRD: Solution; Implementation Decisions ID-1, ID-2
     - Spec: Components §2 (Extension Dependency Documentation)
     - Plan: Task 1

2. Prompt frontmatter model defaults for tk commands
   - Type: AFK
   - Blocked by: S1
   - Scope: Add `model:` (and selective `thinking:` where useful) to the six prompt-backed tk command templates while leaving prompt bodies unchanged.
   - Acceptance:
     - [ ] `prompts/tk-implement.md` has `model: claude-haiku-4-5, claude-sonnet-4-20250514`.
     - [ ] `prompts/tk-brainstorm.md`, `prompts/tk-plan.md`, `prompts/tk-plan-refine.md` use `claude-sonnet-4-20250514` with optional purposeful `thinking:`.
     - [ ] `prompts/tk-plan-check.md` and `prompts/tk-ticketize.md` use `model: claude-haiku-4-5`.
     - [ ] All six frontmatter blocks remain valid YAML; prompt bodies remain semantically unchanged.
   - Source links:
     - PRD: User Stories US-1, US-2; Implementation Decisions ID-2, ID-3
     - Spec: Components §1 (Prompt Template Modifications)
     - Plan: Task 2

3. Canonical model precedence knowledge topic + README cross-link
   - Type: AFK
   - Blocked by: S1
   - Scope: Create `.tf/knowledge/topics/model-configuration.md` with the explicit 5-level precedence ladder and examples separating main-loop model selection from subagent overrides; cross-link from README.
   - Acceptance:
     - [ ] Knowledge topic is created at `.tf/knowledge/topics/model-configuration.md`.
     - [ ] The 5-level precedence ladder appears exactly in required highest→lowest order.
     - [ ] Examples clearly distinguish `subagent` runtime `model` overrides vs main-loop prompt-frontmatter model behavior.
     - [ ] README references this topic and uses the same precedence ordering with no contradictory text.
   - Source links:
     - PRD: User Stories US-4, US-5; Implementation Decisions ID-4
     - Spec: Components §3 (Knowledge Base Documentation)
     - Plan: Task 3

4. Executable validation pass + evidence capture
   - Type: AFK
   - Blocked by: S2, S3
   - Scope: Execute static checks, extension-enabled runtime checks, and extension-disabled graceful-degradation checks; capture outputs and PASS/FAIL criteria in `04-progress.md`.
   - Acceptance:
     - [ ] `.tf/plans/2026-03-04-default-models-for-commands/04-progress.md` is created/appended with evidence for all required static grep checks.
     - [ ] Runtime checks with extension installed are executed and recorded, including switch/restore observations for representative commands.
     - [ ] Graceful degradation run (extension disabled/uninstalled) is executed and recorded, confirming tk commands still run without model-switch failures.
     - [ ] Final PASS/FAIL section evaluates all required criteria (prompt models, README mapping, 5-level ladder, extension-on behavior, extension-off behavior).
   - Source links:
     - PRD: Testing Decisions TD-1..TD-5
     - Spec: Testing Strategy; Graceful Degradation flow
     - Plan: Task 4 (validation checklist)

## Dependency Graph
- S1 -> S2
- S1 -> S3
- S2 -> S4
- S3 -> S4

## Review Questions
- Granularity right?
- Any slice to split/merge?
- Dependency corrections?
