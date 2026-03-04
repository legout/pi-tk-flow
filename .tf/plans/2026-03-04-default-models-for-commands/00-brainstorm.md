# Brainstorm: Default Models for Commands

**Topic**: Define default models for commands to set both subagent and main loop models
**Mode**: Feature
**Date**: 2026-03-04
**Status**: Decision-Ready

---

## Problem Frame

### Current State

The pi-tk-flow package provides commands (`/tk-implement`, `/tk-brainstorm`, `/tk-plan`, etc.) that orchestrate complex workflows using subagents. Currently:

1. **Subagent model selection**: Each agent can define a preferred model in its frontmatter, and callers can override this with the `model` parameter in `subagent` tool calls
2. **Main loop model selection**: Commands run using pi's default model (from global or project settings) with **no per-command override mechanism**

### Pain Points

1. **Cost optimization**: Users cannot easily switch to cheaper/faster models for specific commands without changing global settings
2. **Task-specific models**: Some tasks (planning, reviewing) may benefit from different models than implementation
3. **Testing workflows**: No way to test commands with different models without affecting other work
4. **Inconsistent control**: Subagent models are configurable, but the orchestrating main agent is not

### Opportunity

Add model configuration flags to tk commands that control **both**:
- The main loop model (the agent running the command prompt)
- Default subagent model selection (optional override for all spawned subagents)

---

## Goals & Non-Goals

### Goals

1. **Enable per-command model selection** via command-line flags
2. **Support dual model control**: independently set main loop model and subagent model defaults
3. **Maintain backward compatibility**: existing workflows continue without changes
4. **Follow existing patterns**: use consistent flag parsing with other tk commands
5. **Respect settings hierarchy**: global → project → command-line precedence

### Non-Goals

1. **Persistent command-specific defaults** (no `.tk-implement.json` config files in this iteration)
2. **Dynamic agent reconfiguration** (cannot modify agent definitions at runtime per tk-implement guardrails)
3. **Provider configuration** (assumes providers/API keys already configured in models.json)
4. **Session-level persistence** (model changes apply only to single command invocation)

---

## Approach Options

### Option A: Dual Flags (Recommended)

Add two independent flags to each command:

```
--model <model-id>           # Sets main loop model
--subagent-model <model-id>  # Sets default for all subagents
```

**Usage examples:**
```bash
/tk-implement TICKET-123 --model claude-sonnet-4-5
/tk-implement TICKET-123 --model claude-sonnet-4-5 --subagent-model claude-haiku-4-5
/tk-brainstorm topic --subagent-model claude-haiku-4-5
```

**Implementation:**
1. Parse flags in command prompt (using existing `parseFlag()` pattern)
2. If `--model` is set:
   - Call `pi.setModel(<model-id>)` at command start (ExtensionAPI research required)
   - Restores previous model after command completes (or let session handle it)
3. If `--subagent-model` is set:
   - Pass `model: <model-id>` to all `subagent` tool calls in the command
   - Agent-defined models still overridden by this runtime parameter

**Pros:**
- ✅ Maximum flexibility: independent control of main and subagent models
- ✅ Explicit and clear: user knows exactly what each flag does
- ✅ Backward compatible: optional flags, defaults to current behavior
- ✅ Follows existing flag patterns

**Cons:**
- ⚠️ Two flags to learn/maintain
- ⚠️ Requires ExtensionAPI research for `pi.setModel()` behavior
- ⚠️ Model restoration after command needs investigation

**Trade-offs:**
- More flags = more control but slightly higher complexity
- Independent flags allow optimization (expensive main model + cheap subagents)

---

### Option B: Single Unified Flag

Add one flag that controls both:

```
--model <model-id>  # Sets both main loop and all subagents
```

**Usage examples:**
```bash
/tk-implement TICKET-123 --model claude-sonnet-4-5
```

**Implementation:**
1. Parse `--model` flag
2. Set main loop model via `pi.setModel()`
3. Pass `model: <model-id>` to all subagent calls

**Pros:**
- ✅ Simpler: single flag to understand
- ✅ Backward compatible
- ✅ Good default for "use this model everywhere"

**Cons:**
- ❌ Less flexible: cannot mix models (e.g., Sonnet for planning, Haiku for scouts)
- ❌ May not be cost-optimal for complex workflows
- ❌ Doesn't leverage agent-specific model expertise

**Trade-offs:**
- Simplicity over flexibility
- May lead to users wanting more control later

---

### Option C: Settings-Based Configuration

Add a configuration file per command type:

```
# .pi/commands/tk-implement.json
{
  "defaultModel": "claude-sonnet-4-5",
  "subagentModel": "claude-haiku-4-5"
}
```

**Usage:**
```bash
/tk-implement TICKET-123  # Uses .pi/commands/tk-implement.json if exists
/tk-implement TICKET-123 --model X  # Flag overrides config
```

**Implementation:**
1. At command start, look for `.pi/commands/tk-<command>.json`
2. Load defaults if file exists
3. Allow flags to override config values
4. Apply models as in Option A

