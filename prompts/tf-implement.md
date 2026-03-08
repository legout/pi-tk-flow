---
description: Analyze and implement any tk ticket with main-agent path selection
model: glm-5
thinking: medium
---

Implement ticket from `$@` (parsed into `<TICKET_ID>` + flags).

**Key principle:** The main agent (you) analyzes `anchor-context.md` after the fast anchoring phase and decides which implementation path to use. `context-builder` performs the ticket/lessons/knowledge anchoring; keep this step focused and fast.

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
4. Reject unknown flags with a short help message:
   ```
   Unknown flag: <flag>

   Usage: /tf-implement <TICKET_ID> [flags]

   Flags:
     --interactive    Run with interactive overlay (supervised, blocking)
     --hands-free     Run with agent-monitored overlay (polling, non-blocking)
     --dispatch       Run headless background with notification (fire-and-forget)
     --async          Legacy background mode (no session tracking)
     --clarify        Open chain clarification TUI

   Use /tf-implement --help for full documentation.
   ```

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
  - Required baseline agents: `context-builder`, `worker`, `reviewer`, `tf-closer`
- Path-specific preflight before executing chosen path:
  - Path A: baseline + `fixer`
  - Path B: baseline + `plan-fast`, `tester`, `fixer`
  - Path C with research: baseline + `plan-deep`, `tester`, `fixer`, `researcher`, `librarian`
  - Path C without new research: baseline + `plan-deep`, `tester`, `fixer`
- If a required agent is missing, **STOP** and report which agent(s) are missing.
- Do not write or modify `.pi/agents/*` as part of `/tf-implement`.

## Determine Agent Scope

1. If `.pi/agents/.tf-bootstrap.json` exists → `AGENT_SCOPE = "project"`
2. Otherwise → `AGENT_SCOPE = "user"`
3. Use `"both"` only when intentionally overriding user agents with project agents.

## Subagent Runtime Defaults

- `clarify: <RUN_CLARIFY>` (default false)
- `async: <RUN_ASYNC>` (default false)
- `artifacts: true`
- `includeProgress: false`
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

## 1. Fast Anchoring (Context-Builder Only)

**Optimizations applied:**
- Pre-seed a single anchoring agent with ticket context
- Use `context-builder` only — no scout, no merge step
- Anchor only what is needed to implement the current ticket
- Keep anchoring fast, deterministic, and easy to resume

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

### 1b. Run Context-Builder

Use a single `context-builder` run for anchoring:

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": ".subagent-runs/<TICKET_ID>",
  "clarify": false,
  "async": false,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "agent": "context-builder",
  "task": "Build implementation context for ticket <TICKET_ID>. Read ticket-seed.json first. Read PROJECT.md when present, use AGENTS.md for repo operating guidance, and focus on the ticket, relevant lessons, and existing .tf/knowledge. Use explicit ticket file hints when available. Do NOT do broad codebase scouting; anchor only the context needed to implement this ticket. Output anchor-context.md with: Ticket Summary, Complexity Assessment, Research Gaps, External Libraries, Testing Requirements, Recommended Path (A/B/C), and concrete file hints to start from when known.",
  "reads": ["ticket-seed.json"],
  "output": "anchor-context.md"
}
```

**CRITICAL: Handle subagent session directory structure**
The subagent run may create a session subdirectory (e.g., `.subagent-runs/<TICKET_ID>/<session-id>/`) and write output files there. After the run completes, locate and copy `anchor-context.md` to the expected location:

```bash
ANCHOR_FILE=$(find .subagent-runs/<TICKET_ID> -name "anchor-context.md" -type f 2>/dev/null | head -1)

if [ -n "$ANCHOR_FILE" ] && [ "$ANCHOR_FILE" != ".subagent-runs/<TICKET_ID>/anchor-context.md" ]; then
  cp "$ANCHOR_FILE" .subagent-runs/<TICKET_ID>/anchor-context.md
fi

if [ ! -f ".subagent-runs/<TICKET_ID>/anchor-context.md" ]; then
  echo "ERROR: anchor-context.md not found after anchoring run"
  echo "Searched in: .subagent-runs/<TICKET_ID>/"
  # STOP and report the error
fi
```

**Time saved:**
- Single-agent anchoring instead of parallel scout + merge
- Fewer artifacts to manage in `.subagent-runs/<TICKET_ID>`
- Faster reruns and easier handoff

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

Construct the inner `/tf-implement` command that runs inside the interactive session:

```bash
# Build base command with recursion guard to prevent nested interactive loops
INNER_CMD="PI_TK_INTERACTIVE_CHILD=1 pi \"/tf-implement <TICKET_ID>"

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

