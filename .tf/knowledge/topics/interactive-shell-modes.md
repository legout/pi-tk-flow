# Interactive Shell Modes

## Overview

The `interactive_shell` tool supports three execution modes for delegating to CLI agents:

| Mode | Use Case | Blocking | User Interaction |
|------|----------|----------|------------------|
| `interactive` | User-supervised sessions | Yes | Full control |
| `hands-free` | Agent-monitored execution | No (async) | Can take over anytime |
| `dispatch` | Fire-and-forget | No (background) | No interaction needed |

## Mode Details

### Interactive Mode
- User watches overlay, has full control
- Agent blocked until session ends
- Best for: debugging, exploratory work, user guidance needed

### Hands-Free Mode
- Agent monitors with periodic updates
- Returns sessionId immediately
- User can type to take over
- Best for: long-running tasks where agent should check in

### Dispatch Mode
- Agent notified on completion via triggerTurn
- No polling required
- Can run headless with `background: true`
- Best for: fire-and-forget tasks, batch operations

## Key Parameters

```json
{
  "command": "pi \"/task\"",
  "mode": "interactive|hands-free|dispatch",
  "background": true,  // dispatch only, headless
  "handsFree": {       // hands-free only
    "updateMode": "on-quiet|interval",
    "quietThreshold": 8000,
    "updateInterval": 60000,
    "autoExitOnQuiet": false
  }
}
```

## Session Management

- Sessions stored in background
- Reattach: `interactive_shell({ attach: "sessionId" })`
- List: `interactive_shell({ listBackground: true })`
- Dismiss: `interactive_shell({ dismissBackground: true })`

## Integration Patterns

### Nested Command Pattern
When a command wrapper invokes itself:
1. Check for recursion guard env var at entry
2. If set, skip wrapper logic, run core implementation
3. If not set, set env var and invoke nested command

```bash
# Outer call
PI_TK_INTERACTIVE_CHILD=1 pi "/tk-implement TICKET-123"
```

### Session Metadata Persistence
Store session info for later retrieval:
```json
{
  "mode": "dispatch",
  "sessionId": "calm-reef",
  "startedAt": "2026-03-04T12:34:56Z",
  "command": "pi \"/tk-implement TICKET-123\"",
  "status": "pending"
}
```

## Source
- Discovered in: ptf-53pu (2026-03-04)
- Related: pi-interactive-shell extension