**Pros:**
- ✅ Persistent defaults per command type
- ✅ Project-specific optimization
- ✅ Still allows flag overrides

**Cons:**
- ❌ More complex: new config system to maintain
- ❌ Hidden behavior: not obvious what model is being used
- ❌ Config file sprawl
- ❌ Harder to debug

**Trade-offs:**
- Convenience over transparency
- More infrastructure for persistence

---

## Recommended Direction

**Use `pi-prompt-template-model` extension** for model control, with documentation for subagent model best practices.

### Rationale

1. **Proven solution**: The extension is battle-tested and handles edge cases (auto-restore, fallback, auth checking)
2. **No custom code needed**: No need to build and maintain custom extension code
3. **Clean separation**: Model config lives in prompt frontmatter, not in code
4. **User empowerment**: Users can create their own prompt variants with different models
5. **Composable**: Works seamlessly with existing tk commands

### Implementation Strategy

1. **Phase 1**: Document `pi-prompt-template-model` as optional dependency
   - Add to README: "For per-command model control, install `pi-prompt-template-model`"
   - Show example: adding `model: claude-sonnet-4-20250514` to prompt frontmatter

2. **Phase 2**: Add model frontmatter to tk command prompts (optional)
   - Add `model: claude-sonnet-4-20250514` to `prompts/tk-implement.md`
   - Add appropriate models to other prompts (`tk-brainstorm`, `tk-plan`, etc.)
   - Use fallback lists for flexibility: `model: claude-haiku-4-5, claude-sonnet-4-20250514`

3. **Phase 3**: Document subagent model best practices
   - Agent definitions can specify `model` in frontmatter
   - `subagent` tool calls can override with `model` parameter
   - Show examples of cost-optimized vs quality-optimized configurations

---

## Risks

### High Priority

1. **Extension Dependency** (Low)
   - **Risk**: Users without `pi-prompt-template-model` won't have model switching
   - **Mitigation**: Document as optional; prompts work normally without it
   - **Impact**: Graceful degradation - commands work with default model

2. **API Key Availability** (Medium)
   - **Risk**: User specifies model without configured API key
   - **Mitigation**: Extension handles this with clear error notifications
   - **Impact**: Command fails fast with actionable guidance

### Medium Priority

4. **Precedence Confusion** (Low)
   - **Risk**: Users unclear on model precedence (agent vs flag vs settings)
   - **Mitigation**: Document hierarchy clearly: flag > agent-defined > settings
   - **Impact**: Minor UX friction

5. **Cost Transparency** (Low)
   - **Risk**: Users may not realize model choice affects cost
   - **Mitigation**: Consider cost hints in help text (future enhancement)
   - **Impact**: Unexpected API bills

---

## Research Findings ✅

### ExtensionAPI Model Control - CONFIRMED AVAILABLE

**`pi.setModel(model)` exists and is documented:**

```typescript
const model = ctx.modelRegistry.find("anthropic", "claude-sonnet-4-5");
if (model) {
  const success = await pi.setModel(model);
  if (!success) {
    ctx.ui.notify("No API key for this model", "error");
  }
}
```

**Key behaviors:**
- Returns `false` if no API key is available for the model
- Changes the model for the current session
- Can be called from extension command handlers
- Model registry accessible via `ctx.modelRegistry`

### YAML Frontmatter Model Field - SUPPORTED VIA EXTENSION

**The `pi-prompt-template-model` extension adds `model`, `skill`, and `thinking` frontmatter support:**

Repository: https://github.com/nicobailon/pi-prompt-template-model

```markdown
---
description: Debug Python in tmux REPL
model: claude-sonnet-4-20250514
skill: tmux
thinking: medium
---
Start a Python REPL session and help me debug: $@
```

**Frontmatter fields supported:**
| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `model` | Yes | - | Model ID, `provider/model-id`, or comma-separated list for fallback |
| `skill` | No | - | Skill name to inject into system prompt |
| `thinking` | No | - | Thinking level: `off`, `minimal`, `low`, `medium`, `high`, `xhigh` |
| `description` | No | - | Shown in autocomplete |
| `restore` | No | `true` | Restore previous model and thinking level after response |

**Key features:**
- ✅ Auto-switches model before prompt execution
- ✅ Auto-restores previous model after completion
- ✅ Supports model fallback lists (e.g., `claude-haiku-4-5, claude-sonnet-4-20250514`)
- ✅ Supports explicit provider (`anthropic/claude-sonnet-4-20250514`)
- ✅ Injects skills directly into system prompt (no read tool round-trip)
- ✅ Works with subdirectories for namespaced commands

### Recommended Approach: Use `pi-prompt-template-model`

Instead of building custom flag parsing, **use the existing extension** which provides exactly what we need:

1. **Install the extension:**
   ```bash
   pi install npm:pi-prompt-template-model
   ```

2. **Add `model` frontmatter to tk command prompts:**
   ```markdown
   ---
   description: Analyze and implement any tk ticket
   model: claude-sonnet-4-20250514
   ---
   Implement ticket from `$@` ...
   ```

