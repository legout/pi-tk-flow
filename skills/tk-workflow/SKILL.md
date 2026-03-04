# tk-workflow Skill

Operator guidance for the pi-tk-flow ticket-driven development workflow.

## When to Use Which Execution Mode

### Quick Decision Tree

```
Need to implement a ticket?
│
├─ Can run unattended? ──YES──► Default mode (agent picks Path A/B/C)
│
├─ Want real-time supervision? ──YES──► --interactive
│   └─ You watch the overlay, control with Ctrl+T/Ctrl+B/Ctrl+Q
│
├─ Want oversight without babysitting? ──YES──► --hands-free
│   └─ Agent polls ~60s, you can take over anytime
│
└─ Long-running, check back later? ──YES──► --dispatch
    └─ Fire-and-forget, agent notified on completion
```

### Mode Selection Guide

| Scenario | Recommended Mode | Why |
|----------|-----------------|-----|
| Quick bug fix (<50 LOC) | Default | No need for interactive overhead |
| Complex feature with uncertainty | `--interactive` | Catch issues early, provide guidance |
| Routine refactor with good tests | `--hands-free` | Monitor without full attention |
| Research-heavy spike | `--dispatch` | May take hours, notification on done |
| CI/CD integration | `--dispatch` | Headless, predictable |
| Learning new codebase | `--interactive` | Watch how agents navigate code |
| Production hotfix | `--interactive` | Tight control over changes |
| Existing automation using `--async` | `--async` (legacy) | Backward compatibility only |

### When to Use Legacy `--async`

The `--async` flag remains available for backward compatibility with existing automation scripts. For new workflows:

- **Prefer `--dispatch`** for fire-and-forget background execution with automatic notification
- **Use `--async`** only when maintaining existing scripts that cannot be updated immediately

Legacy `--async` will continue to work, but new interactive modes (`--hands-free`, `--dispatch`) provide better visibility and control.

### Clarify Flag Combinations

The `--clarify` flag opens a TUI for confirming chain steps before execution:

```bash
# Good: Clarify what will happen, then let it run hands-free
/tk-implement TICKET-123 --hands-free --clarify

# Good: Clarify then dispatch
/tk-implement TICKET-123 --dispatch --clarify

# Invalid: Interactive already shows everything, clarify conflicts
/tk-implement TICKET-123 --interactive --clarify  # ❌ ERROR
```

## Session Lifecycle

### Starting a Session

```bash
# Interactive - you supervise
/tk-implement TICKET-123 --interactive
# → Overlay opens showing live output
# → Ctrl+T to transfer output to agent context
# → Ctrl+B to background (keep running, check later)
# → Ctrl+Q for detach menu (transfer/background/kill)

# Hands-free - agent monitors
/tk-implement TICKET-123 --hands-free
# → Returns immediately with session ID
# → Agent polls every ~60 seconds
# → You can /attach anytime to take over

# Dispatch - notification on complete
/tk-implement TICKET-123 --dispatch
# → Returns immediately with session ID
# → Runs headless
# → Agent notified when done
```

### During a Session

**Keybindings (when attached to interactive/hands-free):**

| Key | Action |
|-----|--------|
| `Ctrl+T` | Transfer output to agent context and close overlay |
| `Ctrl+B` | Background session (dismiss overlay, keep running) |
| `Ctrl+Q` | Open detach menu with transfer/background/kill options |

**Slash commands (anytime):**

```bash
/sessions                    # List all active sessions
/attach calm-reef           # Reattach to specific session
/attach                     # Interactive selector
/dismiss calm-reef          # Kill and cleanup specific session
/dismiss                    # Dismiss all sessions
```

### After Completion

Session metadata persists in `.subagent-runs/<ticket>/session.json`:

```json
{
  "mode": "dispatch",
  "sessionId": "calm-reef",
  "startedAt": "2026-03-04T12:34:56Z",
  "command": "pi \"/tk-implement TICKET-123\"",
  "status": "completed"
}
```

Chain outputs are in the same directory:
- `.subagent-runs/TICKET-123/anchor-context.md`
- `.subagent-runs/TICKET-123/plan.md`
- `.subagent-runs/TICKET-123/implementation.md`
- `.subagent-runs/TICKET-123/review.md`
- etc.

## Troubleshooting

### Cannot reattach to session

**Symptom:** `/attach my-session` says "Session not found"

**Check:**
1. Session may have completed — check `.subagent-runs/<ticket>/session.json` for `status: "completed"`
2. Session may have been dismissed — check `/sessions` list
3. Different working directory — session IDs are scoped to cwd

### No notification from dispatch

**Symptom:** Ran `--dispatch` but agent wasn't notified

**Check:**
1. Session may still be running — check `/sessions` or `.subagent-runs/<ticket>/session.json`
2. Process may have crashed — check if `session.json` has `status: "failed"`
3. Notification goes to the agent that called `interactive_shell` — if you switched agents, check the original

### Interactive overlay won't open

**Symptom:** `--interactive` runs but no overlay appears

**Check:**
1. `PI_TK_INTERACTIVE_CHILD` env var may be set (recursion guard)
2. Another overlay may already be open (pi allows only one at a time)
3. TUI may not be available in current context (e.g., headless SSH without display)

### Hands-free polling too slow/fast

**Symptom:** Updates feel too infrequent or too chatty

The default polling is:
- `updateInterval: 60000` (max 60s between updates)
- `quietThreshold: 8000` (emit update after 8s silence)

These are not configurable via flags currently — you can take over with `/attach` anytime for real-time updates.

## Common Patterns

### Pattern: Supervised Start, Background Finish

```bash
# Start interactive, then background when comfortable
/tk-implement TICKET-123 --interactive
# ... watch initial progress ...
# Ctrl+B to background
# ... do other work ...
/attach  # later, to check progress
```

### Pattern: Clarify, Then Dispatch

```bash
# Review the plan, then let it run
/tk-implement TICKET-123 --dispatch --clarify
# ... TUI opens showing planned chain steps ...
# Approve steps, then session runs headless
# Agent notified when complete
```

### Pattern: Batch Dispatch Multiple Tickets

```bash
# Queue up several tickets to run in parallel
/tk-implement TICKET-100 --dispatch
/tk-implement TICKET-101 --dispatch
/tk-implement TICKET-102 --dispatch
# ... check /sessions for status of all three
```

## Guardrails and Constraints

1. **Mutual Exclusion:** Only one of `--interactive`, `--hands-free`, `--dispatch` at a time
2. **No Async Mixing:** New interactive flags cannot combine with `--async` (legacy)
3. **No Interactive + Clarify:** Overlay conflict — use hands-free or dispatch with clarify instead
4. **Recursion Guard:** Nested invocations automatically disable interactive routing (via `PI_TK_INTERACTIVE_CHILD`)
5. **Scope Preservation:** Agent scope (user/project) is preserved through interactive sessions

## Migration from --async

If you previously used `--async` for background execution:

| Old | New | Reason |
|-----|-----|--------|
| `--async` | `--dispatch` | Cleaner notification model |
| `--async --clarify` | `--dispatch --clarify` | Clarify works with dispatch |

Legacy `--async` continues to work but new interactive modes are preferred for human-in-the-loop workflows.

## See Also

- `README.md` — Full workflow documentation
- `prompts/tk-implement.md` — Implementation prompt template
- `.tf/plans/*/02-spec.md` — Design specifications for interactive features
