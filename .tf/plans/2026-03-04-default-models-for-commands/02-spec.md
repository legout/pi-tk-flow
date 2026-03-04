# Technical Spec: Default Models for Commands

**Feature**: Per-Command Model Configuration via `pi-prompt-template-model`
**Date**: 2026-03-04
**Status**: Draft

---

## Architecture

### Overview

This feature integrates the existing `pi-prompt-template-model` extension with the tk-flow command prompts. The extension handles all model switching logic—the implementation requires only adding frontmatter fields to prompt templates and documenting usage patterns.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Model Selection Flow                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User runs /tk-implement TICKET-123                                          │
│       │                                                                      │
│       ▼                                                                      │
│  pi-prompt-template-model extension intercepts prompt expansion             │
│       │                                                                      │
│       ├─ Reads frontmatter: model: claude-haiku-4-5, claude-sonnet-4-20250514 │
│       ├─ Resolves first available model with API key                         │
│       ├─ Captures current model for auto-restore                             │
│       └─ Switches to resolved model                                          │
│       │                                                                      │
│       ▼                                                                      │
│  Main agent executes tk-implement prompt with selected model                 │
│       │                                                                      │
│       ├─ Subagent calls use agent-defined models (or runtime overrides)      │
│       │                                                                      │
│       ▼                                                                      │
│  agent_end fires → Extension restores previous model                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Principle

**No code changes required.** The `pi-prompt-template-model` extension provides all functionality:
- Model selection from frontmatter
- Fallback chain resolution
- Auto-restore after command completion
- API key validation
- Skill injection (optional)

The implementation consists entirely of:
1. Adding `model` frontmatter to prompt templates
2. Adding optional `thinking` frontmatter
3. Documenting the extension as an optional dependency

---

## Components

### 1. Prompt Template Modifications

#### Files to Modify

| File | Current State | Changes |
|------|---------------|---------|
| `prompts/tk-implement.md` | No model frontmatter | Add `model: claude-haiku-4-5, claude-sonnet-4-20250514` |
| `prompts/tk-brainstorm.md` | No model frontmatter | Add `model: claude-sonnet-4-20250514` |
| `prompts/tk-plan.md` | No model frontmatter | Add `model: claude-sonnet-4-20250514` |
| `prompts/tk-plan-check.md` | No model frontmatter | Add `model: claude-haiku-4-5` |
| `prompts/tk-plan-refine.md` | No model frontmatter | Add `model: claude-sonnet-4-20250514` |
| `prompts/tk-ticketize.md` | No model frontmatter | Add `model: claude-haiku-4-5` |

#### Model Selection Rationale

| Command | Model(s) | Rationale |
|---------|----------|-----------|
| `tk-implement` | `claude-haiku-4-5, claude-sonnet-4-20250514` | Cost-optimized primary with capable fallback |
| `tk-brainstorm` | `claude-sonnet-4-20250514` | Creative work benefits from stronger reasoning |
| `tk-plan` | `claude-sonnet-4-20250514` | Planning requires thorough analysis |
| `tk-plan-check` | `claude-haiku-4-5` | Fast review, lower cost for quality gates |
| `tk-plan-refine` | `claude-sonnet-4-20250514` | Refinement needs strong reasoning |
| `tk-ticketize` | `claude-haiku-4-5` | Simple extraction, cost-optimized |

#### Frontmatter Format

```yaml
---
description: Analyze and implement any tk ticket with main-agent path selection
model: claude-haiku-4-5, claude-sonnet-4-20250514
thinking: medium
---
```

**Fields:**
- `model` (required for this feature): Model ID or comma-separated fallback list
- `thinking` (optional): Thinking budget level (`off`, `minimal`, `low`, `medium`, `high`, `xhigh`)
- `description` (existing): Shown in autocomplete
- `restore` (optional, default `true`): Auto-restore previous model after command

### 2. Extension Dependency Documentation

#### README.md Additions

Add an "Optional Extensions" section to `README.md`:

```markdown
## Optional Extensions

### pi-prompt-template-model

Per-command model configuration for cost optimization and quality tuning.

**Installation:**
```bash
pi install npm:pi-prompt-template-model
```

**What it does:**
- Reads `model` frontmatter from prompt templates
- Switches to specified model before command execution
- Auto-restores previous model after completion
- Supports fallback chains (try cheaper model first, fall back to capable)

**Example:**
When you run `/tk-implement TICKET-123`, the extension:
1. Reads `model: claude-haiku-4-5, claude-sonnet-4-20250514` from the prompt
2. Tries Haiku first (if API key available)
3. Falls back to Sonnet if Haiku unavailable
4. Restores your previous model when done

**Without the extension:** Commands work normally with your default model.
```

