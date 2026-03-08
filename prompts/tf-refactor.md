---
description: Refactor code with project-aware context, explicit scope, and behavior-preserving validation
model: glm-5
thinking: medium
---

Refactor from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--from <path>` optional seed notes / refactor brief
- `--scope <path-or-glob>` optional path constraint to emphasize target files or directories
- `--fast` (default)
- `--thorough`
- `--preserve-api` emphasize public API stability
- `--prepare-for <goal>` describe the future work this refactor enables
- `--async` run execution chain in background
- `--clarify` open chain clarification UI

Rules:
1. Remaining non-flag text is `TARGET`.
2. If `TARGET` is empty, STOP and ask for a goal or ticket id.
3. If both `--fast` and `--thorough` are present, STOP and ask the user to choose one.
4. Default mode is `fast`.
5. If both `--async` and `--clarify` are present, prefer async and set clarify=false.
6. Reject unknown flags with a short help message.

## 1) Determine Input Mode and Paths

Determine whether this is:
- **Ticket mode**: if `.tickets/<TARGET>.md` exists
- **Goal mode**: otherwise, treat `TARGET` as freeform refactor goal text

Set:
- `MODE = ticket|goal`
- `RUN_ID = <ticket-id>` in ticket mode, otherwise kebab-case of `TARGET`
- `CHAIN_DIR = .subagent-runs/tf-refactor/<RUN_ID>`
- `SEED_FILE = <CHAIN_DIR>/refactor-seed.json`
- `TARGET_TOPIC_DIR = .tf/knowledge/topics/<RUN_ID>`

Ensure directories exist:
- `.subagent-runs/tf-refactor`
- `<CHAIN_DIR>`
- `.tf/knowledge/topics`
- `<TARGET_TOPIC_DIR>`

If `--from` is provided, verify the file exists before proceeding.

## 2) Build Seeded Inputs

Write `<SEED_FILE>` with:
```json
{
  "mode": "ticket|goal",
  "target": "<TARGET>",
  "scope": "<SCOPE_OR_EMPTY>",
  "from_path": "<FROM_PATH_OR_NULL>",
  "preserve_api": true,
  "prepare_for": "<PREPARE_FOR_OR_EMPTY>",
  "speed_profile": "fast|thorough",
  "summary": "One-line description of the refactor objective"
}
```

If `--from` is set:
1. Read the file.
2. Write `<CHAIN_DIR>/from-seed.md` with its content (or concise extracted sections if large).
3. Set `SEED_READS = ["refactor-seed.json", "from-seed.md"]`.

Otherwise:
- `SEED_READS = ["refactor-seed.json"]`

## 3) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tf-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight with `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
- Required baseline agents:
  - `scout`
  - `context-builder`
  - `plan-fast`
  - `plan-deep`
  - `refactorer`
  - `reviewer`
  - `tester`
  - `fixer`
  - `documenter`
- Optional optimization agent:
  - `context-merger`
- Ticket mode additionally requires:
  - `tf-closer`
- If any required agent is missing, STOP and report missing names.
- Set `HAS_CONTEXT_MERGER=true|false` based on preflight.

## 4) Phase 1 (always sync): Build Anchored Refactor Context

Use runtime defaults:
- `clarify: false`
- `async: false`
- `artifacts: true`
- `includeProgress: false`
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

