# Model Configuration

This document describes the 5-level precedence ladder for model selection in pi-tk-flow commands.

## Precedence Levels

The following levels determine which model is used when executing a command, from highest to lowest priority:

### Level 1: Subagent Tool Call `model` Parameter (Runtime Override)

- **Source**: Explicit `model` parameter in `subagent()` tool call
- **Scope**: Single tool invocation
- **Use When**: You need to temporarily override the model for a specific subagent execution
- **Example**: `subagent({ agent: "worker", task: "...", model: "claude-opus-4" })`

### Level 2: Agent Definition Frontmatter `model`

- **Source**: `model:` field in agent definition (e.g., `assets/agents/worker.md`)
- **Scope**: All invocations of that agent
- **Use When**: An agent consistently needs a specific model capability
- **Example**: A coding agent defined with `model: claude-sonnet-4-20250514`

### Level 3: Main Loop Model (Prompt Frontmatter via Extension)

- **Source**: `model:` field in prompt template frontmatter, applied by `pi-prompt-template-model` extension
- **Scope**: Command execution via the mapped prompt
- **Use When**: Command-level model assignment for consistent behavior
- **Note**: This is the primary mechanism for tk commands when the extension is installed

### Level 4: Project Defaults (`.pi/settings.json`)

- **Source**: `model` field in project's `.pi/settings.json`
- **Scope**: All operations within the project
- **Use When**: Project-wide model preference
- **Example**: `{ "model": "claude-sonnet-4-20250514" }`

### Level 5: Global Defaults (`~/.pi/agent/settings.json`)

- **Source**: `model` field in user's global settings
- **Scope**: All pi operations (fallback)
- **Use When**: User's preferred default across all projects
- **Example**: `{ "model": "claude-haiku-4-5" }`

## Subagent Behavior Notes

### Extension-On Behavior

When `pi-prompt-template-model` is installed:

1. Commands automatically switch to their mapped model on invocation
2. The extension reads the `model:` frontmatter from the prompt file
3. After command completion, the previous model is restored
4. If a command has no mapping, it uses the currently active model (no change)

### Extension-Off Behavior

When `pi-prompt-template-model` is **not** installed:

1. Commands execute with whatever model is currently active
2. No error or warning is emitted
3. The `model:` frontmatter in prompts is ignored by the core system
4. Users can manually set models via `--model` flags or settings

### Nested Subagent Calls

- Parent agent model does not automatically propagate to subagents
- Each subagent invocation checks the precedence ladder independently
- Explicit `model` parameter in subagent call overrides all other levels

### Model List Syntax

Some prompts specify multiple models (e.g., `model: claude-haiku-4-5, claude-sonnet-4-20250514`):

- This indicates the command may use different models for different phases
- The first model is typically used for initial/fast operations
- The second model is used for deeper reasoning phases
- The extension or command logic determines which to use when

## Canonical Command→Model Mapping

| Command | Model | Thinking |
|---------|-------|----------|
| `/tk-bootstrap` | `minimax/m2.5` | `low` |
| `/tk-brainstorm` | `glm-5` | `medium` |
| `/tk-implement` | `glm-5` | `medium` |
| `/tk-plan` | `glm-5` | `medium` |
| `/tk-plan-check` | `glm-5` | `medium` |
| `/tk-plan-refine` | `glm-5` | `medium` |
| `/tk-ticketize` | `glm-5` | `medium` |

> **Note**: This mapping is the authoritative source. When updating model assignments, update the README.md table first.