### 3. Knowledge Base Documentation

Create `.tf/knowledge/topics/model-configuration.md`:

```markdown
# Model Configuration Best Practices

## Model Precedence

From highest to lowest priority:

1. **Runtime override**: `/model <id>` command or `model` parameter in subagent calls
2. **Prompt frontmatter**: `model` field in prompt template (requires pi-prompt-template-model)
3. **Project settings**: `.pi/settings.json` 
4. **Global settings**: `~/.pi/agent/settings.json`

## Subagent Model Patterns

### Agent Frontmatter (Default)

Define in agent file (e.g., `~/.pi/agents/scout.md`):

```yaml
---
name: scout
model: claude-haiku-4-5
tools: read, grep, find, ls
---
```

### Runtime Override

Override in subagent tool call:

```json
{
  "agent": "scout",
  "model": "claude-sonnet-4-20250514",
  "task": "Deep analysis needed..."
}
```

**When to use runtime override:**
- Task complexity exceeds agent's default model capability
- Cost constraints require cheaper model for simple tasks
- Testing/debugging with different models

## Example Configurations

### Cost-Optimized Setup

```yaml
# tk-implement.md
model: claude-haiku-4-5, claude-sonnet-4-20250514

# scout.md (agent)
model: claude-haiku-4-5

# reviewer.md (agent)
model: claude-haiku-4-5
```

**Result:** Most work on Haiku, fallback to Sonnet only when needed.

### Quality-Optimized Setup

```yaml
# tk-implement.md
model: claude-sonnet-4-20250514, claude-opus-4-5

# planner.md (agent)
model: claude-sonnet-4-20250514

# reviewer.md (agent)
model: claude-sonnet-4-20250514
```

**Result:** Stronger reasoning throughout, Opus fallback for edge cases.

### Balanced Setup

```yaml
# tk-implement.md
model: claude-haiku-4-5, claude-sonnet-4-20250514

# planner.md (agent)
model: claude-sonnet-4-20250514  # Planning needs stronger model

# scout.md (agent)
model: claude-haiku-4-5  # Recon is lightweight

# reviewer.md (agent)
model: claude-sonnet-4-20250514  # Review needs careful analysis
```

**Result:** Right-sized models per task type.
```

---

## Data Flow

### Command Invocation Flow

```
User types: /tk-implement TICKET-123
         │
         ▼
┌─────────────────────────────────────┐
│  pi core: Prompt template lookup    │
│  Finds: prompts/tk-implement.md     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  pi-prompt-template-model extension │
│  (if installed)                     │
│                                     │
│  1. Parse frontmatter               │
│  2. Extract: model, thinking        │
│  3. Resolve model (check API keys)  │
│  4. Capture current model           │
│  5. Switch to resolved model        │
│  6. Inject skill (if specified)     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Main agent loop                    │
│  - Executes tk-implement prompt     │
│  - Uses switched model              │
│  - Subagent calls use agent models  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  agent_end event                    │
│                                     │
│  pi-prompt-template-model:          │
│  - Restores captured model          │
│  - Clears injected skill            │
└─────────────────────────────────────┘
```

### Model Resolution Algorithm

```
Input: model string from frontmatter (e.g., "claude-haiku-4-5, claude-sonnet-4-20250514")

1. Split by comma → candidates = ["claude-haiku-4-5", "claude-sonnet-4-20250514"]

2. For each candidate:
   a. If contains "/" → parse as "provider/model-id"
   b. If bare model-id → try providers in order:
      - anthropic
      - github-copilot
      - openrouter
   
3. For each (provider, model-id) pair:
   - Check if model exists in registry
   - Check if API key is configured
   - If both pass → SELECT THIS MODEL
   
4. If current model is in candidates → use current (no switch needed)

5. If no candidates resolve → ERROR with list of tried options
```

### Graceful Degradation (No Extension)

```
User types: /tk-implement TICKET-123
         │
         ▼
┌─────────────────────────────────────┐
│  pi core: Prompt template lookup    │
│  Finds: prompts/tk-implement.md     │
│  Parses frontmatter                 │
│  Ignores unknown fields (model)     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Main agent loop                    │
│  - Uses current/default model       │
│  - Executes prompt normally         │
└─────────────────────────────────────┘
```

**Key insight:** The `model` frontmatter is simply ignored when the extension is not installed. No errors, no warnings—commands work normally.

