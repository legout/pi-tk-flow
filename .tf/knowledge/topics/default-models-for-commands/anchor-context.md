# Anchor Context

## Topic Summary
- **Topic**: Define default models for commands to set both subagent and main loop models
- **Objective**: Add support for specifying default models in tk commands (tk-implement, tk-brainstorm, tk-plan, etc.) that control both the subagent model selection and the main loop model for each command invocation
- **Scope / Boundaries**: This is a feature request for the pi-tk-flow package. It affects how commands like `/tk-implement`, `/tk-brainstorm`, `/tk-plan` can accept model overrides that apply to both subagents spawned during execution and the main loop model running the orchestrating logic

## Existing Architecture Context

### pi Model Configuration (from docs)

1. **Global Settings** (`~/.pi/agent/settings.json`):
   - `defaultProvider`: Default provider (e.g., "anthropic", "openai")
   - `defaultModel`: Default model ID
   - `defaultThinkingLevel`: Thinking budget level

2. **Project Settings** (`.pi/settings.json`):
   - Same structure as global, with project-level overrides

3. **Model Configuration** (`~/.pi/agent/models.json`):
   - Custom providers and models (Ollama, vLLM, LM Studio, proxies)
   - Per-model overrides for cost, context window, max tokens, etc.

### Subagent Model Configuration

From the subagent extension documentation:
- Agents are defined in markdown files with YAML frontmatter
- Frontmatter can include `model` field: `model: claude-haiku-4-5`
- The `subagent` tool accepts a `model` override parameter in the execution call

Example agent definition:
```yaml
---
name: scout
description: Fast codebase recon
tools: read, grep, find, ls
model: claude-haiku-4-5
---
System prompt...
```

### tk Commands Structure

The tk-flow package provides these commands (from tk-bootstrap.ts and prompts):
- `/tk-bootstrap` - Install workflow templates
- `/tk-implement` - Implement tickets with path selection (A/B/C)
- `/tk-brainstorm` - Brainstorm features/refactors
- `/tk-plan` - Create implementation plans
- `/tk-plan-check` - Verify plan quality
- `/tk-plan-refine` - Improve plans

### Current Flag Parsing Pattern

From tk-bootstrap.ts, commands use flag parsing:
```typescript
function parseFlag(args: string, flag: string): boolean { ... }
function parseScope(args: string): Scope { ... }
```

Prompts define flags in YAML frontmatter and parse `$@` for arguments.

## Constraints & Assumptions

### Technical Constraints
1. **Extension API**: Must work within pi's ExtensionAPI pattern
2. **Flag Parsing**: Should follow existing flag parsing conventions (e.g., `--scope`, `--dry-run`)
3. **Settings Hierarchy**: Should respect global → project → command-level precedence
4. **Backward Compatibility**: Existing workflows should continue to work without changes

### Operational Constraints
1. **Model Availability**: Users must have API keys configured for specified models
2. **Provider Support**: Feature should work with any provider configured in models.json
3. **No Agent Creation**: Per tk-implement rules, cannot create new agents dynamically

### Assumptions Needing Validation
- The main loop model can be overridden per-command (not just subagents)
- There exists an API or mechanism to set the model for the current session/command
- The subagent `model` parameter in the tool call actually overrides agent-defined models

## Research Gaps

1. **Main Loop Model Override**: How can a command programmatically set/override the main loop model? Is there an ExtensionAPI method for this?
   - `pi.setModel()` exists in ExtensionAPI - need to verify it works from command handlers
   - Need to understand when/how to call it during command execution

2. **Command-level Settings**: What's the best pattern for command-specific model defaults?
   - Option A: Flag on each command (`--model claude-sonnet-4-5`)
   - Option B: Settings file per command (`.tk-implement.json`)
   - Option C: Frontmatter in prompt templates

3. **Per-Agent Model vs Global Override**: How does subagent model selection precedence work?
   - Agent definition `model` field vs runtime `model` parameter
   - Settings-based defaults vs command-line overrides

4. **Session Persistence**: Do model changes persist beyond a single command?
   - Does `pi.setModel()` affect the current session or just the subagent?
   - How to scope model changes to a single command invocation

## Testing/Validation Considerations

### Validation Approach
- Test with different provider/model combinations
- Verify model changes don't leak between commands
- Test backward compatibility (existing commands without model flags)
- Verify subagent model selection respects override hierarchy

### Test Scenarios
1. `/tk-implement TICKET --model X` → Main loop uses X, subagents use their configured models or X
2. `/tk-brainstorm topic --subagent-model Y` → Only subagents use Y, main loop uses default
3. Multiple commands in sequence → Each respects its own model setting
4. No API key for specified model → Appropriate error handling

## Recommendations for Next Step

1. **Research Phase**: Investigate ExtensionAPI model methods (`pi.setModel()`) behavior
2. **Design Options**: Evaluate flag-based vs settings-based approaches
3. **Prototype**: Create a minimal prototype with `/tk-implement --model` flag
4. **Documentation**: Clarify model precedence (global → project → command → subagent)

### Key Questions to Answer
- Can commands reliably override the main loop model via ExtensionAPI?
- Should model settings be per-command or a general tk-flow configuration?
- What's the UX: explicit flags vs implicit settings file?

## Lessons Applied

- **Recursion Guard Pattern**: When implementing nested command invocations (main loop spawning subagents), consider using environment variables as guards to prevent infinite loops (from `.tf/AGENTS.md`)
- **Flag Parsing Pattern**: Follow existing patterns from tk-bootstrap.ts for consistency in new flags
- **Extension Command Registration**: Use the ExtensionAPI pattern for registering new commands with proper handler signature and argument parsing

---

## Code Context

### Scout Status
⚠️ **Scout task failed** - OpenRouter credit limit reached (requested 32000 tokens, only 12972 available). No code-level findings were retrieved.

### Recommended Code Research

Since scout couldn't complete, manual research is needed for:

1. **ExtensionAPI Model Methods**
   - Read: `/opt/homebrew/Cellar/node/25.7.0/lib/node_modules/@mariozechner/pi-coding-agent/src/extension-api.ts`
   - Look for: `setModel()`, model-related methods, session model state

2. **Subagent Model Override**
   - Read: `/opt/homebrew/Cellar/.../pi-coding-agent/src/tools/subagent.ts`
   - Look for: How `model` parameter is passed and used

3. **Settings Precedence**
   - Read: `/opt/homebrew/Cellar/.../pi-coding-agent/src/config/settings.ts` (or equivalent)
   - Look for: How settings cascade (global → project → runtime)

4. **Existing tk-flow Implementation**
   - Read: `/Users/volker/coding/libs/pi-tk-flow/src/tk-bootstrap.ts`
   - Look for: Flag parsing patterns, extension command handlers

### Files to Investigate
- `pi-coding-agent/src/extension-api.ts` - ExtensionAPI definition
- `pi-coding-agent/src/tools/subagent.ts` - Subagent tool implementation
- `pi-tk-flow/src/tk-bootstrap.ts` - Existing tk command implementations
- `pi-tk-flow/prompts/` - Prompt template structure

### Entry Point
Start by examining the ExtensionAPI to understand what model control methods are available from command handlers.
