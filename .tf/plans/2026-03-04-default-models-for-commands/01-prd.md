# PRD: Default Models for Commands
**Feature**: Per-Command Model Configuration via `pi-prompt-template-model`
**Date**: 2026-03-04
**Status**: Draft

---

## Problem Statement
1. Users cannot specify per-command model preferences for tk commands (`/tk-implement`, `/tk-brainstorm`, `/tk-plan`, etc.) without modifying global or project settings.
2. Cost-sensitive workflows lack a mechanism to use cheaper models for routine tasks while reserving capable models for complex work.
3. Subagent models are configurable via agent frontmatter and runtime overrides, but the main loop model running tk commands has no equivalent per-command control.
4. No documentation exists for best practices around model selection in the tk-flow workflow.

## Solution
Integrate the existing `pi-prompt-template-model` extension by adding `model` frontmatter to tk command prompt templates and documenting best practices:

| Component | Change |
| --- | --- |
| Prompt templates | Add `model` frontmatter field (with fallback lists) to `tk-implement.md`, `tk-brainstorm.md`, `tk-plan.md`, etc. |
| README | Document `pi-prompt-template-model` as optional dependency with installation and usage examples |
| Knowledge base | Create model configuration best practices guide covering cost optimization, quality tuning, and subagent model patterns |

The extension handles model switching, auto-restore on completion, fallback chains, and API key validation—no custom code required.

## User Stories
- **US-1 Cost-Optimized Implementation**: As a developer, I want `/tk-implement` to use a cost-effective model by default so routine tickets don't consume expensive API credits. *Acceptance*: `prompts/tk-implement.md` includes `model: claude-haiku-4-5, claude-sonnet-4-20250514` frontmatter; users with the extension installed get automatic model switching.
- **US-2 Quality-Optimized Planning**: As a developer, I want planning commands to use more capable models for thorough analysis. *Acceptance*: `prompts/tk-plan.md` specifies `model: claude-sonnet-4-20250514` or equivalent; complex planning benefits from stronger reasoning.
- **US-3 Graceful Degradation**: As a developer without the extension, I expect tk commands to work normally with my default model. *Acceptance*: Commands execute without error when `pi-prompt-template-model` is not installed; frontmatter is simply ignored.
- **US-4 Subagent Model Best Practices**: As a developer, I want guidance on configuring subagent models for different cost/quality tradeoffs. *Acceptance*: Documentation explains agent frontmatter `model` field, runtime `subagent` tool `model` parameter, and provides example configurations.
- **US-5 Model Override Flexibility**: As a developer, I want to override the default model for a specific invocation. *Acceptance*: Users can run `/model <id>` before the tk command, or create custom prompt wrappers with different model frontmatter.

## Implementation Decisions
- **ID-1 Extension as Optional Dependency**: Document `pi-prompt-template-model` in README as optional but recommended. No hard dependency added to `package.json`.
- **ID-2 Model Frontmatter in Prompts**: Add `model` field to all tk command prompts with sensible defaults:
  - `tk-implement.md`: `claude-haiku-4-5, claude-sonnet-4-20250514` (cost-optimized with fallback)
  - `tk-brainstorm.md`: `claude-sonnet-4-20250514` (quality-focused for creative work)
  - `tk-plan.md`: `claude-sonnet-4-20250514` (quality-focused for planning)
  - `tk-plan-check.md`: `claude-haiku-4-5` (fast review, lower cost)
  - `tk-plan-refine.md`: `claude-sonnet-4-20250514` (quality-focused for refinement)
- **ID-3 Thinking Level Frontmatter**: Add `thinking: medium` (or appropriate level) to prompts where extended thinking benefits the task.
- **ID-4 Best Practices Documentation**: Create `.tf/knowledge/topics/model-configuration.md` covering:
  - Model precedence: frontmatter > `/model` command > project settings > global settings
  - Subagent model patterns: agent frontmatter vs runtime override
  - Example configurations: cost-optimized, quality-optimized, balanced
- **ID-5 No Code Changes**: This feature requires only prompt template modifications and documentation—no changes to `tk-bootstrap.ts` or other TypeScript code.

## Testing Decisions
- **TD-1 Extension Compatibility**: Verify prompts with model frontmatter work correctly with `pi-prompt-template-model` installed (model switches, auto-restores).
- **TD-2 Graceful Degradation**: Verify prompts work identically without the extension (frontmatter ignored, no errors).
- **TD-3 Fallback Chain Validation**: Test that comma-separated fallback lists work as expected (primary model unavailable → secondary used).
- **TD-4 API Key Handling**: Verify clear error messages when specified model lacks configured API key (handled by extension).
- **TD-5 Documentation Accuracy**: Walk through documented examples to ensure they match actual behavior.

## Out of Scope
1. Building custom flag parsing (`--model`, `--subagent-model`) in tk-bootstrap.ts.
2. Creating per-command configuration files (`.tk-implement.json`).
3. Modifying agent definition files (per tk-implement guardrails).
4. Session-level model persistence beyond what the extension provides.
5. Provider configuration or API key management (assumes users have these set up).
6. Cost estimation or tracking features.
