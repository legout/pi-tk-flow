---
description: Brainstorm a new feature/refactor/simplification and produce a decision-ready design brief before planning
model: glm-5
thinking: medium
---

Brainstorm from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--mode feature|refactor|simplify` (default: `feature`)
- `--from <path>` optional seed notes/problem statement
- `--async` run phase-2 chain in background
- `--clarify` open phase-2 chain clarify UI

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
- `TOPIC_SEED = ${CHAIN_DIR}/topic-seed.json`
- `KNOWLEDGE_TOPIC_DIR = .tf/knowledge/topics/${TOPIC_SLUG}`

Ensure directories exist:
- `.tf/plans`
- `${PLAN_DIR}`
- `.subagent-runs/tk-brainstorm`
- `${CHAIN_DIR}`
- `.tf/knowledge/topics`
- `${KNOWLEDGE_TOPIC_DIR}`

If `--from` is set, verify the file exists before proceeding.

## 2) Build Seeded Inputs (required)

Create a seed file consumed by both `scout` and `context-builder`.

Write `${TOPIC_SEED}` with:
```json
{
  "topic": "<TOPIC>",
  "mode": "<MODE>",
  "plan_dir": "<PLAN_DIR>",
  "from_path": "<FROM_PATH_OR_NULL>",
  "topic_terms": ["token1", "token2", "token3"],
  "summary": "One-line brainstorming objective"
}
```

If `--from` is provided:
1. Read the source file.
2. Write `${CHAIN_DIR}/from-seed.md` with source content (or concise extracted sections if very large).
3. Set `SEED_READS = ["topic-seed.json", "from-seed.md"]`.

If `--from` is not provided:
- Set `SEED_READS = ["topic-seed.json"]`.

## 3) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tk-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required baseline agents: `scout`, `context-builder`, `documenter`, `researcher`, `librarian`
  - Optional optimization agent: `context-merger`
- If baseline agents are missing, STOP and report missing names.
- Set `HAS_CONTEXT_MERGER=true|false` based on preflight.

## 4) Phase 1 (always sync): Build Anchored Context

Run anchoring first so the main agent can decide whether research/librarian calls are needed.

Use runtime defaults for phase 1:
- `clarify: false`
- `async: false`
- `artifacts: true`
- `includeProgress: false`
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

### Preferred phase-1 chain (when `HAS_CONTEXT_MERGER=true`)

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": "<CHAIN_DIR>",
  "clarify": false,
  "async": false,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    {
      "parallel": [
        {
          "agent": "scout",
          "task": "Scout project context for brainstorming topic '<TOPIC>' (<MODE>). Read topic-seed.json FIRST. If from-seed.md exists, prioritize concepts/files implied by it. Focus on relevant files, architecture boundaries, constraints, and test baseline.",
          "reads": <SEED_READS>,
          "output": "scout-context.md"
        },
        {
          "agent": "context-builder",
          "task": "Build anchored brainstorming context base for '<TOPIC>' (<MODE>). Read topic-seed.json FIRST. Include constraints from .tf/AGENTS.md and .tf/knowledge when present. If from-seed.md exists, synthesize it.",
          "reads": <SEED_READS>,
          "output": "anchor-context-base.md"
        }
      ],
      "concurrency": 2,
      "failFast": false
    },
    {
      "agent": "context-merger",
      "task": "Merge scout-context.md and anchor-context-base.md into anchor-context.md. Preserve all anchor sections and append code-context findings from scout. Also write/update '<KNOWLEDGE_TOPIC_DIR>/anchor-context.md' with the merged result.",
      "reads": ["scout-context.md", "anchor-context-base.md"],
      "output": "anchor-context.md"
    }
  ]
}
```

### Fallback phase-1 chain (when `HAS_CONTEXT_MERGER=false`)