---

## Error Handling

### Model Not Available

**Scenario:** Specified model has no API key configured.

**Extension behavior:**
- Tries next model in fallback chain
- If all fail: Shows notification listing tried models

**Example notification:**
```
⚠ Could not switch model. Tried: claude-haiku-4-5 (no API key), claude-sonnet-4-20250514 (no API key)
Continuing with current model: claude-opus-4-5
```

### Extension Not Installed

**Scenario:** User runs command with model frontmatter but extension not installed.

**Behavior:**
- Frontmatter is parsed by pi core
- Unknown fields (`model`, `thinking`) are ignored
- Command executes normally with current model
- No errors or warnings

### Invalid Model Format

**Scenario:** Frontmatter contains malformed model string.

**Extension behavior:**
- Logs warning to console
- Falls back to current model
- Continues execution without interruption

### API Key Rotation

**Scenario:** API key expires mid-session.

**Behavior:**
- Next command using that provider fails at API call time
- Standard pi error handling applies
- User sees provider-specific authentication error

---

## Observability

### User-Visible Indicators

#### Autocomplete Display

Commands show model info in the autocomplete:

```
/tk-implement    Implement ticket [haiku|sonnet] (user)
/tk-brainstorm   Brainstorm feature [sonnet] (user)
/tk-plan         Create plan [sonnet] (user)
/tk-plan-check   Check plan quality [haiku] (user)
```

Format: `[model1|model2]` for fallback chains, `[model]` for single model.

#### Model Switch Notification

When extension switches models:

```
✓ Switched to claude-haiku-4-5 (from claude-opus-4-5)
```

#### Model Restore Notification

When command completes:

```
↩ Restored claude-opus-4-5
```

### Logging

Extension logs to pi's internal log (visible with `--verbose`):

```
[pi-prompt-template-model] Resolved model: claude-haiku-4-5 (provider: anthropic)
[pi-prompt-template-model] Captured current model for restore: claude-opus-4-5
[pi-prompt-template-model] Switched to: claude-haiku-4-5
[pi-prompt-template-model] Restored: claude-opus-4-5
```

### Metrics (Future Consideration)

Potential metrics for tracking:
- Commands using model frontmatter vs default
- Fallback chain utilization (how often fallback is used)
- Model switch latency
- Error rate by model/provider

---

## Testing Strategy

### Test Categories

#### 1. Extension Compatibility Tests

**Purpose:** Verify prompts with model frontmatter work correctly with extension installed.

**Test cases:**
| Test | Command | Expected Behavior |
|------|---------|-------------------|
| TC-1.1 | `/tk-implement TICKET` | Model switches to Haiku (or Sonnet fallback) |
| TC-1.2 | `/tk-brainstorm topic` | Model switches to Sonnet |
| TC-1.3 | `/tk-plan topic` | Model switches to Sonnet |
| TC-1.4 | `/tk-plan-check plan-dir` | Model switches to Haiku |
| TC-1.5 | Command completes | Previous model restored |

**Validation:**
- Check model switch notification appears
- Verify model in use matches expected
- Confirm restore notification after completion

#### 2. Graceful Degradation Tests

**Purpose:** Verify commands work without extension installed.

**Test cases:**
| Test | Setup | Expected Behavior |
|------|-------|-------------------|
| TC-2.1 | Extension not installed | Commands execute without error |
| TC-2.2 | Extension not installed | No model switch notifications |
| TC-2.3 | Extension not installed | Current model used throughout |

**Validation:**
- No errors in console
- Command completes successfully
- Output matches expected behavior

#### 3. Fallback Chain Tests

**Purpose:** Verify comma-separated model lists work correctly.

**Test cases:**
| Test | Setup | Expected Behavior |
|------|-------|-------------------|
| TC-3.1 | Haiku API key only | Uses Haiku |
| TC-3.2 | Sonnet API key only | Falls back to Sonnet |
| TC-3.3 | Both keys available | Uses Haiku (first in list) |
| TC-3.4 | No keys available | Error notification, continues with current |
| TC-3.5 | Currently on Sonnet | No switch (already on valid model) |

**Validation:**
- Verify correct model selected
- Check fallback notification if applicable
- Confirm error handling for no-keys case

#### 4. API Key Handling Tests

**Purpose:** Verify clear error messages for missing API keys.

**Test cases:**
| Test | Setup | Expected Behavior |
|------|-------|-------------------|
| TC-4.1 | No Anthropic key, trying Anthropic model | Clear notification about missing key |
| TC-4.2 | Invalid API key | Provider error at API call time |
| TC-4.3 | Expired API key | Provider authentication error |

