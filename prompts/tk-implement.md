---
description: Analyze and implement any tk ticket with main-agent path selection
---

Implement ticket from `$@` (parsed into `<TICKET_ID>` + flags).

**Key principle:** The main agent (you) analyzes `anchor-context.md` after the fast anchoring phase (pre-seeded scout/context + merge) and decides which implementation path to use. Context-builder performs ticket/lessons/knowledge anchoring; context-merger appends scout code context.

## Parse Input and Runtime Flags

Treat `$@` as raw input that may include a ticket id plus flags.

Supported flags:
- `--async` → run subagent execution in background mode (`async: true`)
- `--clarify` → open chain clarification TUI (`clarify: true`)
- `--interactive` → run with interactive overlay (supervised, blocking)
- `--hands-free` → run with agent-monitored overlay (polling, non-blocking)
- `--dispatch` → run headless background with notification (fire-and-forget)

Parsing rules:
1. Extract `TICKET_ID` as the first non-flag token.
2. Set flag booleans: `RUN_ASYNC`, `RUN_CLARIFY`, `RUN_INTERACTIVE`, `RUN_HANDS_FREE`, `RUN_DISPATCH`.
3. If `TICKET_ID` is missing, STOP and ask for a ticket id.
4. Reject unknown flags with a short help message.

**Flag Validation Matrix:**

| Combination | Valid | Error if invalid |
|-------------|-------|------------------|
| `--interactive` + `--hands-free` | ❌ | Cannot combine --interactive with --hands-free |
| `--interactive` + `--dispatch` | ❌ | Cannot combine --interactive with --dispatch |
| `--hands-free` + `--dispatch` | ❌ | Cannot combine --hands-free with --dispatch |
| `--interactive` + `--async` | ❌ | Interactive modes cannot be used with --async |
| `--hands-free` + `--async` | ❌ | Interactive modes cannot be used with --async |
| `--dispatch` + `--async` | ❌ | Interactive modes cannot be used with --async |
| `--interactive` + `--clarify` | ❌ | --interactive and --clarify are mutually exclusive (overlay conflict) |
| `--hands-free` + `--clarify` | ✅ | Clarify runs before hands-free overlay |
| `--dispatch` + `--clarify` | ✅ | Clarify runs before dispatch |
| `--async` + `--clarify` | ⚠️ | Async wins, clarify=false (legacy behavior) |

Validation order:
1. Check for unknown flags first.
2. Check mutual exclusivity among `--interactive`, `--hands-free`, `--dispatch`.
3. Check interactive flags against `--async`.
4. Check `--interactive` against `--clarify`.
5. Apply legacy rule: if `--async` and `--clarify` both set, prefer async.

## Subagent Scope Guardrails (Critical)

- Use existing agents only.
- **NEVER** call `subagent` with management actions: `create`, `update`, or `delete`.
- Determine `AGENT_SCOPE` first, then use it consistently on every subagent execution call (single, chain, and parallel).
- Baseline preflight before any run:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required baseline agents: `scout`, `context-builder`, `worker`, `reviewer`, `tk-closer`
  - Optional optimization agent: `context-merger` (if missing, use fallback chain in section 1e).
- Path-specific preflight before executing chosen path:
  - Path A: baseline + `fixer`
  - Path B: baseline + `planner-b`, `tester`, `fixer`
  - Path C with research: baseline + `planner-c`, `tester`, `fixer`, `researcher`, `librarian`
  - Path C without new research: baseline + `planner-c`, `tester`, `fixer`
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

## 1. Fast Anchoring (Pre-seeded Parallel Scout + Context-Builder)

**Optimizations applied:**
- Pre-seed both agents with ticket context (no blind exploration)
- Run scout + context-builder in parallel
- Reuse cached scout context if codebase unchanged
- Scout follows dependency chains, not just direct matches
- Batched file reading within scout