```json
{
  "agentScope": "<AGENT_SCOPE>",
  "chainDir": "<CHAIN_DIR>",
  "clarify": false,
  "async": false,
  "artifacts": true,
  "includeProgress": false,
  "maxOutput": { "bytes": 200000, "lines": 5000 },
  "chain": [
    {
      "parallel": [
        {
          "agent": "scout",
          "task": "Scout project context for brainstorming topic '<TOPIC>' (<MODE>). Read topic-seed.json FIRST. If from-seed.md exists, prioritize concepts/files implied by it. Focus on relevant files, architecture boundaries, constraints, and test baseline.",
          "reads": <SEED_READS>,
          "output": "scout-context.md"
        },
        {
          "agent": "context-builder",
          "task": "Build anchored brainstorming context draft for '<TOPIC>' (<MODE>). Read topic-seed.json FIRST. Include constraints from .tf/AGENTS.md and .tf/knowledge when present. If from-seed.md exists, synthesize it.",
          "reads": <SEED_READS>,
          "output": "anchor-context-draft.md"
        }
      ],
      "concurrency": 2,
      "failFast": false
    },
    {
      "agent": "context-builder",
      "task": "Finalize anchor-context.md by merging anchor-context-draft.md with scout-context.md. Keep all draft sections and add a Code Context section from scout findings. Also write/update '<KNOWLEDGE_TOPIC_DIR>/anchor-context.md' with the merged result.",
      "reads": ["anchor-context-draft.md", "scout-context.md"],
      "output": "anchor-context.md"
    }
  ]
}
```

## 5) Research Routing (main-agent decision, no flags)

Read `<CHAIN_DIR>/anchor-context.md` and decide:
- `USE_RESEARCHER=true` when there are unresolved best-practice/design/operational gaps not already covered by `.tf/knowledge/**`.
- `USE_LIBRARIAN=true` when external library behavior, version differences, internals, or source-level evidence are needed.
- Both may be true; both may be false.

Then build:
- `DOC_READS = ["anchor-context.md"]`
- If `USE_RESEARCHER`, append `research.md` to `DOC_READS`.
- If `USE_LIBRARIAN`, append `library-research.md` to `DOC_READS`.

Research step definitions:

```json
{
  "agent": "researcher",
  "task": "Research external best practices for '<TOPIC>' with focus on actionable options and trade-offs relevant to this repository context. Reuse existing .tf/knowledge first. Write chain artifact to 'research.md'. Also persist reusable findings to '<KNOWLEDGE_TOPIC_DIR>/brainstorm-research.md'.",
  "reads": ["anchor-context.md"],
  "output": "research.md"
}
```

```json
{
  "agent": "librarian",
  "task": "Produce source-backed library internals/history findings for '<TOPIC>' with permalinks and concrete implications for this repo. Write chain artifact to 'library-research.md'. Also persist reusable findings to '<KNOWLEDGE_TOPIC_DIR>/brainstorm-library-research.md'.",
  "reads": ["anchor-context.md"],
  "output": "library-research.md"
}
```

If both are needed, run them in a parallel block (`concurrency: 2`, `failFast: false`).

## 6) Phase 2: Draft brainstorm brief (optional research/librarian + documenter)

Run phase 2 with:
- `clarify: <RUN_CLARIFY>`
- `async: <RUN_ASYNC>`

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
    <OPTIONAL_RESEARCH_STEPS>,
    {
      "agent": "documenter",
      "task": "Create a decision-ready brainstorming brief for '<TOPIC>' (<MODE>) and write final files to '<PLAN_DIR>/00-brainstorm.md' and '<PLAN_DIR>/00-design.md' (same content). Include sections: Problem Frame, Goals & Non-Goals, 2-3 Approach Options with trade-offs, Recommended Direction, Risks, Open Questions, and Decision Checklist. Incorporate research and librarian findings when present.",
      "reads": <DOC_READS>,
      "output": "brainstorm-draft.md"
    }
  ]
}
```

When no research step is selected, omit `<OPTIONAL_RESEARCH_STEPS>` entirely.

### 6.5 Canonical design artifact (required)

After phase-2 completion (sync mode), ensure both files exist:
- `<PLAN_DIR>/00-brainstorm.md`
- `<PLAN_DIR>/00-design.md`

If one exists but the other is missing, duplicate content so both exist with identical text.

If async=true:
- Return run id/status immediately for phase 2.
- State artifact path root `<CHAIN_DIR>`.
- Tell user to check with `subagent_status`.

## 7) Final Response

When synchronous run completes:
1. Confirm created brainstorming docs:
   - `<PLAN_DIR>/00-brainstorm.md`
   - `<PLAN_DIR>/00-design.md`
2. Report research routing decision:
   - researcher used? yes/no
   - librarian used? yes/no
3. If used, list persisted knowledge files under `<KNOWLEDGE_TOPIC_DIR>`.
4. Summarize recommendation + key trade-offs in 5-8 bullets.
5. Recommend next step:
   - `/tk-plan <topic> --mode <mode>`
   - optionally with `--from <PLAN_DIR>/00-design.md`
