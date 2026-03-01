---
description: Build planning artifacts (PRD, spec, implementation plan) for a new feature/refactor/simplification using subagents
---

Create planning docs from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--fast` (default — parallel PRD/Spec/Design, lighter outputs)
- `--thorough` (sequential PRD→Spec→Design with full cross-synthesis)
- `--mode feature|refactor|simplify` (default: `feature`)
- `--from <path>` optional seed doc/notes file
- `--async` run chain in background
- `--clarify` open chain clarify UI

Rules:
1. Topic is the remaining non-flag text after parsing.
2. If topic is empty, STOP and ask for a topic.
3. If both `--fast` and `--thorough` are present, STOP and ask user to choose one.
4. Default speed profile is `fast` (feature mode still defaults to `--mode feature`).
5. If both `--async` and `--clarify` are present, prefer async and set clarify=false.
6. Reject unknown flags with a short help message.

## 1) Paths

- `DATE = <YYYY-MM-DD>`
- `TOPIC_SLUG = kebab-case(topic)`
- `PLAN_DIR = .tf/plans/${DATE}-${TOPIC_SLUG}`
- `CHAIN_DIR = .subagent-runs/tk-plan/${TOPIC_SLUG}`

Ensure directories exist:
- `.tf/plans`
- `${PLAN_DIR}`
- `.subagent-runs/tk-plan`

If `--from` is set, verify the file exists before proceeding.

## 2) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tk-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required agents: `scout`, `context-builder`, `documenter`, `planner`
- If any required agent is missing, STOP and report missing names.

## 3) Planning Chain

Select chain by speed profile:
- If `--thorough` is set, run the **Thorough Mode** chain.
- Otherwise (default, including explicit `--fast`), run the **Fast Mode** chain.

### Fast Mode (default) — Parallel Documenters

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
      "task": "Scout project context for planning topic '<TOPIC>' (<MODE>). Focus on relevant files, constraints, existing architecture, and test patterns.",
      "output": "scout-context.md"
    },
    {
      "agent": "context-builder",
      "task": "Build anchored planning context for '<TOPIC>' (<MODE>). Include constraints from .tf/AGENTS.md and .tf/knowledge when available. If --from path provided, include it in synthesis.",
      "reads": ["scout-context.md"],
      "output": "anchor-context.md"
    },
    {
      "parallel": [
        {
          "agent": "documenter",
          "task": "Draft a concise Product Requirements Document for '<TOPIC>' (<MODE>) using anchored context. Write final PRD to '<PLAN_DIR>/01-prd.md' with sections: Problem Statement, Solution, User Stories, Implementation Decisions, Testing Decisions, Out of Scope.",
          "reads": ["anchor-context.md"],
          "output": "prd-draft.md"
        },
        {
          "agent": "documenter",
          "task": "Draft a technical spec for '<TOPIC>' (<MODE>) using anchored context. Write final spec to '<PLAN_DIR>/02-spec.md' with sections: Architecture, Components, Data Flow, Error Handling, Observability, Testing Strategy, Rollout & Risks.",
          "reads": ["anchor-context.md"],
          "output": "spec-draft.md"
        },
        {
          "agent": "documenter",
          "task": "Create a canonical design document for '<TOPIC>' (<MODE>) and write final file to '<PLAN_DIR>/00-design.md'. Synthesize anchored context into a concise implementation-facing design brief with sections: Context, Chosen Architecture, Component Contracts, Key Flows, Risks, and Decisions.",
          "reads": ["anchor-context.md"],
          "output": "design-draft.md"
        }
      ],
      "concurrency": 3,
      "failFast": false
    },
    {
      "agent": "planner",
      "task": "Create a concrete implementation plan for '<TOPIC>' (<MODE>) and write final plan to '<PLAN_DIR>/03-implementation-plan.md'. Use small actionable tasks, explicit verification, dependencies, and rollback notes. Synthesize PRD intent + spec architecture + design contracts into actionable plan.",
      "reads": ["anchor-context.md", "prd-draft.md", "spec-draft.md", "design-draft.md"],
      "output": "plan-draft.md"
    }
  ]
}
```

### Thorough Mode — Sequential with Full Synthesis

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
      "task": "Scout project context for planning topic '<TOPIC>' (<MODE>). Focus on relevant files, constraints, existing architecture, and test patterns.",
      "output": "scout-context.md"
    },
    {
      "agent": "context-builder",
      "task": "Build anchored planning context for '<TOPIC>' (<MODE>). Include constraints from .tf/AGENTS.md and .tf/knowledge when available. If --from path provided, include it in synthesis.",
      "reads": ["scout-context.md"],
      "output": "anchor-context.md"
    },
    {
      "agent": "documenter",
      "task": "Draft a concise Product Requirements Document for '<TOPIC>' (<MODE>) using anchored context. Write final PRD to '<PLAN_DIR>/01-prd.md' with sections: Problem Statement, Solution, User Stories, Implementation Decisions, Testing Decisions, Out of Scope.",
      "reads": ["anchor-context.md"],
      "output": "prd-draft.md"
    },
    {
      "agent": "documenter",
      "task": "Draft a technical spec for '<TOPIC>' (<MODE>) using anchored context and PRD intent. Write final spec to '<PLAN_DIR>/02-spec.md' with sections: Architecture, Components, Data Flow, Error Handling, Observability, Testing Strategy, Rollout & Risks.",
      "reads": ["anchor-context.md", "prd-draft.md"],
      "output": "spec-draft.md"
    },
    {
      "agent": "documenter",
      "task": "Create a canonical design document for '<TOPIC>' (<MODE>) and write final file to '<PLAN_DIR>/00-design.md'. Synthesize anchored context + PRD + spec into a concise implementation-facing design brief with sections: Context, Chosen Architecture, Component Contracts, Key Flows, Risks, and Decisions.",
      "reads": ["anchor-context.md", "prd-draft.md", "spec-draft.md"],
      "output": "design-draft.md"
    },
    {
      "agent": "planner",
      "task": "Create a concrete implementation plan for '<TOPIC>' (<MODE>) and write final plan to '<PLAN_DIR>/03-implementation-plan.md'. Use small actionable tasks, explicit verification, dependencies, and rollback notes.",
      "reads": ["anchor-context.md", "prd-draft.md", "spec-draft.md", "design-draft.md"],
      "output": "plan-draft.md"
    }
  ]
}
```

If async=true:
- Return run id/status immediately.
- State artifact path root `<CHAIN_DIR>`.
- Tell user to check with `subagent_status`.

## 4) Final Response

When synchronous run completes:
1. Confirm created planning docs in `<PLAN_DIR>`:
   - `00-design.md`
   - `01-prd.md`
   - `02-spec.md`
   - `03-implementation-plan.md`
2. Summarize key decisions in 5-10 bullets.
3. Note mode used (fast/thorough).
4. Recommend next step:
   - ` /tk-ticketize <PLAN_DIR>/03-implementation-plan.md`