### 1a. Quick Ticket Analysis (Main Agent - 15 seconds)

YOU extract seeding context from the ticket:

```bash
# Ensure run directory exists
mkdir -p .subagent-runs/<TICKET_ID>

# Find ticket file
TICKET_FILE=$(find . -name "<TICKET_ID>.md" -type f 2>/dev/null | head -1)
if [ -z "$TICKET_FILE" ]; then
  echo "ERROR: ticket file not found for <TICKET_ID>"
  # STOP here and report missing ticket file to user.
fi
```

Read the ticket file and extract:
- **Primary terms**: function names, class names, module names mentioned
- **Secondary terms**: concepts, patterns, technologies referenced
- **File hints**: any explicit file paths mentioned
- **Change scope**: which files/directories likely need modification

Write this to `.subagent-runs/<TICKET_ID>/ticket-seed.json`:
```json
{
  "ticket_id": "<TICKET_ID>",
  "primary_terms": ["funcName", "ClassName", "module_name"],
  "secondary_terms": ["authentication", "jwt", "middleware"],
  "file_hints": ["src/auth/", "tests/test_auth.py"],
  "change_scope": "auth module and related tests",
  "ticket_summary": "One-line summary of what needs to be done"
}
```

### 1b. Check for Cached Scout Context

Check if we can reuse previous scout output:

```bash
# Check if scout context exists from a previous run
SCOUT_CACHE=".subagent-runs/<TICKET_ID>/scout-context.md"
CACHE_META=".subagent-runs/<TICKET_ID>/.scout-git-hash"
CACHE_VALID=false

if [ -f "$SCOUT_CACHE" ] && [ -f "$CACHE_META" ]; then
  CURRENT_HASH=$(git rev-parse HEAD 2>/dev/null || echo "no-git")
  CACHE_HASH=$(cat "$CACHE_META" 2>/dev/null || echo "")

  if [ "$CURRENT_HASH" = "$CACHE_HASH" ]; then
    CACHE_VALID=true
  elif ! git cat-file -e "$CACHE_HASH^{commit}" 2>/dev/null; then
    # Cache points to unknown history (rebased/pruned). Do a fresh scout.
    CACHE_VALID=false
  else
    # "Significant" change check: reuse cache only when changes do not touch
    # (a) previously scouted files and (b) ticket seed scope hints.
    CHANGED_FILES=$(git diff --name-only "$CACHE_HASH"..HEAD 2>/dev/null || true)

    if [ -n "$CHANGED_FILES" ]; then
      # First, invalidate cache if any changed file was part of previously scouted context.
      RELEVANT_CHANGE=false
      while IFS= read -r f; do
        [ -z "$f" ] && continue
        if grep -F -q -- "\`$f\`" "$SCOUT_CACHE" || grep -F -q -- "$f" "$SCOUT_CACHE"; then
          RELEVANT_CHANGE=true
          break
        fi
      done <<< "$CHANGED_FILES"

      # Secondary check using ticket seed scope hints.
      SCOPE_REGEX=$(python3 - <<'PY'
import json, re
from pathlib import Path
p = Path('.subagent-runs/<TICKET_ID>/ticket-seed.json')
if not p.exists():
    print('.*')
    raise SystemExit
seed = json.loads(p.read_text())
parts = []
for h in seed.get('file_hints', []):
    if h:
        parts.append(re.escape(h.strip('/')))
for t in seed.get('primary_terms', []):
    if t:
        parts.append(re.escape(t))
print('|'.join(parts) if parts else '.*')
PY
)

      if [ "$RELEVANT_CHANGE" = true ] || echo "$CHANGED_FILES" | grep -E -q -- "$SCOPE_REGEX"; then
        CACHE_VALID=false
      else
        CACHE_VALID=true
      fi
    else
      # Different commit hash but no file changes in range; reuse cache.
      CACHE_VALID=true
    fi
  fi
fi
```

