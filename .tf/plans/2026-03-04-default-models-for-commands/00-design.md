# Design: Default Models for Commands

**Feature**: Per-Command Model Configuration via `pi-prompt-template-model`
**Date**: 2026-03-04
**Architecture**: Extension integration (no code changes)

---

## Context

Tk-flow commands (`/tk-implement`, `/tk-plan`, etc.) currently use the user's default model with no per-command control. Users cannot optimize costs by using cheaper models for routine tasks or reserve capable models for complex work.

The `pi-prompt-template-model` extension already provides the required functionality—it intercepts prompt expansion, reads model frontmatter, switches models, and auto-restores after command completion. This design integrates the extension by adding frontmatter to existing prompt templates.

**Key Constraint**: Subagent calls within commands must remain unaffected. Agent definitions define their own models, and runtime overrides in `subagent` tool calls take precedence. This feature only controls the main agent loop model.

---

## Chosen Architecture

**Pattern**: Extension Integration (Zero Code Changes)

```
┌─────────────────────────────────────────────────────────────────┐
│  User runs /tk-implement TICKET-123                              │
│       │                                                          │
│       ▼                                                          │
│  pi-prompt-template-model (if installed)                         │
│       ├─ Parse `model:` frontmatter                              │
│       ├─ Resolve first available model (check API keys)          │
│       ├─ Capture current model for auto-restore                  │
│       └─ Switch to resolved model                                │
│       │                                                          │
│       ▼                                                          │
│  Main agent executes prompt (switched model)                     │
│       │                                                          │
│       ├─ Subagent calls → use agent-defined models (unchanged)   │
│       │                                                          │
│       ▼                                                          │
│  agent_end → Extension restores previous model                   │
└─────────────────────────────────────────────────────────────────┘
```

**Why this architecture**:
- No code changes required—only frontmatter additions
- Graceful degradation: commands work identically without extension
- Leverages existing extension behavior (switch, fallback, restore)
- Unknown frontmatter fields are silently ignored by pi core

---

## Component Contracts

### Prompt Templates (6 files)

| File | Model Frontmatter | Rationale |
|------|-------------------|-----------|
| `prompts/tk-implement.md` | `claude-haiku-4-5, claude-sonnet-4-20250514` | Cost-optimized primary, capable fallback |
| `prompts/tk-brainstorm.md` | `claude-sonnet-4-20250514` | Creative work needs stronger reasoning |
| `prompts/tk-plan.md` | `claude-sonnet-4-20250514` | Planning requires thorough analysis |
| `prompts/tk-plan-check.md` | `claude-haiku-4-5` | Fast review, lower cost |
| `prompts/tk-plan-refine.md` | `claude-sonnet-4-20250514` | Refinement needs strong reasoning |
| `prompts/tk-ticketize.md` | `claude-haiku-4-5` | Simple extraction, cost-optimized |

**Frontmatter format**:
```yaml
---
description: <existing description>
model: claude-haiku-4-5, claude-sonnet-4-20250514
thinking: medium  # optional
---
```

### README.md

Add "Optional Extensions" section documenting:
- Installation: `pi install npm:pi-prompt-template-model`
- Behavior: model switching, fallback chains, auto-restore
- Example: `/tk-implement` flow with Haiku→Sonnet fallback
- Without extension: commands work normally

### Knowledge Base

Create `.tf/knowledge/topics/model-configuration.md`:
- Model precedence hierarchy
- Subagent model patterns (agent frontmatter vs runtime override)
- Example configurations (cost-optimized, quality-optimized, balanced)

---

## Key Flows

### Flow 1: Command with Extension Installed

```
/tk-implement TICKET-123
    → Extension reads: model: claude-haiku-4-5, claude-sonnet-4-20250514
    → Resolve: check Haiku API key → available
    → Capture: current model (e.g., claude-opus-4-5)
    → Switch: claude-haiku-4-5
    → Execute: tk-implement prompt
    → Complete: restore claude-opus-4-5
```

### Flow 2: Command without Extension

```
/tk-implement TICKET-123
    → pi core parses frontmatter
    → Ignores unknown field `model`
    → Execute: tk-implement prompt with current model
    → No switch, no restore
```

### Flow 3: Fallback Chain Activation

```
/tk-implement TICKET-123
    → Extension reads: model: claude-haiku-4-5, claude-sonnet-4-20250514
    → Resolve Haiku: no API key configured → skip
    → Resolve Sonnet: API key available → select
    → Switch: claude-sonnet-4-20250514
    → Execute + restore
```

### Flow 4: No Available Models

```
/tk-implement TICKET-123
    → Extension reads: model: claude-haiku-4-5, claude-sonnet-4-20250514
    → Resolve Haiku: no API key → skip
    → Resolve Sonnet: no API key → skip
    → Notify: "Could not switch model. Tried: haiku (no key), sonnet (no key)"
    → Continue: use current model
```

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Extension bugs affect commands | Low | Medium | Graceful degradation; users can uninstall |
| Model switch adds latency | Low | Low | Switch happens during prompt expansion (fast) |
| Users confused about switching | Medium | Low | Clear notifications; documentation |
| Fallback not intuitive | Medium | Low | Autocomplete shows `[haiku\|sonnet]` |
| API key errors unclear | Low | Medium | Extension provides actionable messages |

**Rollback**: Remove `model` frontmatter from prompts. Trivial, no code changes.

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Extension integration | Zero code changes, leverages existing behavior |
| Dependency type | Optional | Commands must work without extension |
| Implementation scope | Frontmatter + docs only | No TypeScript changes required |
| tk-implement default | Haiku with Sonnet fallback | Cost-optimized primary, capable fallback |
| Planning commands | Sonnet only | Quality-focused for analysis |
| Review/extraction commands | Haiku only | Fast, low-cost for routine work |
| Auto-restore | Enabled (default) | Return to user's preferred model |
| Error handling | Continue with current model | Never block user from running commands |

---

## Implementation Checklist

- [ ] Add `model` frontmatter to 6 prompt templates
- [ ] Add `thinking` frontmatter where beneficial
- [ ] Update README with extension documentation
- [ ] Create `.tf/knowledge/topics/model-configuration.md`
- [ ] Manual test: extension installed
- [ ] Manual test: extension not installed
- [ ] Verify fallback chain scenarios