On successful `interactive_shell` invocation, persist session metadata using atomic write and emit breadcrumbs.

**Implementation Steps:**

1. **Extract sessionId from result** - The `interactive_shell` call returns a `sessionId` (e.g., "calm-reef")

2. **Atomic Write session.json** using temp-file + rename pattern to prevent partial/corrupt files:

```bash
SESSION_DIR=".subagent-runs/<TICKET_ID>"
SESSION_FILE="$SESSION_DIR/session.json"
TEMP_FILE="$SESSION_FILE.tmp.$$"  # $$ provides process-specific suffix

# Ensure directory exists
mkdir -p "$SESSION_DIR"

# Write to temp file first (prevents partial files on crash/interrupt)
cat > "$TEMP_FILE" << 'SESS_EOF'
{
  "mode": "<MODE>",
  "sessionId": "<sessionId_from_result>",
  "startedAt": "<ISO8601_timestamp>",
  "command": "<INNER_CMD>",
  "status": "pending"
}
SESS_EOF

# Sync to disk for durability (best-effort; ignore errors on systems without sync)
sync "$TEMP_FILE" 2>/dev/null || true

# Atomic rename (on POSIX filesystems, rename is atomic)
mv "$TEMP_FILE" "$SESSION_FILE"

# Clear temp file reference after successful rename
TEMP_FILE=""
```

**Critical:** The temp file MUST use a unique suffix (e.g., `.$$` for PID) to avoid collisions from concurrent invocations.

3. **Emit console breadcrumbs** immediately after successful atomic write:
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

**Failure Handling:**

If `interactive_shell` invocation fails:

```bash
# 1. Clean up any temp file that may have been created
if [ -n "$TEMP_FILE" ] && [ -f "$TEMP_FILE" ]; then
  rm -f "$TEMP_FILE"
  TEMP_FILE=""
fi

# 2. Ensure no session.json was written (it should not exist if we failed before write)
#    If somehow it exists from a previous run, DO NOT modify it
```

1. **Clean up temp file** - Remove `$TEMP_FILE` if it exists before exiting
2. **Do NOT write session.json** - partial/corrupt files must not be created
3. **Emit actionable error message**:
   ```
   ERROR: Failed to start interactive session
   
   Possible causes:
   - Invalid command syntax in INNER_CMD
   - CLI agent not available (pi, claude, gemini, etc.)
   - Resource constraints
   
   Remediation:
   - Check that the CLI agent is installed: which pi
   - Verify the ticket ID exists: tk show <TICKET_ID>
   - Try without interactive flags for non-interactive execution
   - Check system resources (memory, disk space)
   ```
4. **Preserve existing artifacts** - Do not delete/modify any existing `.subagent-runs/<TICKET_ID>/` contents
5. **Exit with error status** - Do not continue to Path A/B/C execution

**Non-Interactive Guard:**

Session artifacts are ONLY created when interactive flags (`--interactive`, `--hands-free`, `--dispatch`) are present. For legacy non-interactive runs:
- `--async` alone → No session.json created
- No flags → No session.json created
- This preserves backward compatibility with existing automation

**Session Status Lifecycle:**

| Status | When Set | Description |
|--------|----------|-------------|
| `pending` | On successful interactive_shell invocation | Session is active/running |
| `completed` | When session ends successfully | Normal termination |
| `failed` | When session ends with error | Error/exception occurred |

Status updates after initial creation are handled by session monitoring (not in scope for ptf-102j).

**Example Session.json Files:**

Interactive mode:
```json
{
  "mode": "interactive",
  "sessionId": "calm-reef",
  "startedAt": "2026-03-04T12:34:56.789Z",
  "command": "pi \"/tf-implement TICKET-123\"",
  "status": "pending"
}
```

Hands-free mode with clarify:
```json
{
  "mode": "hands-free",
  "sessionId": "wise-owl",
  "startedAt": "2026-03-04T12:35:01.234Z",
  "command": "pi \"/tf-implement TICKET-123 --clarify\"",
  "status": "pending"
}
```

Dispatch mode:
```json
{
  "mode": "dispatch",
  "sessionId": "bright-star",
  "startedAt": "2026-03-04T12:35:12.567Z",
  "command": "pi \"/tf-implement TICKET-123\"",
  "status": "pending"
}
```

