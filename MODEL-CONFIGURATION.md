# Model Configuration

This document describes the model-selection behavior for `pi-tk-flow` commands and agents.

## Precedence Levels

The following levels determine which model is used, from highest to lowest priority:

### 1. Subagent tool call `model` parameter
- Source: explicit `model` parameter in a `subagent(...)` tool call
- Scope: one tool invocation
- Use when: a specific subagent execution must override everything else

### 2. Agent definition frontmatter `model`
- Source: `model:` in an agent definition such as `assets/agents/worker.md`
- Scope: all invocations of that agent unless overridden at runtime
- Use when: an agent consistently benefits from a particular model

### 3. Main loop model (prompt frontmatter via extension)
- Source: `model:` in prompt frontmatter, typically applied by `pi-prompt-template-model`
- Scope: the top-level `/tf-*` command execution
- Use when: a command should default to a particular model profile

### 4. Project defaults (`.pi/settings.json`)
- Source: project-level pi settings
- Scope: all operations in the project unless overridden above

### 5. Global defaults (`~/.pi/agent/settings.json`)
- Source: user-level pi settings
- Scope: fallback default across all pi usage

## Command Mapping

Current authoritative command-to-model mapping:

| Command | Model | Thinking |
|---------|-------|----------|
| `/tf-bootstrap` | `minimax/m2.5` | `low` |
| `/tf-brainstorm` | `glm-5` | `medium` |
| `/tf-implement` | `glm-5` | `medium` |
| `/tf-plan` | `glm-5` | `medium` |
| `/tf-plan-check` | `glm-5` | `medium` |
| `/tf-plan-refine` | `glm-5` | `medium` |
| `/tf-ticketize` | `glm-5` | `medium` |
| `/tf-refactor` | `glm-5` | `medium` |
| `/tf-simplify` | `glm-5` | `medium` |

## Behavioral Notes

### Main loop vs subagents
- Top-level `/tf-*` commands may use prompt frontmatter model defaults
- Subagents resolve their own model independently using the precedence ladder above
- A parent command model does not automatically override agent-level models unless the `subagent` call passes an explicit runtime `model`

### With `pi-prompt-template-model`
When installed, the extension can:
- switch to the mapped command model at command start
- leave unmapped commands unchanged
- restore the previous model after command completion

### Without the extension
Commands still run normally using the active/project/global model settings.

## Package Notes
- `pi-tk-flow` ships prompt templates, agent templates, chain presets, and extensions
- ticket operations remain external and should use the `tk` CLI
- this document is package documentation; it is distinct from any `.tf/knowledge/...` files used by a project that self-hosts `pi-tk-flow`