3. **Users can override per invocation** by using the `/model` command before running the tk command, or by creating their own prompt wrappers.

**Benefits:**
- ✅ No custom extension code needed
- ✅ Battle-tested implementation with auto-restore
- ✅ Supports model fallback lists
- ✅ Clean separation: model config in prompt, not in code
- ✅ Users can create their own variants with different models

## Open Questions

### Research Required

1. **❓ Model Session Scoping**
   - **Question**: Does `pi.setModel()` affect the current session or command only?
   - **Why**: Determines if we need explicit model restoration after command completes
   - **Action**: Test with prototype command
   - **Priority**: High - affects implementation design
   - **Hypothesis**: Model change persists for session; may need to save/restore previous model

2. **❓ Subagent Model Precedence**
   - **Question**: Does runtime `model` parameter override agent frontmatter `model` field?
   - **Why**: Confirms `--subagent-model` flag behavior
   - **Action**: Read `/opt/homebrew/Cellar/node/25.7.0/lib/node_modules/@mariozechner/pi-coding-agent/src/tools/subagent.ts`
   - **Priority**: Medium - well-documented but needs verification

### Design Decisions

3. **🤔 Approach: Use `pi-prompt-template-model` vs Build Custom**
   - **Question**: Should we use the existing `pi-prompt-template-model` extension or build custom flag parsing?
   - **Analysis**:
     - `pi-prompt-template-model`: Battle-tested, auto-restore, fallback support, no code needed
     - Custom flags: More control, can add `--subagent-model`, more complex
   - **Recommendation**: Use `pi-prompt-template-model` for main loop model; document it as optional dependency

4. **🤔 Subagent Model Control**
   - **Question**: How to control subagent models?
   - **Options**:
     - Add `model` field to agent definitions (already supported)
     - Pass `model` parameter in `subagent` tool calls (already supported)
     - Create wrapper agents with different models
   - **Recommendation**: Document best practices; no code changes needed
   - **Question**: Should it be `--subagent-model` or `--agent-model`?
   - **Consideration**: "subagent" is more precise but longer
   - **Recommendation**: Use `--subagent-model` for clarity

5. **🤔 Error Handling**
   - **Question**: What happens if invalid model ID is provided?
   - **Options**:
     - Fail fast with error
     - Fall back to default with warning
   - **Recommendation**: Fail fast with clear error (better UX)

6. **🤔 Help Text**
   - **Question**: Should help text list available models?
   - **Consideration**: Models are dynamic (models.json)
   - **Recommendation**: Point to `pi models list` command

---

## Decision Checklist

Before proceeding with implementation, confirm:

- [x] **ExtensionAPI Research Complete**
  - [x] Verified `pi.setModel()` exists and works from command handlers
  - [x] Found `pi-prompt-template-model` extension that provides model frontmatter support
  - [x] Confirmed extension handles model restoration automatically

- [ ] **Subagent Behavior Confirmed**
  - [ ] Verified runtime `model` parameter overrides agent frontmatter
  - [ ] Understood precedence: flag > agent > settings

- [ ] **Design Approved**
  - [ ] Option A (dual flags) confirmed as direction
  - [ ] Flag names finalized: `--model`, `--subagent-model`
  - [ ] Error handling strategy decided (fail fast vs fallback)

- [ ] **Implementation Plan Defined**
  - [ ] Phase 1 pilot command selected (recommend: `/tk-implement`)
  - [ ] Rollout sequence for other commands defined
  - [ ] Testing strategy documented

- [ ] **Documentation Planned**
  - [ ] User-facing docs for new flags
  - [ ] Precedence diagram (flag > agent > settings)
  - [ ] Troubleshooting guide (API keys, invalid models)

- [ ] **Backward Compatibility Verified**
  - [ ] Existing commands work without flags
  - [ ] No breaking changes to subagent tool interface
  - [ ] Settings hierarchy preserved

---

## Next Steps

1. **Documentation** (30 min)
   - Add `pi-prompt-template-model` to optional dependencies in README
   - Create example showing model frontmatter usage
   - Document subagent model best practices

2. **Phase 1: Add model frontmatter to prompts** (1 hour)
   - Add `model: claude-sonnet-4-20250514` to `prompts/tk-implement.md`
   - Add appropriate models to other prompts
   - Test with extension installed

3. **Phase 2: Create example configurations** (1 hour)
   - Cost-optimized: Haiku for scouts, Sonnet for planners
   - Quality-optimized: Sonnet/Opus for all
   - Document in `.tf/knowledge/topics/model-configuration.md`

4. **Phase 3: Update agent definitions** (30 min)
   - Review agent definitions for appropriate model settings
   - Add `model` field to agent frontmatter where beneficial

---

## References

- Anchor context: `.subagent-runs/tk-brainstorm/default-models-for-commands/anchor-context.md`
- Brainstorm draft: `.subagent-runs/tk-brainstorm/default-models-for-commands/f4ca5607/brainstorm-draft.md`
- Code patterns: `extensions/tk-bootstrap.ts`, `prompts/tk-implement.md`
- Related docs: pi documentation on model configuration