### 2e. Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Interactive Mode Router Flow                               │
├─────────────────────────────────────────────────────────────┤
│  1. Check recursion guard (PI_TK_INTERACTIVE_CHILD=1)       │
│     → If set: skip to Path A/B/C execution                  │
│                                                              │
│  2. Validate flag combinations                               │
│     → If invalid: emit error, STOP                          │
│                                                              │
│  3. Build INNER_CMD (nested command without interactive)    │
│                                                              │
│  4. Call interactive_shell with mode parameters             │
│     ├─ On SUCCESS:                                          │
│     │  a. Atomic write session.json (temp→sync→rename)      │
│     │  b. Emit console breadcrumbs                          │
│     │  c. Return control (user/agent/background)            │
│     │                                                       │
│     └─ On FAILURE:                                          │
│        a. Clean up temp file if exists                      │
│        b. Do NOT write session.json                         │
│        c. Emit actionable error message                     │
│        d. STOP (do not proceed to Path A/B/C)               │
│                                                              │
│  5. SKIP Path A/B/C - nested command will run them          │
└─────────────────────────────────────────────────────────────┘
```

**Detailed Steps:**

1. **Check recursion sentinel** (`PI_TK_INTERACTIVE_CHILD=1`)
   - If set: We're inside a nested invocation, skip interactive routing
   - If not set: Proceed with interactive mode handling

2. **Validate flags** (Section 2b validation matrix)
   - Unknown flags → error with help message
   - Invalid combinations → specific error message
   - Valid flags → proceed

3. **Build inner command** (`INNER_CMD`)
   - Base: `pi "/tf-implement <TICKET_ID>"`
   - Preserve `--clarify` if set: `pi "/tf-implement <TICKET_ID> --clarify"`
   - Never pass interactive flags to inner command

4. **Invoke interactive_shell**
   - Interactive mode: blocking, user-supervised
   - Hands-free mode: non-blocking, agent-monitored with polling
   - Dispatch mode: background, notification on completion

5. **Handle result:**
   - **Success:** Atomic write session.json, emit breadcrumbs, return
   - **Failure:** Clean up temp file, emit error guidance, exit

6. **Skip Path A/B/C** when interactive mode is active
   - The nested command (without interactive flags) will execute the full Path A/B/C flow
   - This prevents double execution of implementation logic

**Environment Variable Handling:**

Set `PI_TK_INTERACTIVE_CHILD=1` in the nested command environment to prevent infinite recursion:
```bash
PI_TK_INTERACTIVE_CHILD=1 pi "/tf-implement <TICKET_ID>"
```

**Important:** When any interactive mode is active, SKIP Path A/B/C execution in sections 3-5. The nested command (without interactive flags) will execute the full Path A/B/C flow.

## 3. YOU Decide the Implementation Path

Read `.subagent-runs/<TICKET_ID>/anchor-context.md` and decide based on:

| Factor | Path A (Minimal) | Path B (Standard) | Path C (Deep) |
|--------|------------------|-------------------|---------------|
| **Complexity** | Config, docs, small fixes | Features, integrations | AI, novel algorithms, library-heavy |
| **Research needed?** | No (existing knowledge sufficient) | Maybe (check knowledge first) | Yes (new domain/libraries) |
| **LOC estimate** | <50 | 50-200 | >200 |
| **Validation** | Review only | Review + Test (parallel) | Review + Test (parallel) |
| **Chain steps** | seed→context→worker→reviewer→fixer→reviewer(quick re-check)→closer | seed→context→plan-fast→worker→**parallel review+test**→fixer→reviewer(quick re-check)→closer | seed→context→**parallel research**→plan-deep→worker→**parallel review+test**→fixer→reviewer(quick re-check)→closer |

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
    { "agent": "reviewer", "task": "Initial review for ticket <TICKET_ID>. Review ONLY the changes introduced during this implementation. Use implementation.md to identify touched files and use git diff/show as needed to inspect changed hunks. Focus on ticket scope, acceptance criteria, and regressions in changed code; ignore unrelated pre-existing issues.", "reads": ["implementation.md", "anchor-context.md"], "output": "review.md" },
    { "agent": "fixer", "task": "Apply one fix pass for ticket <TICKET_ID> based on review.md. If no critical/major issues exist, record a no-op rationale.", "reads": ["implementation.md", "review.md", "anchor-context.md"], "output": "fixes.md" },
    { "agent": "reviewer", "task": "QUICK re-check for ticket <TICKET_ID>. Review ONLY the changed files/hunks touched by implementation and fixes. Focus on whether the critical/major issues from review.md are clearly resolved and whether the ticket scope looks safe. If anything is uncertain, insufficiently verified, or not an unambiguous pass, say so explicitly.", "reads": ["implementation.md", "review.md", "fixes.md", "anchor-context.md"], "output": "review-post-fix.md" },
    { "agent": "tf-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket artifact copy, and ticket close gate. maxFixPasses=1 per run. If the quick re-check is anything other than a clear pass, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "fixes.md", "review-post-fix.md"], "output": "close-summary.md" }
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
    { "agent": "plan-fast", "task": "Create implementation plan for ticket <TICKET_ID>.", "reads": ["anchor-context.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Initial review for ticket <TICKET_ID>. Review ONLY the changes introduced during this implementation. Use implementation.md to identify touched files and use git diff/show as needed to inspect changed hunks. Focus on ticket scope, acceptance criteria, and regressions in changed code; ignore unrelated pre-existing issues.", "reads": ["implementation.md", "plan.md", "anchor-context.md"], "output": "review.md" },
        { "agent": "tester", "task": "Initial tests for ticket <TICKET_ID>. Run only the most relevant ticket-scoped tests and checks you can identify with high signal. Prioritize changed modules, referenced tests, and the most direct validation commands.", "reads": ["implementation.md", "plan.md", "anchor-context.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Apply one fix pass for ticket <TICKET_ID> using review.md and test-results.md. If no critical/major issues exist, record a no-op rationale.", "reads": ["implementation.md", "review.md", "test-results.md", "plan.md"], "output": "fixes.md" },
    { "agent": "reviewer", "task": "QUICK re-check for ticket <TICKET_ID>. Review ONLY the changed files/hunks touched by implementation and fixes. Focus on whether the critical/major issues from review.md are clearly resolved and whether the ticket scope looks safe. Use the initial test-results.md as supporting signal, but do not broaden scope. If anything is uncertain, insufficiently verified, or not an unambiguous pass, say so explicitly.", "reads": ["implementation.md", "review.md", "test-results.md", "fixes.md", "plan.md", "anchor-context.md"], "output": "review-post-fix.md" },
    { "agent": "tf-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket artifact copy, and ticket close gate. maxFixPasses=1 per run. If the quick re-check is anything other than a clear pass, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md"], "output": "close-summary.md" }
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
    { "agent": "plan-deep", "task": "Create implementation plan for ticket <TICKET_ID>.", "reads": ["anchor-context.md", "research.md", "library-research.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Initial review for ticket <TICKET_ID>. Review ONLY the changes introduced during this implementation. Use implementation.md to identify touched files and use git diff/show as needed to inspect changed hunks. Focus on ticket scope, acceptance criteria, and regressions in changed code; ignore unrelated pre-existing issues.", "reads": ["implementation.md", "plan.md", "anchor-context.md"], "output": "review.md" },
        { "agent": "tester", "task": "Initial tests for ticket <TICKET_ID>. Run only the most relevant ticket-scoped tests and checks you can identify with high signal. Prioritize changed modules, referenced tests, and the most direct validation commands.", "reads": ["implementation.md", "plan.md", "anchor-context.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Apply one fix pass for ticket <TICKET_ID>. Prioritize: test failures > critical review > major review. If no critical/major issues exist, record a no-op rationale.", "reads": ["review.md", "test-results.md", "implementation.md", "plan.md"], "output": "fixes.md" },
    { "agent": "reviewer", "task": "QUICK re-check for ticket <TICKET_ID>. Review ONLY the changed files/hunks touched by implementation and fixes. Focus on whether the critical/major issues from review.md are clearly resolved and whether the ticket scope looks safe. Use the initial test-results.md as supporting signal, but do not broaden scope. If anything is uncertain, insufficiently verified, or not an unambiguous pass, say so explicitly.", "reads": ["implementation.md", "review.md", "test-results.md", "fixes.md", "plan.md", "anchor-context.md"], "output": "review-post-fix.md" },
    { "agent": "tf-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, persist research, lessons learned, ticket artifact copy, and ticket close gate. maxFixPasses=1 per run. If the quick re-check is anything other than a clear pass, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md", "research.md", "library-research.md"], "output": "close-summary.md" }
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
    { "agent": "plan-deep", "task": "Create implementation plan for ticket <TICKET_ID> using existing knowledge.", "reads": ["anchor-context.md"], "output": "plan.md" },
    { "agent": "worker", "task": "Implement ticket <TICKET_ID> per plan.", "reads": ["plan.md", "anchor-context.md"], "output": "implementation.md" },
    {
      "parallel": [
        { "agent": "reviewer", "task": "Initial review for ticket <TICKET_ID>. Review ONLY the changes introduced during this implementation. Use implementation.md to identify touched files and use git diff/show as needed to inspect changed hunks. Focus on ticket scope, acceptance criteria, and regressions in changed code; ignore unrelated pre-existing issues.", "reads": ["implementation.md", "plan.md", "anchor-context.md"], "output": "review.md" },
        { "agent": "tester", "task": "Initial tests for ticket <TICKET_ID>. Run only the most relevant ticket-scoped tests and checks you can identify with high signal. Prioritize changed modules, referenced tests, and the most direct validation commands.", "reads": ["implementation.md", "plan.md", "anchor-context.md"], "output": "test-results.md" }
      ],
      "concurrency": 2,
      "failFast": false
    },
    { "agent": "fixer", "task": "Apply one fix pass for ticket <TICKET_ID> using review.md and test-results.md. If no critical/major issues exist, record a no-op rationale.", "reads": ["review.md", "test-results.md", "implementation.md", "plan.md"], "output": "fixes.md" },
    { "agent": "reviewer", "task": "QUICK re-check for ticket <TICKET_ID>. Review ONLY the changed files/hunks touched by implementation and fixes. Focus on whether the critical/major issues from review.md are clearly resolved and whether the ticket scope looks safe. Use the initial test-results.md as supporting signal, but do not broaden scope. If anything is uncertain, insufficiently verified, or not an unambiguous pass, say so explicitly.", "reads": ["implementation.md", "review.md", "test-results.md", "fixes.md", "plan.md", "anchor-context.md"], "output": "review-post-fix.md" },
    { "agent": "tf-closer", "task": "Finalize ticket <TICKET_ID>: git commit, progress tracking, lessons learned, ticket artifact copy, and ticket close gate. maxFixPasses=1 per run. If the quick re-check is anything other than a clear pass, do not close; set tk status in_progress and add blocker note.", "reads": ["anchor-context.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md"], "output": "close-summary.md" }
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

Progress tracking and lessons learned are handled by `tf-closer` — no need to manually update `.tf/progress.md` or `.tf/AGENTS.md` in the main loop.

## tf-closer Responsibilities

The `tf-closer` agent handles all post-implementation finalization:

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
- Topic directory: `.tf/knowledge/topics/<topic-slug>/`
  - recommended files: `summary.md`, `research.md`, `library-research.md`
- Ticket research: `.tf/knowledge/tickets/<TICKET_ID>/research.md`

### D) Ticket Artifacts
Persist a compact ticket record to `.tf/tickets/<TICKET_ID>/`:
- Always write `.tf/tickets/<TICKET_ID>/close-summary.md`
- Keep it concise and durable; do not mirror every `.subagent-runs/` artifact by default
- Prefer summaries and handoff notes over copying large transient files

### E) Git Commit
1. `git rev-parse --is-inside-work-tree`
2. `git status --short`
3. Stage and commit with message: `<TICKET_ID>: <summary>`

### F) Ticket Note
- `tk add-note <TICKET_ID> "..."`

### G) Close Decision
Close only if:
- Dependencies complete
- Implementation complete
- No blocking issues (critical/major failures)
- Tests passed when tests were part of the path
- `review-post-fix.md` is a clear, unambiguous pass

Then: `tk close <TICKET_ID>`

Else: `tk status <TICKET_ID> in_progress`

### H) Fix-loop Policy (Max 1 per run)
- `maxFixPasses = 1` for each `/tf-implement` run.
- Use `review-post-fix.md` as the final go/no-go gate.
- The post-fix step is a **quick re-check**, not a second full validation pass.
- If the quick re-check is uncertain or still has critical/major issues, do not attempt additional fix passes in the same run.
- Keep ticket `in_progress`, add a clear blocker note via `tk add-note`, and suggest a follow-up run.

## Example Usage

```
/tf-implement TICKET-123                        # you decide path after analysis
/tf-implement TICKET-123 --async                # background execution (legacy)
/tf-implement TICKET-123 --clarify              # chain clarification TUI

# Interactive modes (new)
/tf-implement TICKET-123 --interactive          # supervised overlay (blocking)
/tf-implement TICKET-123 --hands-free           # agent-monitored overlay
/tf-implement TICKET-123 --dispatch             # background + notification

# Valid combinations
/tf-implement TICKET-123 --hands-free --clarify # clarify then hands-free
/tf-implement TICKET-123 --dispatch --clarify   # clarify then dispatch
```