If `CACHE_VALID=true`, skip the scout run and reuse existing `scout-context.md`; run context-builder and merge with cached scout context.

### 1c. Parallel Scout + Context-Builder (Pre-seeded, when cache is invalid)

Use this when `CACHE_VALID=false`. Both agents receive the ticket seed for targeted work:

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
      "parallel": [
        {
          "agent": "scout",
          "task": "Scout codebase for ticket <TICKET_ID>. SEED CONTEXT in ticket-seed.json - use it to target your search.\n\nMUST DO:\n1. Read ticket-seed.json first for targeting hints\n2. Find files matching primary_terms using grep/find\n3. Read those files AND their imports/dependencies (follow import statements)\n4. Read related test files\n5. Use batched/rapid read calls when fetching multiple files\n\nOUTPUT: scout-context.md with:\n- Files Retrieved (with line ranges and WHY relevant)\n- Key Code (actual snippets of types/functions)\n- Dependency Graph (what imports what)\n- Architecture Notes\n- Start Here recommendation",
          "reads": ["ticket-seed.json"],
          "output": "scout-context.md"
        },
        {
          "agent": "context-builder",
          "task": "Build implementation context for ticket <TICKET_ID>. SEED CONTEXT in ticket-seed.json - use it for context.\n\nMUST DO:\n1. Read ticket-seed.json for ticket summary\n2. Read full ticket file for details\n3. Read .tf/AGENTS.md for lessons learned\n4. Read relevant .tf/knowledge/** files\n\nOUTPUT: anchor-context-base.md with:\n- Ticket Summary (what + why)\n- Complexity Assessment (simple/medium/complex)\n- Research Gaps (if any)\n- External Libraries Involved\n- Testing Requirements\n- Recommended Path (A/B/C)\n\nNOTE: scout-context.md may not be available yet - work independently.",
          "reads": ["ticket-seed.json"],
          "output": "anchor-context-base.md"
        }
      ],
      "concurrency": 2,
      "failFast": false
    },
    {
      "agent": "context-merger",
      "task": "Merge scout and context-builder outputs into final anchor-context.md.\n\nRead both scout-context.md and anchor-context-base.md.\nIf scout found relevant code patterns/dependencies, ADD them under a new 'Code Context' section.\nKeep all existing sections from anchor-context-base.md.\nWrite the merged result to anchor-context.md.",
      "reads": ["scout-context.md", "anchor-context-base.md"],
      "output": "anchor-context.md"
    }
  ]
}
```

After completion, store git hash for cache validation:
```bash
git rev-parse HEAD > .subagent-runs/<TICKET_ID>/.scout-git-hash 2>/dev/null || true
```

### 1d. Cache-Hit Path (Reuse scout output)

Use this when `CACHE_VALID=true`:

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
      "agent": "context-builder",
      "task": "Build implementation context for ticket <TICKET_ID> using ticket-seed.json and latest ticket/knowledge files.",
      "reads": ["ticket-seed.json"],
      "output": "anchor-context-base.md"
    },
    {
      "agent": "context-merger",
      "task": "Merge cached scout-context.md with fresh anchor-context-base.md into final anchor-context.md.",
      "reads": ["scout-context.md", "anchor-context-base.md"],
      "output": "anchor-context.md"
    }
  ]
}
```

### 1e. If No context-merger Agent Exists