**Validation:**
- Error message is actionable
- Command doesn't hang
- User can recover by setting API key

#### 5. Documentation Accuracy Tests

**Purpose:** Verify documented examples match actual behavior.

**Test cases:**
| Test | Document | Verification |
|------|----------|--------------|
| TC-5.1 | README examples | Walk through installation steps |
| TC-5.2 | Knowledge base patterns | Test each configuration example |
| TC-5.3 | Model precedence docs | Verify precedence order |

**Validation:**
- All commands in docs execute successfully
- Output matches documentation claims
- No outdated information

### Test Execution

**Manual Testing:**
1. Install extension: `pi install npm:pi-prompt-template-model`
2. Restart pi
3. Run each tk command with test inputs
4. Verify model switches and restores
5. Uninstall extension, verify graceful degradation

**Automated Testing:**
- Not applicable (extension behavior, not code changes)
- Consider adding integration tests to pi-prompt-template-model repo

---

## Rollout & Risks

### Rollout Plan

#### Phase 1: Prompt Updates (Immediate)

1. Add `model` frontmatter to all tk command prompts
2. Add `thinking` frontmatter where beneficial
3. Update README with extension documentation
4. Create knowledge base documentation

**No release required**—prompt templates are loaded at runtime.

#### Phase 2: Documentation (Same Day)

1. Update README.md with optional extension section
2. Create `.tf/knowledge/topics/model-configuration.md`
3. Add examples for common configurations

#### Phase 3: Validation (Within 24h)

1. Manual testing with extension installed
2. Manual testing without extension
3. Verify all documented examples work
4. Test fallback chain scenarios

### Rollback Plan

**If issues arise:**

1. Remove `model` frontmatter from prompts (reverts to previous behavior)
2. Update README to remove extension recommendation
3. No code changes to roll back

**Rollback is trivial**—just remove the frontmatter fields.

### Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Extension bugs affect tk commands | Low | Medium | Graceful degradation; users can uninstall extension |
| Model switch latency adds delay | Low | Low | Extension is fast; switch happens during prompt expansion |
| Users confused about model switching | Medium | Low | Clear documentation; visible notifications |
| API key errors not actionable | Low | Medium | Extension provides clear error messages |
| Fallback chains not intuitive | Medium | Low | Document with examples; show in autocomplete |

### Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| `pi-prompt-template-model` | Optional | None (graceful degradation) |
| pi core prompt template system | Required | None (already in use) |

### Success Criteria

1. **Functional:** Commands work identically with or without extension
2. **Performance:** No measurable delay in command execution
3. **UX:** Clear feedback when model switches
4. **Documentation:** All examples in docs work as described
5. **Adoption:** Users can easily install and benefit from the feature

---

## Implementation Checklist

- [ ] Add `model` frontmatter to `prompts/tk-implement.md`
- [ ] Add `model` frontmatter to `prompts/tk-brainstorm.md`
- [ ] Add `model` frontmatter to `prompts/tk-plan.md`
- [ ] Add `model` frontmatter to `prompts/tk-plan-check.md`
- [ ] Add `model` frontmatter to `prompts/tk-plan-refine.md`
- [ ] Add `model` frontmatter to `prompts/tk-ticketize.md`
- [ ] Add `thinking` frontmatter where appropriate
- [ ] Update `README.md` with extension documentation
- [ ] Create `.tf/knowledge/topics/model-configuration.md`
- [ ] Manual test with extension installed
- [ ] Manual test without extension
- [ ] Verify fallback chain scenarios
- [ ] Review documentation accuracy

---

## Appendix: Model Frontmatter Examples

### Cost-Optimized Implementation

```yaml
---
description: Implement ticket with cost-optimized model selection
model: claude-haiku-4-5, claude-sonnet-4-20250514
thinking: low
---
```

### Quality-Focused Planning

```yaml
---
description: Create thorough implementation plan
model: claude-sonnet-4-20250514
thinking: high
---
```

### Fast Review

```yaml
---
description: Quick plan quality check
model: claude-haiku-4-5
---
```

### Cross-Provider Fallback

```yaml
---
description: Implementation with provider redundancy
model: anthropic/claude-haiku-4-5, openrouter/claude-haiku-4-5, claude-sonnet-4-20250514
---
```

### Stay on Switched Model

```yaml
---
description: Switch to Haiku for this session
model: claude-haiku-4-5
restore: false
---
```
