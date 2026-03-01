---
description: Analyze and implement any tk ticket with main-agent path selection
---

Implement ticket from `$@` (parsed into `<TICKET_ID>` + flags).

**Key principle:** The main agent (you) analyzes `anchor-context.md` after the scout/context-builder chain and decides which implementation path to use. All anchoring (ticket, lessons, knowledge) is handled by context-builder.

## Parse Input and Runtime Flags

Treat `$@` as raw input that may include a ticket id plus flags.

Supported flags:
- `--async` → run subagent execution in background mode (`async: true`)
- `--clarify` → open chain clarification TUI (`clarify: true`)

Parsing rules:
1. Extract `TICKET_ID` as the first non-flag token.
2. Set `RUN_ASYNC` and `RUN_CLARIFY` booleans from flags.
3. If `TICKET_ID` is missing, STOP and ask for a ticket id.
4. If both `--async` and `--clarify` are set, prefer async and set clarify=false.
5. Reject unknown flags with a short help message.

## Subagent Scope Guardrails (Critical)

- Use existing agents only.
- **NEVER** call `subagent` with management actions: `create`, `update`, or `delete`.
- Determine `AGENT_SCOPE` first, then use it consistently on every subagent execution call (single, chain, and parallel).
- Baseline preflight before any run:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required baseline agents: `scout`, `context-builder`, `worker`, `reviewer`, `tk-closer`
- Path-specific preflight before executing chosen path:
  - Path A: baseline only
  - Path B: baseline + `planner`, `tester`
  - Path C with research: baseline + `planner`, `tester`, `fixer`, `researcher`, `librarian`
  - Path C without new research: baseline + `planner`, `tester`, `fixer`
- If a required agent is missing, **STOP** and report which agent(s) are missing.
- Do not write or modify `.pi/agents/*` as part of `/tk-implement`.

## Determine Agent Scope

1. If `.pi/agents/.tk-bootstrap.json` exists → `AGENT_SCOPE = "project"`
2. Otherwise → `AGENT_SCOPE = "user"`
3. Use `"both"` only when intentionally overriding user agents with project agents.

## Subagent Runtime Defaults

- `clarify: <RUN_CLARIFY>` (default false)
- `async: <RUN_ASYNC>` (default false)
- `artifacts: true`
- `includeProgress: false`
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

## 1. Scout + Context-Builder (Anchoring Chain)

Ensure `.subagent-runs/<TICKET_ID>` directory exists, then run:

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": ".subagent-runs/<TICKET_ID>",
  "clarify": false,
  "async": false,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    {
      "agent": "scout",
      "task": "Scout codebase context for ticket <TICKET_ID>. Focus on relevant files, patterns, tests, and architecture.",
      "output": "scout-context.md"
    },
    {
      "agent": "context-builder",
      "task": "Build re-anchored implementation context for ticket <TICKET_ID>. You MUST: 1) Read the ticket file (find with `find . -name \"<TICKET_ID>.md\"`), 2) Read `.tf/AGENTS.md` for lessons learned, 3) Read relevant `.tf/knowledge/**` files for cached research, 4) Synthesize with scout output. Output a structured `anchor-context.md` with: ticket summary, complexity assessment (simple/medium/complex), research gaps (if any), external libraries involved, testing requirements, and recommended implementation path (A/B/C).",
      "reads": ["scout-context.md"],
      "output": "anchor-context.md"
    }
  ]
}
```

The context-builder handles all anchoring: ticket reading, lessons from `.tf/AGENTS.md`, and cached knowledge from `.tf/knowledge/`.

## 2. YOU Decide the Implementation Path

Read `.subagent-runs/<TICKET_ID>/anchor-context.md` and decide based on:

| Factor | Path A (Minimal) | Path B (Standard) | Path C (Deep) |
|--------|------------------|-------------------|---------------|
| **Complexity** | Config, docs, small fixes | Features, integrations | AI, novel algorithms, library-heavy |
| **Research needed?** | No (existing knowledge sufficient) | Maybe (check knowledge first) | Yes (new domain/libraries) |
| **LOC estimate** | <50 | 50-200 | >200 |
| **Validation** | Review only | Review + Test (parallel) | Review + Test (parallel) |
| **Chain steps** | scout→context→worker→reviewer→closer | scout→context→planner→worker→**parallel review+test**→closer | scout→context→**parallel research**→planner→worker→**parallel review+test**→fixer→closer |

### Decision Rules

**Hard gate:** If `anchor-context.md` identifies unresolved knowledge gaps, unknown library behavior, or missing best-practice guidance, you **must** choose Path C and include research steps.

**Choose Path A when:**
- Ticket is configuration, documentation, or small isolated fix
- No external libraries needed
- Clear implementation path from existing code patterns
- No research gaps identified

**Choose Path B when:**
- New feature or integration
- Some complexity but within existing patterns
- Planning needed, but anchor context confirms no unresolved research gaps
- Sequential validation sufficient

**Choose Path C when:**
- Complex algorithms, AI systems, or novel domains
- Multiple new external libraries
- Research required (check .tf/knowledge first, then fill gaps)
- Parallel validation speeds up feedback

## 3. Execute Chosen Path

Before execution, run path-specific preflight (from guardrails above) and stop if any required agent is missing.

**CRITICAL: Preserve `parallel` structure exactly.** When constructing the `subagent` call:
- Keep `{"parallel": [...]}` as a single object in the chain array
- Do NOT expand parallel blocks into separate sequential steps
- The `concurrency` and `failFast` fields must remain inside the parallel object

### Path A: Minimal

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
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per anchor context.", "reads": ["anchor-context.md"], "output": "implementation.md" },
    { "agent": "reviewer", "task": "Review implementation for ticket <TICKET_ID>.", "reads": ["implementation.md"], "output": "review.md" },
    { "agent": "tk-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket close gate. Reads: anchor-context.md, implementation.md, review.md. Writes: .tf/progress.md (append entry), .tf/AGENTS.md (append only NEW+USEFUL lessons), git commit, tk add-note, tk close/status decision.", "reads": ["anchor-context.md", "implementation.md", "review.md"], "output": "close-summary.md" }
  ]
}
```