If `context-merger` is not available, use this fallback chain:

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
      "parallel": [
        {
          "agent": "scout",
          "task": "Scout codebase for ticket <TICKET_ID>. Read ticket-seed.json FIRST for targeting.\n\nMUST:\n1. grep/find files matching primary_terms\n2. Read matched files AND their dependencies (follow imports)\n3. Read related test files\n4. Use batched/rapid read calls for multiple files\n\nOutput: scout-context.md",
          "reads": ["ticket-seed.json"],
          "output": "scout-context.md"
        },
        {
          "agent": "context-builder",
          "task": "Build anchor context for <TICKET_ID>. Read ticket-seed.json, full ticket, .tf/AGENTS.md, .tf/knowledge/**.\n\nAfter parallel phase, you'll receive scout-context.md to incorporate.\n\nOutput: anchor-context-draft.md with ticket summary, complexity, research gaps, path recommendation.",
          "reads": ["ticket-seed.json"],
          "output": "anchor-context-draft.md"
        }
      ],
      "concurrency": 2,
      "failFast": false
    },
    {
      "agent": "context-builder",
      "task": "Finalize anchor-context.md by merging scout findings.\n\nRead anchor-context-draft.md and scout-context.md.\nAdd a 'Code Context' section with scout's findings to the draft.\nWrite final merged result to anchor-context.md.",
      "reads": ["anchor-context-draft.md", "scout-context.md"],
      "output": "anchor-context.md"
    }
  ]
}
```

After successful fallback run that included a fresh scout, store git hash for cache validation:
```bash
git rev-parse HEAD > .subagent-runs/<TICKET_ID>/.scout-git-hash 2>/dev/null || true
```

If `context-merger` is missing **and** `CACHE_VALID=true`, use this cache-hit fallback:

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
      "agent": "context-builder",
      "task": "Build anchor context for <TICKET_ID> from ticket-seed.json, ticket file, .tf/AGENTS.md, and .tf/knowledge/**.",
      "reads": ["ticket-seed.json"],
      "output": "anchor-context-draft.md"
    },
    {
      "agent": "context-builder",
      "task": "Finalize anchor-context.md by merging cached scout findings. Read anchor-context-draft.md and scout-context.md, then add a Code Context section and write anchor-context.md.",
      "reads": ["anchor-context-draft.md", "scout-context.md"],
      "output": "anchor-context.md"
    }
  ]
}
```

**Time saved:**
- Pre-seeding: Scout doesn't wander, targets specific files (~50% faster)
- Parallel: Scout + context-builder run simultaneously (~40% faster)
- Caching: Skip scout entirely if unchanged (~100% faster for re-runs)

## 2. Interactive Mode Router (Post-Anchoring)

If any interactive flag (`--interactive`, `--hands-free`, `--dispatch`) is set, route through `interactive_shell` **instead of** Path A/B/C execution. This section runs after fast anchoring completes and before Path selection.

### 2a. Recursion Guard

Prevent nested interactive invocations from re-entering this router:

```bash
# Check recursion sentinel
if [ -n "$PI_TK_INTERACTIVE_CHILD" ]; then
  # Already running inside interactive_shell, fall through to Path A/B/C
  RUN_INTERACTIVE=false
  RUN_HANDS_FREE=false
  RUN_DISPATCH=false
fi
```

### 2b. Build Nested Command

Construct the inner `/tk-implement` command that runs inside the interactive session:

```bash
# Build base command
INNER_CMD="pi \"/tk-implement <TICKET_ID>"

# Pass --clarify if set (allowed with hands-free and dispatch)
if [ "<RUN_CLARIFY>" = "true" ]; then
  INNER_CMD="$INNER_CMD --clarify"
fi

INNER_CMD="$INNER_CMD\""
```

### 2c. Route to interactive_shell

If `RUN_INTERACTIVE`, `RUN_HANDS_FREE`, or `RUN_DISPATCH` is true:

**For `--interactive` mode:**
```json
{
  "command": "<INNER_CMD>",
  "mode": "interactive",
  "reason": "Interactive supervised execution for <TICKET_ID>"
}
```

**For `--hands-free` mode:**
```json
{
  "command": "<INNER_CMD>",
  "mode": "hands-free",
  "reason": "Hands-free monitored execution for <TICKET_ID>",
  "handsFree": {
    "updateMode": "on-quiet",
    "quietThreshold": 8000,
    "updateInterval": 60000,
    "autoExitOnQuiet": false
  }
}
```

