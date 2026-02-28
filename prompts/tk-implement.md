---
description: Analyze and implement any tk ticket with appropriate depth and subagents
---

Implement ticket from `$@` (parsed into `<TICKET_ID>` + flags) using dynamic subagent dispatch based on ticket analysis.

## Parse Input and Runtime Flags

Treat `$@` as raw input that may include a ticket id plus flags.

Supported flags:
- `--async` → run subagent execution in background mode (`async: true`)
- `--clarify` → open chain clarification TUI (`clarify: true`)

Parsing rules:
1. Extract `TICKET_ID` as the first non-flag token.
2. Set `RUN_ASYNC` and `RUN_CLARIFY` booleans from flags.
3. If `TICKET_ID` is missing, STOP and ask for a ticket id.
4. If both `--async` and `--clarify` are set, prefer async automation and force `RUN_CLARIFY = false` (log this decision).
5. Reject unknown flags with a short help message.

## Subagent Scope Guardrails (Critical)

- Use existing agents only.
- **NEVER** call `subagent` with management actions: `create`, `update`, or `delete`.
- Determine `AGENT_SCOPE` first, then use it consistently on every subagent execution call (single, chain, and parallel).
- Do a preflight check with `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}` to confirm required agents exist.
- If a required agent is missing, **STOP** and report which agent(s) are missing. Do not auto-create project agents.
- Do not write or modify `.pi/agents/*` as part of `/tk-implement`.

## Determine Agent Scope

Set `AGENT_SCOPE` before any subagent call:

1. If `.pi/agents/.tk-bootstrap.json` exists and indicates project-scoped install, set `AGENT_SCOPE = "project"`.
2. Otherwise set `AGENT_SCOPE = "user"`.
3. Optionally use `"both"` only when you intentionally want project agents to override user agents for same-name definitions.

Then use `AGENT_SCOPE` consistently in all subagent calls.

## Subagent Runtime Defaults (pi-subagents best practices)

Unless you explicitly need interactive preview/editing, use these execution defaults:

- `clarify: <RUN_CLARIFY>` (default false; true only with `--clarify`)
- `async: <RUN_ASYNC>` (default false; true with `--async`)
- `artifacts: true` (keep debug artifacts)
- `includeProgress: false` (avoid huge tool responses; rely on files)
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

Use chain features intentionally:
- Use `output` per step to persist key artifacts in `chainDir`
- Use `reads` per step to pass specific files instead of only `{previous}`
- Use template vars where helpful: `{task}`, `{previous}`, `{chain_dir}`

## Re-Anchor Context (Do this before implementation)

1. Set run paths:
   - `TICKET_ID = <TICKET_ID>`
   - `CHAIN_DIR = .subagent-runs/<TICKET_ID>`
   - `KNOWLEDGE_ROOT = .tf/knowledge`
2. Ensure directories exist:
   - `.subagent-runs/<TICKET_ID>`
   - `.tf`
   - `.tf/knowledge`
3. Read re-anchor docs if they exist:
   - `.tf/AGENTS.md` (lessons learned)
   - relevant files under `.tf/knowledge/**` for this ticket/topic
4. Build a short context summary from:
   - ticket details
   - dependencies
   - prior lessons from `.tf/AGENTS.md`
   - existing knowledge in `.tf/knowledge`
5. Start with fresh execution context for this ticket run and avoid relying on stale conversational state.

## Persistent Research Cache Behavior

Before running new web/library research:

1. Check existing knowledge first in `.tf/knowledge`:
   - ticket-specific notes (e.g. `.tf/knowledge/tickets/<TICKET_ID>/`)
   - topic notes (e.g. `.tf/knowledge/topics/**`)
2. Reuse existing knowledge if sufficient.
3. If gaps remain:
   - Use `researcher` for general best practices, docs, recent updates.
   - Use `librarian` for library internals/history requiring source-backed evidence/permalinks.
4. After new research, persist distilled results to `.tf/knowledge` (not just temp chain files), and reference sources clearly.
5. Require researcher/librarian outputs to include a `Knowledge Pack` YAML section and use it to decide what to persist.

## Knowledge Persistence Templates (Use after research/librarian)

When `knowledge_pack.reusable = true`, persist/update these files.

### 1) Topic file
Path: `.tf/knowledge/topics/<topic-slug>.md`

```markdown
# Topic: <topic-slug>

## Reusable Summary
<2-3 sentence reusable summary>

## Reusable Insights
- <insight 1>
- <insight 2>

## Canonical Sources
- <url or permalink>
- <url or permalink>

## Last Updated
- ticket: <ticket-id>
- date: <ISO timestamp>
```

