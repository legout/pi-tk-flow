---
description: Refine planning artifacts using plan gap analysis + review findings
model: glm-5
thinking: medium
---

Refine planning docs from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--async` run phase-2 chain in background
- `--clarify` open phase-2 chain clarify UI

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
- `CHAIN_DIR = .subagent-runs/tf-plan-refine/${TOPIC_SLUG}`
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

Write `${CHAIN_DIR}/plan-refine-seed.json`:
```json
{
  "plan_dir": "<PLAN_DIR>",
  "plan_path": "<PLAN_PATH>",
  "topic_slug": "<TOPIC_SLUG>",
  "knowledge_topic_dir": "<KNOWLEDGE_TOPIC_DIR>"
}
```

Set:
- `SEED_READS = ["plan-refine-seed.json"] + <PLAN_DOC_READS>`
- `ANALYZER_READS = ["plan-refine-seed.json"] + <PLAN_DOC_READS>`
- `REVIEW_READS = ["plan-refine-seed.json", "plan-gaps.md"] + <PLAN_DOC_READS>`
- `REFINE_PLAN_READS = ["plan-refine-seed.json", "plan-gaps.md", "plan-review.md"] + <PLAN_DOC_READS>`
- `REFINE_SUMMARY_READS = ["plan-gaps.md", "plan-review.md", "plan-refined.md"] + <PLAN_DOC_READS>`

## 3) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tf-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required agents: `plan-gap-analyzer`, `plan-reviewer`, `plan-fast`, `documenter`
- If any required agent is missing, STOP and report missing names.

## 4) Phase 1: analyze + review (skip if already available)

If `<PLAN_DIR>/05-plan-gaps.md` **and** `<PLAN_DIR>/06-plan-review.md` already exist (e.g., from `/tf-plan-check`), skip phase 1. Instead:
- Copy those two files into `${CHAIN_DIR}/plan-gaps.md` and `${CHAIN_DIR}/plan-review.md`.
- Ensure knowledge snapshots exist (copy to `<KNOWLEDGE_TOPIC_DIR>/plan-gaps.md` and `<KNOWLEDGE_TOPIC_DIR>/plan-review.md` if missing).

Otherwise, run analysis first so refinement is guided by concrete gaps.

Use phase-1 runtime defaults:
- `clarify: false`
- `async: false`
- `artifacts: true`
- `includeProgress: false`
- `maxOutput: { "bytes": 200000, "lines": 5000 }`

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
      "agent": "plan-gap-analyzer",
      "task": "Analyze planning artifacts for gaps and write final files to '<PLAN_DIR>/05-plan-gaps.md' and '<KNOWLEDGE_TOPIC_DIR>/plan-gaps.md'.",
      "reads": <ANALYZER_READS>,
      "output": "plan-gaps.md"
    },
    {
      "agent": "plan-reviewer",
      "task": "Review plan readiness and required changes; write final files to '<PLAN_DIR>/06-plan-review.md' and '<KNOWLEDGE_TOPIC_DIR>/plan-review.md'.",
      "reads": <REVIEW_READS>,
      "output": "plan-review.md"
    }
  ]
}
```

## 5) Phase 2: refine artifacts

Locate and read the gap analysis and review files.
**File location strategy (chain outputs may be in run-specific subdirectories):**
1. First try: `<CHAIN_DIR>/plan-gaps.md` and `<CHAIN_DIR>/plan-review.md`
2. If not found, search: `find <CHAIN_DIR> -name "plan-gaps.md" -type f | head -1` (and same for plan-review.md)
3. Read from the found paths

After reading both files, analyze them:

Set `NEEDS_REFINEMENT=true` if either contains:
- `Status: NEEDS_REWORK`
- `Ticketization: NO-GO`
- any Critical/Major required change

If `NEEDS_REFINEMENT=false`:
- write `<PLAN_DIR>/07-refinement-summary.md` stating no material changes required
- stop (no phase-2 chain needed)

If `NEEDS_REFINEMENT=true`, run phase 2 with:
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
    {
      "agent": "plan-fast",
      "task": "Refine '<PLAN_DIR>/03-implementation-plan.md' using plan-gaps.md and plan-review.md. Write final refined plan back to '<PLAN_DIR>/03-implementation-plan.md' and persist a knowledge snapshot at '<KNOWLEDGE_TOPIC_DIR>/implementation-plan.md'.",
      "reads": <REFINE_PLAN_READS>,
      "output": "plan-refined.md"
    },
    {
      "agent": "documenter",
      "task": "Write refinement summary to '<PLAN_DIR>/07-refinement-summary.md'. Include: major changes made, unresolved items, and whether ticketization is now GO or NO-GO. Also persist to '<KNOWLEDGE_TOPIC_DIR>/refinement-summary.md'.",
      "reads": <REFINE_SUMMARY_READS>,
      "output": "refinement-summary.md"
    }
  ]
}
```

### 5.5) Materialize and verify expected artifacts (sync runs)

After phase-2 completion in synchronous mode, normalize expected chain outputs to canonical root paths in `<CHAIN_DIR>`.

```bash
EXPECTED_FILES="plan-gaps.md plan-review.md plan-refined.md refinement-summary.md"

for name in $EXPECTED_FILES; do
  if [ ! -f "<CHAIN_DIR>/$name" ]; then
    FOUND=$(find "<CHAIN_DIR>" -name "$name" -type f 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
      cp "$FOUND" "<CHAIN_DIR>/$name"
    fi
  fi
done
```

Required final docs in `<PLAN_DIR>`:
- `05-plan-gaps.md`
- `06-plan-review.md`
- `07-refinement-summary.md`
- plus `03-implementation-plan.md` when refinement was applied

If any required final doc is missing, report it explicitly as a blocker.

If async=true:
- Return run id/status immediately for phase 2.
- State artifact path root `<CHAIN_DIR>`.
- Tell user to check with `subagent_status`.

## 6) Final Response

When synchronous run completes:
1. Confirm generated/updated files:
   - `<PLAN_DIR>/05-plan-gaps.md`
   - `<PLAN_DIR>/06-plan-review.md`
   - `<PLAN_DIR>/03-implementation-plan.md` (if refined)
   - `<PLAN_DIR>/07-refinement-summary.md`
2. Report latest ticketization decision (GO/NO-GO).
3. List persisted knowledge files in `<KNOWLEDGE_TOPIC_DIR>`.
4. Recommend next step:
   - if GO: `/tf-ticketize <PLAN_DIR>/03-implementation-plan.md`
   - if still NO-GO: review gaps and consider manual refinement