**For `--dispatch` mode:**
```json
{
  "command": "<INNER_CMD>",
  "mode": "dispatch",
  "background": true,
  "reason": "Background dispatched execution for <TICKET_ID>"
}
```

### 2d. Session Metadata Persistence

On successful `interactive_shell` invocation, write session metadata:

```json
{
  "mode": "<interactive|hands-free|dispatch>",
  "sessionId": "<sessionId_from_result>",
  "startedAt": "<ISO8601_timestamp>",
  "command": "<INNER_CMD>",
  "status": "pending"
}
```

Write to: `.subagent-runs/<TICKET_ID>/session.json`

**Console breadcrumbs to emit:**
```
═══════════════════════════════════════════════════════════════
  Interactive Session Started
  Mode: <mode>
  Session ID: <sessionId>

  Commands:
    /attach <sessionId>    Reattach to this session
    /sessions              List all active sessions

  Keybindings:
    Ctrl+T  Transfer output to agent context
    Ctrl+B  Background session (keep running)
    Ctrl+Q  Detach menu (transfer/background/kill)
═══════════════════════════════════════════════════════════════
```

### 2e. Execution Flow

1. Call `interactive_shell` with appropriate mode parameters
2. If successful, persist `session.json` and emit breadcrumbs
3. Set `PI_TK_INTERACTIVE_CHILD=1` env var in nested command context
4. Return control to user (interactive mode) or agent (hands-free/dispatch)

**Important:** When any interactive mode is active, SKIP Path A/B/C execution in sections 3-4. The nested command (without interactive flags) will execute the full Path A/B/C flow.

## 3. YOU Decide the Implementation Path

Read `.subagent-runs/<TICKET_ID>/anchor-context.md` and decide based on:

| Factor | Path A (Minimal) | Path B (Standard) | Path C (Deep) |
|--------|------------------|-------------------|---------------|
| **Complexity** | Config, docs, small fixes | Features, integrations | AI, novel algorithms, library-heavy |
| **Research needed?** | No (existing knowledge sufficient) | Maybe (check knowledge first) | Yes (new domain/libraries) |
| **LOC estimate** | <50 | 50-200 | >200 |
| **Validation** | Review only | Review + Test (parallel) | Review + Test (parallel) |
| **Chain steps** | seed→(scout∥context)→merge→worker→reviewer→fixer→reviewer(re-check)→closer | seed→(scout∥context)→merge→planner-b→worker→**parallel review+test**→fixer→**parallel re-check**→closer | seed→(scout∥context)→merge→**parallel research**→planner-c→worker→**parallel review+test**→fixer→**parallel re-check**→closer |

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
- Standard parallel validation (review + test) is sufficient

**Choose Path C when:**
- Complex algorithms, AI systems, or novel domains
- Multiple new external libraries
- Research required (check .tf/knowledge first, then fill gaps)
- Parallel validation speeds up feedback

