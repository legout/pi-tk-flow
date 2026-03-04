# Implementation Plan

## Goal
Implement command-level default model configuration for tk-flow (including `/tk-bootstrap` mapping), document a single canonical model-precedence ladder, and validate behavior with an executable pass/fail checklist while keeping agent-definition edits out of scope.

## Tasks
1. **Add optional extension docs + canonical command-to-model mapping**
   - File: `README.md`
   - Changes:
     - Add/refresh `pi-prompt-template-model` optional-extension section (install, behavior, fallback, restore, graceful degradation).
     - Add a single command-model mapping table that explicitly includes:
       - `/tk-bootstrap` → `claude-haiku-4-5`
       - `/tk-implement` → `claude-haiku-4-5, claude-sonnet-4-20250514`
       - `/tk-brainstorm` → `claude-sonnet-4-20250514`
       - `/tk-plan` → `claude-sonnet-4-20250514`
       - `/tk-plan-check` → `claude-haiku-4-5`
       - `/tk-plan-refine` → `claude-sonnet-4-20250514`
       - `/tk-ticketize` → `claude-haiku-4-5`
   - Acceptance:
     - Mapping table exists and includes `/tk-bootstrap` with `claude-haiku-4-5`.
     - README explicitly states behavior when extension is not installed.

2. **Apply prompt frontmatter model defaults for prompt-backed tk commands**
   - Files:
     - `prompts/tk-implement.md`
     - `prompts/tk-brainstorm.md`
     - `prompts/tk-plan.md`
     - `prompts/tk-plan-check.md`
     - `prompts/tk-plan-refine.md`
     - `prompts/tk-ticketize.md`
   - Changes:
     - Add `model:` frontmatter matching the mapping above.
     - Add `thinking:` only where materially useful (planning/brainstorm/refinement-heavy prompts).
     - Keep prompt bodies unchanged.
   - Acceptance:
     - All six prompt files have valid YAML frontmatter with `model:`.
     - Model values match the canonical mapping.

3. **Document the explicit 5-level model precedence ladder and subagent behavior**
   - Files:
     - `.tf/knowledge/topics/model-configuration.md` (new)
     - `README.md` (cross-link summary)
   - Changes:
     - Add one canonical precedence ladder (highest → lowest), exactly:
       1. `subagent` tool call `model` parameter (runtime override)
       2. Agent definition frontmatter `model`
       3. Main loop model (prompt frontmatter via extension)
       4. Project defaults (`.pi/settings.json`)
       5. Global defaults (`~/.pi/agent/settings.json`)
     - Add examples that distinguish main-loop command model selection from subagent model selection.
   - Acceptance:
     - Ladder appears verbatim in the knowledge doc.
     - README references the same ordering (no conflicting precedence text).

4. **Resolve scope contradiction by keeping agent-definition edits out of scope**
   - File: `.tf/plans/2026-03-04-default-models-for-commands/03-implementation-plan.md`
   - Changes:
     - Remove prior “audit/update `assets/agents/*.md`” implementation work.
     - State explicitly that agent definition changes are out of scope for this feature iteration.
   - Acceptance:
     - No `assets/agents/*.md` files appear in “Files to Modify” for this plan.
     - Scope now matches PRD out-of-scope constraints.

5. **Run executable validation checklist and record evidence**
   - File: `.tf/plans/2026-03-04-default-models-for-commands/04-progress.md` (create or append)
   - Changes:
     - Execute and record the following checks:

       **A. Static file checks**
       - `grep -n '^model:' prompts/tk-implement.md prompts/tk-brainstorm.md prompts/tk-plan.md prompts/tk-plan-check.md prompts/tk-plan-refine.md prompts/tk-ticketize.md`
       - `grep -n '/tk-bootstrap' README.md`
       - `grep -n 'subagent tool call `model` parameter' .tf/knowledge/topics/model-configuration.md`
       - `grep -n 'Agent definition frontmatter `model`' .tf/knowledge/topics/model-configuration.md`
       - `grep -n 'Main loop model' .tf/knowledge/topics/model-configuration.md`
       - `grep -n '.pi/settings.json' .tf/knowledge/topics/model-configuration.md`
       - `grep -n '~/.pi/agent/settings.json' .tf/knowledge/topics/model-configuration.md`

       **B. Runtime checks with extension installed**
       - `pi install npm:pi-prompt-template-model`
       - Start `pi`, then run:
         - `/model anthropic/claude-opus-4-5` (set known baseline)
         - `/tk-plan default-models-smoke`
         - `/tk-plan-check .tf/plans/2026-03-04-default-models-for-commands`
         - `/tk-bootstrap --scope project --dry-run`
       - Capture notifications/status text in `04-progress.md`.

       **C. Graceful degradation checks (extension disabled/uninstalled)**
       - Disable or uninstall extension in local environment.
       - Start `pi`, run `/tk-plan default-models-smoke-no-ext`.
       - Record that command still executes without model-switch failures.

     - Pass/Fail criteria:
       - PASS if all six prompt files include expected `model:` values.
       - PASS if README mapping includes `/tk-bootstrap` → `claude-haiku-4-5`.
       - PASS if precedence ladder includes all 5 levels in correct order.
       - PASS if extension-on run shows expected switch/restore behavior for prompt-backed commands.
       - PASS if extension-off run still executes tk commands without regression.

## Files to Modify
- `README.md` - optional extension docs, canonical command→model mapping (including `/tk-bootstrap`), precedence summary link.
- `prompts/tk-implement.md` - add `model` (and optional `thinking`).
- `prompts/tk-brainstorm.md` - add `model` (and optional `thinking`).
- `prompts/tk-plan.md` - add `model` (and optional `thinking`).
- `prompts/tk-plan-check.md` - add `model`.
- `prompts/tk-plan-refine.md` - add `model` (and optional `thinking`).
- `prompts/tk-ticketize.md` - add `model`.
- `.tf/plans/2026-03-04-default-models-for-commands/04-progress.md` - validation evidence and pass/fail outcomes.

## New Files (if any)
- `.tf/knowledge/topics/model-configuration.md` - canonical precedence ladder, subagent/main-loop guidance, example configurations.

## Dependencies
- Task 1 establishes the canonical mapping; Task 2 and Task 3 must align to it.
- Task 2 and Task 3 must complete before Task 5 runtime verification.
- Task 4 (scope lock) must be finalized before ticket split to avoid contradictory implementation work.

## Risks
- `/tk-bootstrap` is extension-command based (not prompt-backed), so mapping must be clearly documented to avoid ambiguity.
- Missing API keys may trigger fallback paths and confuse validation if not captured explicitly.
- Inconsistent precedence wording across docs can reintroduce ambiguity; keep one canonical ladder text.