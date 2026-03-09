---
description: Run a quality gate on planning artifacts and produce GO/NO-GO ticketization guidance
model: glm-5
thinking: medium
---

Check planning quality from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--async` run chain in background
- `--clarify` open chain clarify UI

Rules:
1. First non-flag token is `SOURCE` (`<plan-dir>` or `<plan-dir>/03-implementation-plan.md`).
2. If `SOURCE` is missing, STOP and ask for it.
3. If both `--async` and `--clarify` are present, prefer async and set clarify=false.
4. Reject unknown flags with a short help message.

## 1) Resolve Paths

Determine:
- If `SOURCE` is a directory, `PLAN_DIR = SOURCE`, `PLAN_PATH = <PLAN_DIR>/03-implementation-plan.md`
- If `SOURCE` is a file, require basename `03-implementation-plan.md`, then `PLAN_DIR = dirname(SOURCE)` and `PLAN_PATH = SOURCE`

Set:
- `PLAN_BASENAME = basename(PLAN_DIR)`
- `TOPIC_SLUG = PLAN_BASENAME` stripped of date prefix `YYYY-MM-DD-` when present
- `CHAIN_DIR = .subagent-runs/tf-plan-check/${TOPIC_SLUG}`
- `KNOWLEDGE_TOPIC_DIR = .tf/knowledge/topics/${TOPIC_SLUG}`

Ensure directories exist:
- `${CHAIN_DIR}`
- `.tf/knowledge/topics`
- `${KNOWLEDGE_TOPIC_DIR}`

Validate required input:
- `PLAN_PATH` must exist, else STOP.

Build `PLAN_DOC_READS` from existing files only:
- `<PLAN_DIR>/00-design.md`
- `<PLAN_DIR>/01-prd.md`
- `<PLAN_DIR>/02-spec.md`
- `<PLAN_DIR>/03-implementation-plan.md`

## 2) Seeded Input

Write `${CHAIN_DIR}/plan-check-seed.json`:
```json
{
  "plan_dir": "<PLAN_DIR>",
  "plan_path": "<PLAN_PATH>",
  "topic_slug": "<TOPIC_SLUG>",
  "knowledge_topic_dir": "<KNOWLEDGE_TOPIC_DIR>"
}
```

Set:
- `SEED_READS = ["plan-check-seed.json"] + <PLAN_DOC_READS>`
- `ANALYZER_READS = ["plan-check-seed.json"] + <PLAN_DOC_READS>`
- `REVIEW_READS = ["plan-check-seed.json", "plan-gaps.md"] + <PLAN_DOC_READS>`

## 3) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tf-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required agents: `plan-gap-analyzer`, `plan-reviewer`
- If any required agent is missing, STOP and report missing names.

## 4) Run Plan-Check Chain

Use:
- `clarify: <RUN_CLARIFY>`
- `async: <RUN_ASYNC>`
- `artifacts: true`
- `includeProgress: false`
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

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
      "agent": "plan-gap-analyzer",
      "task": "Analyze planning artifacts for gaps and write final files to '<PLAN_DIR>/05-plan-gaps.md' and '<KNOWLEDGE_TOPIC_DIR>/plan-gaps.md'. Include explicit ticketization readiness.",
      "reads": <ANALYZER_READS>,
      "output": "plan-gaps.md"
    },
    {
      "agent": "plan-reviewer",
      "task": "Review plan readiness and write final files to '<PLAN_DIR>/06-plan-review.md' and '<KNOWLEDGE_TOPIC_DIR>/plan-review.md'. Decision must include GO|NO-GO for ticketization.",
      "reads": <REVIEW_READS>,
      "output": "plan-review.md"
    }
  ]
}
```

## 5) Post-run File Guarantees

When synchronous run completes, ensure these exist in `PLAN_DIR`:
- `05-plan-gaps.md`
- `06-plan-review.md`

If a target file is missing, locate and copy from chain artifacts.
**File location strategy (chain outputs may be in run-specific subdirectories):**
1. First try: `<CHAIN_DIR>/<filename>`
2. If not found, search: `find <CHAIN_DIR> -name "<filename>" -type f | head -1`

Copy found files:
- `<found-plan-gaps.md>` -> `<PLAN_DIR>/05-plan-gaps.md`
- `<found-plan-review.md>` -> `<PLAN_DIR>/06-plan-review.md`

Also ensure knowledge persistence:
- `<KNOWLEDGE_TOPIC_DIR>/plan-gaps.md`
- `<KNOWLEDGE_TOPIC_DIR>/plan-review.md`

If async=true:
- Return run id/status immediately.
- State artifact path root `<CHAIN_DIR>`.
- Tell user to check with `subagent_status`.

## 6) Final Response

When synchronous run completes:
1. Confirm generated files:
   - `<PLAN_DIR>/05-plan-gaps.md`
   - `<PLAN_DIR>/06-plan-review.md`
2. Report decision from review:
   - ticketization GO or NO-GO
   - top 3 blockers (if NO-GO)
3. Recommend next step:
   - if GO: `/tf-ticketize <PLAN_DIR>/03-implementation-plan.md`
   - if NO-GO: `/tf-plan-refine <PLAN_DIR>`