## 4. Execute Chosen Path

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
    { "agent": "reviewer", "task": "Initial review for ticket <TICKET_ID>. Identify critical/major/minor issues.", "reads": ["implementation.md", "anchor-context.md"], "output": "review.md" },
    { "agent": "fixer", "task": "Apply one fix pass for ticket <TICKET_ID> based on review.md. If no critical/major issues exist, record a no-op rationale.", "reads": ["implementation.md", "review.md", "anchor-context.md"], "output": "fixes.md" },
    { "agent": "reviewer", "task": "Post-fix re-check for ticket <TICKET_ID>. Validate whether critical/major issues are resolved after fixes.md.", "reads": ["implementation.md", "fixes.md", "anchor-context.md"], "output": "review-post-fix.md" },
    { "agent": "tk-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket close gate. maxFixPasses=1 per run. If post-fix review still has critical/major issues, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "fixes.md", "review-post-fix.md"], "output": "close-summary.md" }
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
    { "agent": "planner-b", "task": "Create implementation plan for ticket <TICKET_ID>.", "reads": ["anchor-context.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Initial review for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
        { "agent": "tester", "task": "Initial tests for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Apply one fix pass for ticket <TICKET_ID> using review.md and test-results.md. If no critical/major issues exist, record a no-op rationale.", "reads": ["implementation.md", "review.md", "test-results.md", "plan.md"], "output": "fixes.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Post-fix re-check review for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md", "fixes.md"], "output": "review-post-fix.md" },
        { "agent": "tester", "task": "Post-fix re-check tests for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md", "fixes.md"], "output": "test-results-post-fix.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "tk-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket close gate. maxFixPasses=1 per run. If post-fix re-check still has critical/major issues, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md", "test-results-post-fix.md"], "output": "close-summary.md" }
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
    { "agent": "planner-c", "task": "Create implementation plan for ticket <TICKET_ID>.", "reads": ["anchor-context.md", "research.md", "library-research.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Initial review for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
        { "agent": "tester", "task": "Initial tests for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Apply one fix pass for ticket <TICKET_ID>. Prioritize: test failures > critical review > major review. If no critical/major issues exist, record a no-op rationale.", "reads": ["review.md", "test-results.md", "implementation.md", "plan.md"], "output": "fixes.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Post-fix re-check review for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md", "fixes.md"], "output": "review-post-fix.md" },
        { "agent": "tester", "task": "Post-fix re-check tests for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md", "fixes.md"], "output": "test-results-post-fix.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "tk-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, persist research, lessons learned, ticket close gate. maxFixPasses=1 per run. If post-fix re-check still has critical/major issues, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md", "test-results-post-fix.md", "research.md", "library-research.md"], "output": "close-summary.md" }
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
    { "agent": "planner-c", "task": "Create implementation plan for ticket <TICKET_ID> using existing knowledge.", "reads": ["anchor-context.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Initial review for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "review.md" },
        { "agent": "tester", "task": "Initial tests for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Apply one fix pass for ticket <TICKET_ID> using review.md and test-results.md. If no critical/major issues exist, record a no-op rationale.", "reads": ["review.md", "test-results.md", "implementation.md", "plan.md"], "output": "fixes.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Post-fix re-check review for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md", "fixes.md"], "output": "review-post-fix.md" },
        { "agent": "tester", "task": "Post-fix re-check tests for ticket <TICKET_ID>.", "reads": ["implementation.md", "plan.md", "fixes.md"], "output": "test-results-post-fix.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "tk-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket close gate. maxFixPasses=1 per run. If post-fix re-check still has critical/major issues, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md", "test-results-post-fix.md"], "output": "close-summary.md" }
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

Else: `tk status <TICKET_ID> in_progress`

### G) Fix-loop Policy (Max 1 per run)
- `maxFixPasses = 1` for each `/tk-implement` run.
- Use post-fix artifacts (`review-post-fix.md`, `test-results-post-fix.md`) as the source of truth when present.
- If post-fix re-check still has critical/major issues, do not attempt additional fix passes in the same run.
- Keep ticket `in_progress`, add a clear blocker note via `tk add-note`, and suggest a follow-up run.

## Example Usage

```
/tk-implement TICKET-123                        # you decide path after analysis
/tk-implement TICKET-123 --async                # background execution (legacy)
/tk-implement TICKET-123 --clarify              # chain clarification TUI

# Interactive modes (new)
/tk-implement TICKET-123 --interactive          # supervised overlay (blocking)
/tk-implement TICKET-123 --hands-free           # agent-monitored overlay
/tk-implement TICKET-123 --dispatch             # background + notification

# Valid combinations
/tk-implement TICKET-123 --hands-free --clarify # clarify then hands-free
/tk-implement TICKET-123 --dispatch --clarify   # clarify then dispatch
```
