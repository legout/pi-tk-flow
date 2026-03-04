# Brainstorm Brief: Ralph Wiggum Method for pi-tk-flow

**Feature**: Add interactive/background execution mode for ticket implementation
**Date**: 2026-03-04
**Status**: Decision-needed

---

## Problem Frame

### Current State
- `/tk-implement` uses the `subagent` tool with `async: true` for background execution
- Users cannot supervise or interact with running implementations in real-time
- No way to handoff a running implementation to background and reattach later
- The `--async` flag creates fire-and-forget execution without user oversight

### The "Ralph Wiggum Method"
Named after the Simpson's character's memorable "I'm in danger!" catchphrase, this method represents **interactive shell-based execution** where:
- Users can watch implementation progress in real-time via an overlay
- Users can take over control at any moment (Ctrl+T to transfer output)
- Sessions can be backgrounded (Ctrl+B) and reattached later (`/attach`)
- Agent can be notified on completion (dispatch mode) without polling

### Why This Matters
1. **Visibility**: Users see what the agent is doing, building trust
2. **Control**: Users can intervene when the agent goes off-track
3. **Flexibility**: Background long-running implementations, reattach when needed
4. **Efficiency**: Dispatch mode eliminates polling overhead

---

## Goals & Non-Goals

### Goals
- ✅ Enable interactive execution mode with user supervision capability
- ✅ Enable background/dispatch mode with automatic completion notification
- ✅ Allow session management (background, reattach, list sessions)
- ✅ Maintain backward compatibility with existing `/tk-implement --async`
- ✅ Follow existing pi-tk-flow patterns (flag parsing, subagent guardrails)

