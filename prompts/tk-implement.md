---
description: Analyze and implement any tk ticket with main-agent path selection
---

Implement ticket from `$@` (parsed into `<TICKET_ID>` + flags).

**Key principle:** The main agent (you) analyzes the ticket after scout/context-builder and decides which implementation path to use. Research is never skipped when needed.

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

## Re-Anchor Context

1. Set paths:
   - `TICKET_ID = <TICKET_ID>`
   - `CHAIN_DIR = .subagent-runs/<TICKET_ID>`
   - `KNOWLEDGE_ROOT = .tf/knowledge`
2. Ensure directories exist
3. Read `.tf/AGENTS.md` and relevant `.tf/knowledge/**` files
4. Build context summary from ticket + dependencies + lessons + knowledge

## 1. Read and Analyze the Ticket

Read the ticket file (find with `find . -name "<TICKET_ID>.md" 2>/dev/null`):

- **Title/Description**: What needs to be done?
- **Tags/Type**: code, config, workflow, frontend, etc.
- **Dependencies**: Are they complete?
- **Complexity indicators**:
  - Simple: Config, docs, small fixes (<50 LOC)
  - Medium: Features, integrations, workflows (50-200 LOC)
  - Complex: AI systems, novel algorithms, library-heavy, performance-critical (>200 LOC)

## 2. Scout + Context-Builder (Always First)

Run these sequentially first:

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
      "task": "Build re-anchored implementation context for ticket <TICKET_ID>. Synthesize scout output, ticket requirements, .tf/AGENTS.md lessons, and .tf/knowledge. Identify: 1) implementation path complexity, 2) research needs, 3) external libraries involved, 4) testing requirements.", 
      "reads": ["scout-context.md"], 
      "output": "anchor-context.md" 
    }
  ]
}
```

## 3. YOU Decide the Implementation Path

Read `anchor-context.md` and decide based on:

| Factor | Path A (Minimal) | Path B (Standard) | Path C (Deep) |
|--------|------------------|-------------------|---------------|
| **Complexity** | Config, docs, small fixes | Features, integrations | AI, novel algorithms, library-heavy |
| **Research needed?** | No (existing knowledge sufficient) | Maybe (check knowledge first) | Yes (new domain/libraries) |
| **LOC estimate** | <50 | 50-200 | >200 |
| **Validation** | Review only | Review → Test | Review + Test (parallel) |
| **Chain steps** | scout→context→worker→reviewer→closer | scout→context→planner→worker→reviewer→tester→closer | scout→context→**research**→planner→worker→**parallel review+test**→fixer→closer |

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

## 4. Execute Chosen Path

Before execution, run path-specific preflight (from guardrails above) and stop if any required agent is missing.

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
    { "agent": "tk-closer", "task": "Commit and close gate for ticket <TICKET_ID>.", "reads": ["implementation.md", "review.md"], "output": "close-summary.md" }
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
    { "agent": "reviewer", "task": "Review implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
    { "agent": "tester", "task": "Test implementation for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md", "review.md"], "output": "test-results.md" },
    { "agent": "tk-closer", "task": "Commit and close gate for ticket <TICKET_ID>.", "reads": ["implementation.md", "review.md", "test-results.md"], "output": "close-summary.md" }
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
    { "agent": "tk-closer", "task": "Commit and close gate for ticket <TICKET_ID>.", "reads": ["implementation.md", "review.md", "test-results.md", "fixes.md"], "output": "close-summary.md" }
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
    { "agent": "tk-closer", "task": "Commit and close gate for ticket <TICKET_ID>.", "reads": ["implementation.md", "review.md", "test-results.md", "fixes.md"], "output": "close-summary.md" }
  ]
}
```

## 5. Execute and Report

Use `subagent` tool with chosen path and report:

1. **Which path you chose and why**
2. **Whether research was included**
3. **Summary of what was done**
4. **Files changed**
5. **Blockers/decisions**
6. **Persist new research** to `.tf/knowledge` if applicable
7. **Append to `.tf/progress.md`**
8. **Conditionally update `.tf/AGENTS.md`** with new useful lessons

## Git Commit and Ticket Closure (tk-closer)

### A) Commit
1. `git rev-parse --is-inside-work-tree`
2. `git status --short`
3. Stage and commit with message: `<TICKET_ID>: <summary>`

### B) Add ticket note
- `tk add-note <TICKET_ID> "..."`

### C) Decide closure
Close only if:
- Dependencies complete
- Implementation complete
- No blocking issues (critical/major failures)
- Tests passed

Then: `tk close <TICKET_ID>`

Else: `tk status <TICKET_ID> in-progress`

## Progress Tracking

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
- commands executed

## Example Usage

```
/tk-implement TICKET-123              # you decide path after analysis
/tk-implement TICKET-123 --async      # background execution
```
