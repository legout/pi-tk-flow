---
description: Brainstorm a new feature/refactor/simplification and produce a decision-ready design brief before planning
---

Brainstorm from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--mode feature|refactor|simplify` (default: `feature`)
- `--from <path>` optional seed notes/problem statement
- `--research` include external best-practice research
- `--async` run chain in background
- `--clarify` open chain clarify UI

Rules:
1. Topic is the remaining non-flag text after parsing.
2. If topic is empty, STOP and ask for a topic.
3. If both `--async` and `--clarify` are present, prefer async and set clarify=false.
4. Reject unknown flags with a short help message.

## 1) Paths

- `DATE = <YYYY-MM-DD>`
- `TOPIC_SLUG = kebab-case(topic)`
- `PLAN_DIR = .tf/plans/${DATE}-${TOPIC_SLUG}`
- `CHAIN_DIR = .subagent-runs/tk-brainstorm/${TOPIC_SLUG}`

Ensure directories exist:
- `.tf/plans`
- `${PLAN_DIR}`
- `.subagent-runs/tk-brainstorm`

If `--from` is set, verify the file exists before proceeding.

## 2) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tk-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required agents: `scout`, `context-builder`, `documenter`
  - Additional required if `--research`: `researcher`
- If required agents are missing, STOP and report missing names.

## 3) Brainstorm Chain

Run one of the following chains.

### Without `--research`

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": "<CHAIN_DIR>",
  "clarify": <RUN_CLARIFY>,
  "async": <RUN_ASYNC>,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    {
      "agent": "scout",
      "task": "Scout project context for brainstorming topic '<TOPIC>' (<MODE>). Focus on relevant files, architecture boundaries, constraints, and test baseline.",
      "output": "scout-context.md"
    },
    {
      "agent": "context-builder",
      "task": "Build anchored brainstorming context for '<TOPIC>' (<MODE>) using scout output. Include constraints from .tf/AGENTS.md and .tf/knowledge when present. If --from path is provided, synthesize it.",
      "reads": ["scout-context.md"],
      "output": "anchor-context.md"
    },
    {
      "agent": "documenter",
      "task": "Create a decision-ready brainstorming brief for '<TOPIC>' (<MODE>) and write final files to '<PLAN_DIR>/00-brainstorm.md' and '<PLAN_DIR>/00-design.md' (same content). Include sections: Problem Frame, Goals & Non-Goals, 2-3 Approach Options with trade-offs, Recommended Direction, Risks, Open Questions, and Decision Checklist.",
      "reads": ["anchor-context.md"],
      "output": "brainstorm-draft.md"
    }
  ]
}
```

### With `--research`

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": "<CHAIN_DIR>",
  "clarify": <RUN_CLARIFY>,
  "async": <RUN_ASYNC>,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    {
      "agent": "scout",
      "task": "Scout project context for brainstorming topic '<TOPIC>' (<MODE>). Focus on relevant files, architecture boundaries, constraints, and test baseline.",
      "output": "scout-context.md"
    },
    {
      "agent": "context-builder",
      "task": "Build anchored brainstorming context for '<TOPIC>' (<MODE>) using scout output. Include constraints from .tf/AGENTS.md and .tf/knowledge when present. If --from path is provided, synthesize it.",
      "reads": ["scout-context.md"],
      "output": "anchor-context.md"
    },
    {
      "agent": "researcher",
      "task": "Research external best practices for '<TOPIC>' with focus on actionable options and trade-offs relevant to this repository context.",
      "reads": ["anchor-context.md"],
      "output": "research.md"
    },
    {
      "agent": "documenter",
      "task": "Create a decision-ready brainstorming brief for '<TOPIC>' (<MODE>) and write final files to '<PLAN_DIR>/00-brainstorm.md' and '<PLAN_DIR>/00-design.md' (same content). Include sections: Problem Frame, Goals & Non-Goals, 2-3 Approach Options with trade-offs, Recommended Direction, Risks, Open Questions, and Decision Checklist. Incorporate research findings where useful.",
      "reads": ["anchor-context.md", "research.md"],
      "output": "brainstorm-draft.md"
    }
  ]
}
```

### 3.5 Canonical design artifact (required)

After chain completion (sync mode), ensure both files exist:
- `<PLAN_DIR>/00-brainstorm.md`
- `<PLAN_DIR>/00-design.md`

If one exists but the other is missing, duplicate content so both exist with identical text.

If async=true:
- Return run id/status immediately.
- State artifact path root `<CHAIN_DIR>`.
- Tell user to check with `subagent_status`.

## 4) Final Response

When synchronous run completes:
1. Confirm created brainstorming docs:
   - `<PLAN_DIR>/00-brainstorm.md`
   - `<PLAN_DIR>/00-design.md`
2. Summarize recommendation + key trade-offs in 5-8 bullets.
3. Recommend next step:
   - `/tk-plan <topic> --mode <mode>`
   - optionally with `--from <PLAN_DIR>/00-design.md`