### Non-Goals
- ❌ Creating new subagents (must use existing agents only)
- ❌ Modifying existing agent definitions
- ❌ Building a separate TUI (leverage pi's overlay system)
- ❌ Replacing the `--async` flag (add new complementary flags)

---

## Approach Options

### Option A: New Extension Command `/tk-interactive`

**Description**: Create a dedicated command that wraps ticket implementation in interactive shell modes.

**Implementation**:
```typescript
// extensions/tk-interactive.ts
pi.registerCommand("tk-interactive", {
  description: "Run ticket implementation in interactive/background mode",
  handler: async (args, ctx) => {
    // Parse: /tk-interactive <TICKET_ID> [--interactive|--background|--dispatch]
    const { ticketId, mode } = parseArgs(args);

    // Invoke interactive_shell tool directly
    const result = await ctx.tools.interactive_shell({
      command: `pi "/tk-implement ${ticketId}"`,
      mode: mode, // 'interactive' | 'hands-free' | 'dispatch'
      background: mode === 'dispatch',
    });
  }
});
```

**Trade-offs**:
| Aspect | Pros | Cons |
|--------|------|------|
| **Separation** | Clean separation of concerns | Fragmented UX (two commands) |
| **Discovery** | Explicit command is discoverable | More commands to remember |
| **Maintenance** | Independent evolution | Duplicate flag parsing |
| **Testing** | Isolated testing | More test surface |

**Complexity**: Medium - requires new extension, but straightforward implementation

---

### Option B: Extend `/tk-implement` with New Flags (Recommended)

**Description**: Add `--interactive`, `--hands-free`, and `--dispatch` flags to the existing command.

**Implementation**:
```markdown
# In prompts/tk-implement.md

## Parse Input and Runtime Flags

Supported flags:
- `--async` → run subagent execution in background mode (`async: true`) [EXISTING]
- `--clarify` → open chain clarification TUI (`clarify: true`) [EXISTING]
- `--interactive` → run in interactive shell with user supervision [NEW]
- `--hands-free` → run in hands-free mode (agent monitors, user can takeover) [NEW]
- `--dispatch` → run in dispatch mode (agent notified on completion) [NEW]
```

**Execution Logic**:
```markdown
## Interactive Shell Integration

When `--interactive`, `--hands-free`, or `--dispatch` is set:

1. Skip the normal subagent chain execution
2. Invoke `interactive_shell` tool directly:
   - command: `pi "/tk-implement <TICKET_ID> --clarify=<RUN_CLARIFY>"`
   - mode: determined by flag (interactive/hands-free/dispatch)
   - background: true if dispatch mode

3. For dispatch mode: no polling needed - notification arrives on completion
4. For hands-free mode: agent polls every 60s for status updates
5. For interactive mode: user controls the session entirely
```

**Trade-offs**:
| Aspect | Pros | Cons |
|--------|------|------|
| **UX** | Single command, familiar workflow | More flags to learn |
| **Compatibility** | `--async` still works | Potential confusion between async/dispatch |
| **Implementation** | Extends existing logic | Modifies core workflow file |
| **Testing** | Extends existing tests | More test combinations |

**Complexity**: Low-Medium - leverages existing infrastructure

---

### Option C: Hybrid - Flag + Helper Script

**Description**: Add a single `--shell` flag that delegates to a helper bash script for mode selection.

**Implementation**:
```bash
# scripts/tk-shell.sh
#!/bin/bash
TICKET_ID=$1
MODE=$2  # interactive, hands-free, dispatch

case $MODE in
  interactive)
    pi "/tk-implement $TICKET_ID"  # User runs this manually in a shell
    ;;
  hands-free)
    # Uses pi's --background flag or tmux session
    ;;
  dispatch)
    # Uses pi's notification system
    ;;
esac
```

**Trade-offs**:
| Aspect | Pros | Cons |
|--------|------|------|
| **Simplicity** | Minimal pi changes | External dependency |
| **Flexibility** | Easy to modify script | Harder to test |
| **Integration** | Works with any shell | Less discoverable |
| **Portability** | Works everywhere | Requires bash |

**Complexity**: Low - but introduces external script dependency

---

## Recommended Direction

**Choose Option B: Extend `/tk-implement` with New Flags**

### Rationale

1. **Minimal Disruption**: Extends existing workflow users already know
2. **Tool Compatibility**: `interactive_shell` tool is already available in pi
3. **Clear Semantics**:
   - `--async` = fire-and-forget (current behavior)
   - `--interactive` = user supervision with takeover capability
   - `--dispatch` = background with notification
   - `--hands-free` = agent monitors with periodic updates
4. **No New Agents**: Uses existing subagent infrastructure
5. **Testable**: Can extend existing path-based tests

### Implementation Path

**Phase 1: Flag Parsing** (15 min)
- Add new flags to `prompts/tk-implement.md`
- Parse and validate flag combinations (e.g., `--interactive` + `--async` = error)

**Phase 2: Interactive Shell Integration** (30 min)
- Add conditional logic to check for interactive flags
- When present, invoke `interactive_shell` instead of `subagent` chain
- Pass ticket context and chain configuration appropriately

**Phase 3: Session Management** (15 min)
- Document session management commands (`/attach`, Ctrl+B, Ctrl+Q)
- Add guidance for checking session status

**Phase 4: Testing** (30 min)
- Test flag parsing
- Test interactive mode manually
- Test dispatch mode with notification
- Verify backward compatibility with `--async`

---

## Risks

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **interactive_shell tool limitations** | Medium | High | Test tool behavior early; document constraints |
| **Session state loss** | Low | Medium | Auto-save transcripts; handoff snapshots |
| **Flag combination conflicts** | Medium | Low | Clear validation and error messages |
| **Performance overhead** | Low | Low | Dispatch mode eliminates polling |

### UX Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **User confusion (async vs dispatch)** | Medium | Medium | Clear documentation; deprecate `--async` eventually |
| **Overlay discoverability** | Medium | Low | Document keyboard shortcuts prominently |
| **Session management complexity** | Low | Medium | Provide simple commands (`/attach`, `/sessions`) |

---

## Open Questions

### Technical Questions

1. **Can `interactive_shell` be invoked from within a prompt template?**
   - Need to verify: Do prompt templates have access to all tools?
   - Alternative: Extension command that reads the prompt

2. **How does ticket context get passed to interactive shell?**
   - Option 1: Pass ticket ID, let inner agent read anchor-context.md
   - Option 2: Pre-seed the command with full context (may hit length limits)

3. **What happens to session artifacts?**
   - Subagent runs write to `.subagent-runs/<TICKET_ID>/`
   - Interactive shell sessions have their own artifact directories
   - Need to align or document the difference

### Design Questions

4. **Should `--async` be deprecated in favor of `--dispatch`?**
   - Pro: Cleaner semantics (dispatch = background + notification)
   - Con: Breaking change for existing users
   - Recommendation: Keep both, document equivalence

5. **Should interactive mode allow the full subagent chain?**
   - Current design: Interactive shell runs `pi "/tk-implement <ID>"`
   - This creates a nested pi invocation
   - Alternative: Extract chain logic into reusable function

6. **How to handle `--clarify` with interactive modes?**
   - `--clarify` opens a TUI for chain review
   - Conflict: Interactive shell already has an overlay
   - Recommendation: Incompatible flags, clear error message

---

## Decision Checklist

Before proceeding with implementation, confirm:

- [ ] **Tool Verification**: Tested `interactive_shell` tool modes (interactive, hands-free, dispatch)
- [ ] **Flag Design**: Decided on exact flag names and semantics
- [ ] **Backward Compatibility**: Confirmed `--async` still works as expected
- [ ] **Session Management**: Documented `/attach`, `/sessions`, keyboard shortcuts
- [ ] **Error Handling**: Defined behavior for invalid flag combinations
- [ ] **Testing Strategy**: Planned test cases for each mode
- [ ] **Documentation**: Drafted user guide for new modes

---

## Next Steps

1. **Research Spike** (30 min)
   - Test `interactive_shell` tool directly with a simple command
   - Verify tool availability from prompt templates
   - Document session management behavior

2. **Design Review** (15 min)
   - Confirm flag names and semantics
   - Decide on `--async` deprecation timeline
   - Review with stakeholders

3. **Implementation** (1-2 hours)
   - Phase 1-4 from Recommended Direction

4. **Documentation** (30 min)
   - Update README with new modes
   - Add examples for each mode
   - Document keyboard shortcuts

---

## Appendix: interactive_shell Tool Reference

From pi tool documentation:

**Modes**:
- `interactive` (default): User controls the session
- `hands-free`: Agent monitors, user can takeover by typing
- `dispatch`: Agent notified on completion, no polling needed

**Key Features**:
- Overlay for real-time output viewing
- Ctrl+T: Transfer output to agent context
- Ctrl+B: Background the session
- Ctrl+Q: Detach menu (transfer/background/kill)
- `/attach <sessionId>`: Reattach to background session
- Auto-save transcripts and handoff snapshots

**Rate Limiting**: Queries limited to once every 60 seconds in hands-free mode