### Preferred phase-1 chain (when `HAS_CONTEXT_MERGER=true`)

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": "<CHAIN_DIR>",
  "clarify": false,
  "async": false,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    {
      "parallel": [
        {
          "agent": "scout",
          "task": "Scout codebase context for refactor target '<TARGET>'. Read refactor-seed.json FIRST. Focus on structural boundaries, affected files, relevant tests, and public API seams. Respect --scope when present.",
          "reads": <SEED_READS>,
          "output": "scout-context.md"
        },
        {
          "agent": "context-builder",
          "task": "Build anchored refactor context for '<TARGET>'. Read refactor-seed.json FIRST. Read PROJECT.md when present, use AGENTS.md for repo operating guidance, include lessons from .tf/AGENTS.md plus relevant .tf/knowledge, and emphasize behavior-preservation constraints. If from-seed.md exists, synthesize it.",
          "reads": <SEED_READS>,
          "output": "anchor-context-base.md"
        }
      ],
      "concurrency": 2,
      "failFast": false
    },
    {
      "agent": "context-merger",
      "task": "Merge scout-context.md and anchor-context-base.md into anchor-context.md. Preserve all anchor sections and append scoped code context.",
      "reads": ["scout-context.md", "anchor-context-base.md"],
      "output": "anchor-context.md"
    }
  ]
}
```

### Fallback phase-1 chain

Same as above, but use `context-builder` for the final merge step.

After the run, ensure `anchor-context.md` exists in `<CHAIN_DIR>`. If needed, locate it under a session subdirectory and copy it to `<CHAIN_DIR>/anchor-context.md`.

## 5) Phase 2: Plan + Execute + Validate

Use:
- `clarify: <RUN_CLARIFY>`
- `async: <RUN_ASYNC>`
- `artifacts: true`
- `includeProgress: false`
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

Choose planning depth:
- `plan-fast` when `--fast`
- `plan-deep` when `--thorough`

### Ticket mode chain

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": "<CHAIN_DIR>",
  "clarify": <RUN_CLARIFY>,
  "async": <RUN_ASYNC>,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    { "agent": "<PLAN_AGENT>", "task": "Create a behavior-preserving refactor plan for '<TARGET>'. Respect PROJECT.md, AGENTS.md, the anchor context, and any --scope / --preserve-api constraints.", "reads": ["anchor-context.md"], "output": "plan.md" },
    { "agent": "refactorer", "task": "Execute the refactor for '<TARGET>' according to plan.md. Preserve behavior, keep public APIs stable unless explicitly permitted, and constrain changes to the intended scope.", "reads": ["anchor-context.md", "plan.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Initial review for refactor target '<TARGET>'. Review only the changes introduced by this refactor. Focus on behavior preservation, API stability, regressions, and scope control.", "reads": ["implementation.md", "plan.md", "anchor-context.md"], "output": "review.md" },
        { "agent": "tester", "task": "Run the most relevant tests and checks for refactor target '<TARGET>'. Prioritize changed modules, public interfaces, and the highest-signal validations available.", "reads": ["implementation.md", "plan.md", "anchor-context.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Apply one fix pass for refactor target '<TARGET>'. Prioritize test failures first, then critical/major review findings. Preserve the intended refactor scope.", "reads": ["implementation.md", "review.md", "test-results.md", "plan.md", "anchor-context.md"], "output": "fixes.md" },
    { "agent": "reviewer", "task": "Quick re-check for refactor target '<TARGET>'. Review only the changed files and hunks touched by implementation and fixes. State clearly whether behavior preservation and scope control are an unambiguous pass.", "reads": ["implementation.md", "review.md", "test-results.md", "fixes.md", "plan.md", "anchor-context.md"], "output": "review-post-fix.md" },
    { "agent": "tf-closer", "task": "Finalize ticket <TARGET>: git commit, progress tracking, lessons learned, ticket artifact copy, and ticket close gate. maxFixPasses=1 per run. If the quick re-check is anything other than a clear pass, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md"], "output": "close-summary.md" }
  ]
}
```

### Goal mode chain

Same chain, but replace the final `tf-closer` step with:

```json
{ "agent": "documenter", "task": "Write close-summary.md for refactor target '<TARGET>'. Summarize what changed, what validations ran, whether behavior preservation looks clear, and what follow-up work (if any) remains.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md"], "output": "close-summary.md" }
```

If async=true:
- Return run id/status immediately.
- State artifact path root `<CHAIN_DIR>`.
- Tell the user to check with `subagent_status`.

## 6) Final Response

When synchronous execution completes:
1. Report whether this was **ticket mode** or **goal mode**.
2. Report planning depth used (`fast` or `thorough`).
3. Summarize what was refactored and which files were affected.
4. Report validation outcome (review/test + quick re-check).
5. Point to `<CHAIN_DIR>` and `close-summary.md`.
6. If ticket mode, report final ticket status outcome.
