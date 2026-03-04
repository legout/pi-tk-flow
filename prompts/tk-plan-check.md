---
description: Run a quality gate on planning artifacts and produce GO/NO-GO ticketization guidance
---

Check planning quality from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--fast` (default — lightweight scout)
- `--thorough` (deeper scout and stricter findings)
- `--async` run chain in background
- `--clarify` open chain clarify UI

Rules:
1. First non-flag token is `SOURCE` (`<plan-dir>` or `<plan-dir>/03-implementation-plan.md`).
2. If `SOURCE` is missing, STOP and ask for it.
3. If both `--fast` and `--thorough` are present, STOP and ask user to choose one.
4. If both `--async` and `--clarify` are present, prefer async and set clarify=false.
5. Reject unknown flags with a short help message.

## 1) Resolve Paths

Determine:
- If `SOURCE` is a directory, `PLAN_DIR = SOURCE`, `PLAN_PATH = <PLAN_DIR>/03-implementation-plan.md`
- If `SOURCE` is a file, require basename `03-implementation-plan.md`, then `PLAN_DIR = dirname(SOURCE)` and `PLAN_PATH = SOURCE`

Set:
- `PLAN_BASENAME = basename(PLAN_DIR)`
- `TOPIC_SLUG = PLAN_BASENAME` stripped of date prefix `YYYY-MM-DD-` when present
- `CHAIN_DIR = .subagent-runs/tk-plan-check/${TOPIC_SLUG}`
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
  "analysis_mode": "<fast|thorough>",
  "knowledge_topic_dir": "<KNOWLEDGE_TOPIC_DIR>"
}
```

Set:
- `SEED_READS = ["plan-check-seed.json"] + <PLAN_DOC_READS>`
- `ANALYZER_READS = ["plan-check-seed.json", "scout-context.md"] + <PLAN_DOC_READS>`
- `REVIEW_READS = ["plan-check-seed.json", "scout-context.md", "plan-gaps.md"] + <PLAN_DOC_READS>`

## 3) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tk-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required agents: `scout`, `plan-gap-analyzer`, `plan-reviewer`
- If any required agent is missing, STOP and report missing names.

## 4) Run Plan-Check Chain

Use:
- `clarify: <RUN_CLARIFY>`
- `async: <RUN_ASYNC>`
- `artifacts: true`
- `includeProgress: false`
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

### Fast mode (default)

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
      "task": "Lightweight scout for plan quality check. Read plan-check-seed.json first. Focus on architecture seams, dependency hotspots, and test baseline relevant to PLAN_PATH.",
      "reads": <SEED_READS>,
      "output": "scout-context.md"
    },
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

### Thorough mode

Same chain, but scout task should do deeper recon:
- read higher-impact modules and tests relevant to plan scope
- validate sequencing assumptions against actual code seams
- identify integration and rollout risks early

(Keep analyzer/reviewer steps unchanged.)

## 5) Post-run File Guarantees

When synchronous run completes, ensure these exist in `PLAN_DIR`:
- `05-plan-gaps.md`
- `06-plan-review.md`

If a target file is missing, copy from chain artifacts:
- `${CHAIN_DIR}/plan-gaps.md` -> `<PLAN_DIR>/05-plan-gaps.md`
- `${CHAIN_DIR}/plan-review.md` -> `<PLAN_DIR>/06-plan-review.md`

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
3. Note analysis mode used (fast/thorough).
4. Recommend next step:
   - if GO: `/tk-ticketize <PLAN_DIR>/03-implementation-plan.md`
   - if NO-GO: `/tk-plan-refine <PLAN_DIR>`