### 2) Ticket research file
Path: `.tf/knowledge/tickets/<ticket-id>/research.md`

```markdown
# Research Cache: <ticket-id>

## Topics Linked
- <topic-slug-1>
- <topic-slug-2>

## Delta (What was new vs existing knowledge)
- <new point 1>
- <new point 2>

## Sources Used
- <url/permalink>

## Reuse Decision
- reusable: true|false
- reason: <if false, why>
```

### 3) Optional index update
Path: `.tf/knowledge/index.md`

Append (or update existing entry) in this format:

```markdown
- <topic-slug>: .tf/knowledge/topics/<topic-slug>.md (updated by <ticket-id> on <date>)
```

Persistence rules:
- Prefer updating existing topic files over creating near-duplicates.
- Keep only durable, reusable knowledge in topic files.
- Put ticket-specific details in `.tf/knowledge/tickets/<ticket-id>/research.md`.
- If `knowledge_pack.reusable = false`, do not create/update topic files; only write a minimal ticket cache note with the reason.

## 1. Read and Analyze the Ticket

Read the ticket file (typically `.tickets/<TICKET_ID>.md` or find it with `find . -name "<TICKET_ID>.md" 2>/dev/null`):

- **Title/Description**: What needs to be done?
- **Tags/Type**: Any type indicators (code, config, workflow, frontend, etc.)
- **Dependencies**: What must be done first? (check if they're complete)
- **Complexity indicators**:
  - Simple: Config changes, scaffolding, small fixes, documentation
  - Medium: New features, integrations, workflows, UI components
  - Complex: AI systems, API clients, novel algorithms, system architecture, performance-critical code

## 2. Quick Codebase Scout

Use `subagent` with scout (`agentScope: "<AGENT_SCOPE>"`, `chainDir: ".subagent-runs/<TICKET_ID>"`) to understand current state relevant to the ticket:
- Find existing related files and patterns
- Understand the project structure and conventions
- Locate similar implementations
- Identify test structure if any

Note: all path templates include `scout` as the first chain step. If you already ran scout manually here, reuse that output and avoid duplicate scouting.

## 3. Decide Implementation Path

Based on ticket + re-anchor + scout results, choose depth.

**Re-anchoring requirement across all paths:** run `context-builder` immediately after `scout` before implementation.

### Path A: Minimal (scout → context-builder → worker → reviewer → tk-closer)
**Use when:**
- Simple configuration changes
- Scaffold or setup tasks
- Small, isolated fixes
- Documentation updates
- Clear implementation with no unknowns

**Flow:**
```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": ".subagent-runs/<TICKET_ID>",
  "clarify": <RUN_CLARIFY>,
  "async": <RUN_ASYNC>,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    { "agent": "scout", "task": "Scout codebase context for ticket <TICKET_ID> and summarize relevant files/patterns/tests.", "output": "scout-context.md" },
    { "agent": "context-builder", "task": "Build re-anchored implementation context for ticket <TICKET_ID> using scout output and project knowledge. Include constraints from .tf/AGENTS.md and .tf/knowledge if present.", "reads": ["scout-context.md"], "output": "anchor-context.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID>. Context: {previous}", "reads": ["anchor-context.md"], "output": "implementation.md" },
    { "agent": "reviewer", "task": "Review implementation for ticket <TICKET_ID>. Context: {previous}", "reads": ["implementation.md"], "output": "review.md" },
    { "agent": "tk-closer", "task": "Commit and close gate for ticket <TICKET_ID>.", "reads": ["implementation.md", "review.md"], "output": "close-summary.md" }
  ]
}
```

Optional per-step override hints (apply in any path):

```json
{ "agent": "worker", "model": "anthropic/claude-sonnet-4-5", "skill": "safe-bash,python-testing" }
```


### Path B: Standard (scout → context-builder → optional research/librarian → planner → worker → reviewer → tester → tk-closer)
**Use when:**
- New features requiring some research
- Integration with external services or APIs
- Medium complexity with some unknowns
- Workflow or automation tasks
- UI components or frontend features

**Flow (with research):**
```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": ".subagent-runs/<TICKET_ID>",
  "clarify": <RUN_CLARIFY>,
  "async": <RUN_ASYNC>,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    { "agent": "scout", "task": "Scout codebase context for ticket <TICKET_ID> and summarize relevant files/patterns/tests.", "output": "scout-context.md" },
    { "agent": "context-builder", "task": "Build re-anchored implementation context for ticket <TICKET_ID> using scout output and project knowledge.", "reads": ["scout-context.md"], "output": "anchor-context.md" },
    { "agent": "researcher", "task": "Research best practices for ticket <TICKET_ID> based on anchor context. Reuse .tf/knowledge first; only fill gaps.", "reads": ["anchor-context.md"], "output": "research.md" },
    { "agent": "planner", "task": "Create implementation plan for ticket <TICKET_ID>. Integrate anchored context + research.", "reads": ["anchor-context.md", "research.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    { "agent": "reviewer", "task": "Review implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
    { "agent": "tester", "task": "Test implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md", "review.md"], "output": "test-results.md" },
    { "agent": "tk-closer", "task": "Commit and close gate for ticket <TICKET_ID>.", "reads": ["implementation.md", "review.md", "test-results.md"], "output": "close-summary.md" }
  ]
}
```

If no knowledge gaps remain after re-anchor/scout, skip researcher/librarian steps.
If library internals are part of the gap, add `librarian` after `context-builder` (or run `researcher` + `librarian` in parallel) before `planner`.

Parallel research insertion example:

```json
{
  "parallel": [
    { "agent": "researcher", "task": "Best-practice/documentation research for <TICKET_ID>", "reads": ["anchor-context.md"], "output": "research.md" },
    { "agent": "librarian", "task": "Source-backed library internals for <TICKET_ID>", "reads": ["anchor-context.md"], "output": "library-research.md" }
  ]
}
```

### Path C: Deep (scout → context-builder → parallel research → planner → worker → parallel validation → fixer → documenter → tk-closer)
**Use when:**
- Complex AI systems or algorithms
- Library-heavy implementation (new frameworks, complex dependencies)
- Performance-critical code
- Novel domain requiring deep research
- Multiple interdependent components
- Public API design

**Flow:**
1. scout (local codebase recon)
2. context-builder (re-anchor + synthesize constraints/context)
3. PARALLEL research as needed:
   - librarian (library internals/history)
   - researcher (patterns/best practices/recent updates)
4. planner (integrate findings into plan)
5. worker (implement)
6. PARALLEL: reviewer (static analysis) + tester (behavior validation)
7. fixer (resolve critical/major issues)
8. documenter (API docs/examples if public interface)
9. tk-closer (commit + ticket close/status gate)

Use `agentScope: "<AGENT_SCOPE>"` and `chainDir: ".subagent-runs/<TICKET_ID>"` for all Path C subagent calls.

Reusable chain presets installed by `/tk-bootstrap`:
- `tk-path-a.chain.md`
- `tk-path-b.chain.md`
- `tk-path-c.chain.md`

Use these as starting templates and override step `model`/`skill` as needed via clarify or by editing chain files.

Recommended Path C chain shape:

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": ".subagent-runs/<TICKET_ID>",
  "clarify": <RUN_CLARIFY>,
  "async": <RUN_ASYNC>,
  "artifacts": true,
  "includeProgress": false,
  "chain": [
    { "agent": "scout", "task": "Scout codebase context for ticket <TICKET_ID>.", "output": "scout-context.md" },
    { "agent": "context-builder", "task": "Build re-anchored implementation context for ticket <TICKET_ID>.", "reads": ["scout-context.md"], "output": "anchor-context.md" },
    { "parallel": [
      { "agent": "researcher", "task": "Research external best practices for <TICKET_ID>", "reads": ["anchor-context.md"], "output": "research.md" },
      { "agent": "librarian", "task": "Research source-backed library internals for <TICKET_ID>", "reads": ["anchor-context.md"], "output": "library-research.md" }
    ], "concurrency": 2, "failFast": false },
    { "agent": "planner", "task": "Create implementation plan for ticket <TICKET_ID>.", "reads": ["anchor-context.md", "research.md", "library-research.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    { "parallel": [
      { "agent": "reviewer", "task": "Review implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
      { "agent": "tester", "task": "Test implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "test-results.md" }
    ], "concurrency": 2, "failFast": false },
    { "agent": "fixer", "task": "Fix critical/major issues for ticket <TICKET_ID>.", "reads": ["review.md", "test-results.md", "implementation.md"], "output": "fixes.md" },
    { "agent": "documenter", "task": "Document externally visible changes for ticket <TICKET_ID>.", "reads": ["implementation.md", "review.md", "fixes.md"], "output": "docs-update.md" },
    { "agent": "tk-closer", "task": "Commit and close gate for ticket <TICKET_ID>.", "reads": ["implementation.md", "review.md", "test-results.md", "fixes.md", "docs-update.md"], "output": "close-summary.md" }
  ]
}
```

## 4. Execute and Report

Use `subagent` tool with the chosen path and:
- `agentScope: "<AGENT_SCOPE>"`
- `chainDir: ".subagent-runs/<TICKET_ID>"`
- `clarify: <RUN_CLARIFY>`
- `async: <RUN_ASYNC>`
- execution mode only (no management actions)

After completion:

1. **Summarize what was done**
2. **List files changed**
3. **Note blockers/decisions**
4. **Persist new research** to `.tf/knowledge` if research/librarian produced new findings
5. **Append progress entry** to `.tf/progress.md`
6. **Conditionally append lessons learned** to `.tf/AGENTS.md` (strict rules below)
7. **Commit changes and close/update ticket** using the gate below

## Git Commit and Ticket Closure Gate (Executed by `tk-closer`)

This gate should be executed by the final `tk-closer` chain step.

### A) Commit changes

1. Verify repository state:
   - run `git rev-parse --is-inside-work-tree`
   - run `git status --short`
2. Stage relevant changes (implementation + docs/knowledge/progress updates for this run).
3. Commit with message:
   - `<TICKET_ID>: <short summary>`
4. If there are no changes to commit, report that explicitly.

### B) Add ticket implementation note

Before closing/status update, add a concise ticket note with:
- implementation summary
- key files changed
- test/validation results
- commit hash (if available)

Use:
- `tk add-note <TICKET_ID> "..."`
- or pipe multiline markdown/text into `tk add-note <TICKET_ID>`

### C) Decide ticket closure

Close ticket **only if all are true**:
- dependency checks passed
- implementation is complete for ticket scope
- reviewer/tester results indicate no blocking issues (no unresolved critical/major failures)
- required validation/tests for this ticket passed

Then run:
- `tk close <TICKET_ID>`

If any condition fails, do **not** close. Instead run:
- `tk status <TICKET_ID> in-progress`

If actively blocked by external dependency or missing input, use blocked status if your `tk` setup supports it; otherwise keep `in-progress` and report blockers.

### D) Async mode behavior

If `RUN_ASYNC = true`, the same gate still runs inside the background chain via `tk-closer`.
From the initiating turn, you should:
- return run id/status immediately
- state that commit/close will be performed by `tk-closer` when the async chain reaches the final step
- remind to verify completion with `subagent_status`

## Progress Tracking (Required)

Append one entry to `.tf/progress.md` per run, including:
- timestamp
- ticket id
- status (`in-progress` / `blocked` / `done`)
- short summary
- key files changed
- test result summary
- chain artifacts path: `.subagent-runs/<TICKET_ID>`
- commit hash (if committed)
- note command executed (`tk add-note ...`)
- ticket command executed (`tk close ...` or `tk status ...`)

## Lessons Learned Update (Strict)

When considering updates to `.tf/AGENTS.md`:

Add a lesson **only if BOTH are true**:
1. **New**: not already captured in `.tf/AGENTS.md` (check for semantic duplicates)
2. **Useful**: likely to improve future ticket implementations (reusable pattern, gotcha, reliability/security/perf insight)

Do **not** add:
- ticket-specific trivia
- obvious/general advice
- duplicates or near-duplicates

If no qualifying lesson exists, skip this step explicitly.

## Decision Rules

| Factor | Minimal | Standard | Deep |
|--------|---------|----------|------|
| Lines of code estimate | <50 | 50-200 | >200 |
| External libraries | None/standard | 1-2 new | Multiple or complex |
| Unknowns/Research needed | None | Some | Significant |
| Type of work | Config, docs, fixes | Features, integrations | Systems, agents, APIs |
| Testing critical | Nice-to-have | Should have | Must have |
| Public API surface | No | Maybe | Yes |

## Safety Checks

- If dependencies are incomplete → STOP and report
- If ticket is unclear → Ask for clarification before proceeding
- If scout reveals unexpected complexity → Escalate to deeper path
- If no tests exist for code changes → Flag this as technical debt
- If `.pi/agents` contains overlapping names, still use `agentScope: "<AGENT_SCOPE>"` and do not modify project agents
- If `.tf/AGENTS.md` or `.tf/knowledge` is missing, continue but create minimal structure as needed

## Example Usage

```
/tk-implement TICKET-123
/tk-implement TICKET-123 --async
/tk-implement TICKET-123 --clarify
```