### Path B: Standard

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
    { "agent": "planner", "task": "Create implementation plan for ticket <TICKET_ID>.", "reads": ["anchor-context.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Review implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
        { "agent": "tester", "task": "Test implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "tk-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket close gate. Reads: anchor-context.md, implementation.md, review.md, test-results.md. Writes: .tf/progress.md (append entry), .tf/AGENTS.md (append only NEW+USEFUL lessons), git commit, tk add-note, tk close/status decision.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md"], "output": "close-summary.md" }
  ]
}
```

### Path C: Deep (Always includes research when needed)

**First, check if research is needed:**
- Read `anchor-context.md` — does it identify knowledge gaps?
- Check existing `.tf/knowledge/` — is there sufficient coverage?

**If research IS needed:**

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
    {
      "parallel": [
        { "agent": "researcher", "task": "Research external best practices and documentation for ticket <TICKET_ID>. Check .tf/knowledge first; only research gaps.", "reads": ["anchor-context.md"], "output": "research.md" },
        { "agent": "librarian", "task": "Research source-backed library internals for ticket <TICKET_ID> with GitHub permalinks.", "reads": ["anchor-context.md"], "output": "library-research.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "planner", "task": "Create implementation plan for ticket <TICKET_ID>.", "reads": ["anchor-context.md", "research.md", "library-research.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Review implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
        { "agent": "tester", "task": "Test implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Fix issues from review and test results. Prioritize: test failures > critical review > major review.", "reads": ["review.md", "test-results.md", "implementation.md"], "output": "fixes.md" },
    { "agent": "tk-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, persist research, lessons learned, ticket close gate. Reads: anchor-context.md, implementation.md, review.md, test-results.md, fixes.md, research.md, library-research.md. Writes: .tf/progress.md (append entry), .tf/knowledge (persist reusable research), .tf/AGENTS.md (append only NEW+USEFUL lessons), git commit, tk add-note, tk close/status decision.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "research.md", "library-research.md"], "output": "close-summary.md" }
  ]
}
```

**If research is NOT needed** (knowledge sufficient):

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
    { "agent": "planner", "task": "Create implementation plan for ticket <TICKET_ID> using existing knowledge.", "reads": ["anchor-context.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Review implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
        { "agent": "tester", "task": "Test implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Fix issues from review and test results.", "reads": ["review.md", "test-results.md", "implementation.md"], "output": "fixes.md" },
    { "agent": "tk-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket close gate. Reads: anchor-context.md, implementation.md, review.md, test-results.md, fixes.md. Writes: .tf/progress.md (append entry), .tf/AGENTS.md (append only NEW+USEFUL lessons), git commit, tk add-note, tk close/status decision.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md"], "output": "close-summary.md" }
  ]
}
```

## 4. Execute and Report

Use `subagent` tool with chosen path and report:

1. **Which path you chose and why**
2. **Whether research was included**
3. **Summary of what was done**
4. **Files changed**
5. **Blockers/decisions**

Progress tracking and lessons learned are handled by `tk-closer` — no need to manually update `.tf/progress.md` or `.tf/AGENTS.md` in the main loop.

## tk-closer Responsibilities

The `tk-closer` agent handles all post-implementation finalization:

### A) Progress Tracking
Append to `.tf/progress.md`:
- timestamp
- ticket id
- status
- path chosen (A/B/C)
- research included? (yes/no)
- summary
- files changed
- test results
- chain path: `.subagent-runs/<TICKET_ID>`
- commit hash

### B) Lessons Learned
Append to `.tf/AGENTS.md` **only if BOTH are true**:
1. **New**: not already captured in `.tf/AGENTS.md`
2. **Useful**: likely to improve future ticket implementations

Do NOT add:
- ticket-specific trivia
- obvious/general advice
- duplicates or near-duplicates

### C) Research Persistence (Path C only)
If research was conducted, persist reusable findings to `.tf/knowledge/`:
- Topic files: `.tf/knowledge/topics/<topic-slug>.md`
- Ticket research: `.tf/knowledge/tickets/<TICKET_ID>/research.md`

### D) Git Commit
1. `git rev-parse --is-inside-work-tree`
2. `git status --short`
3. Stage and commit with message: `<TICKET_ID>: <summary>`

### E) Ticket Note
- `tk add-note <TICKET_ID> "..."`

### F) Close Decision
Close only if:
- Dependencies complete
- Implementation complete
- No blocking issues (critical/major failures)
- Tests passed

Then: `tk close <TICKET_ID>`

Else: `tk status <TICKET_ID> in-progress`

## Example Usage

```
/tk-implement TICKET-123              # you decide path after analysis
/tk-implement TICKET-123 --async      # background execution
```
