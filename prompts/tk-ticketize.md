---
description: Convert planning docs into tk-ready vertical-slice tickets (dry-run by default, optional create)
---

Create ticket breakdown from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--dry-run` (default if no mode flag)
- `--create` (actually run `tk create` + `tk dep`)
- `--epic "<title>"` optional explicit epic title override
- `--async` run chain in background
- `--clarify` open chain clarify UI

Rules:
1. First non-flag token is `SOURCE_PATH` (typically `docs/plans/.../03-implementation-plan.md`).
2. If `SOURCE_PATH` is missing, STOP and ask for it.
3. If both `--create` and `--dry-run` are present, STOP and ask user to choose one.
4. Default mode is `dry-run`.
5. If both `--async` and `--clarify` are set, prefer async and set clarify=false.
6. Reject unknown flags with a short help message.

## 1) Validate Inputs

- Ensure `SOURCE_PATH` exists.
- Set:
  - `SOURCE_DIR = dirname(SOURCE_PATH)`
  - `CHAIN_DIR = .subagent-runs/tk-ticketize/<source-slug>`
  - `MODE = dry-run|create`

## 2) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tk-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required agents: `scout`, `ticketizer`
- If any required agent is missing, STOP and report missing names.

## 3) Ticketize Chain

Run this chain:

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
      "task": "Scout codebase context relevant to planning source '<SOURCE_PATH>'. Focus on architecture boundaries and natural vertical slice seams.",
      "output": "scout-context.md"
    },
    {
      "agent": "ticketizer",
      "task": "SOURCE_PATH=<SOURCE_PATH> MODE=<MODE> OUTPUT_DIR=<SOURCE_DIR> PARENT_TITLE=<EPIC_TITLE_OR_EMPTY>. Build vertical-slice tickets and write OUTPUT_DIR/04-ticket-breakdown.md, OUTPUT_DIR/tickets.yaml, OUTPUT_DIR/ticketize-summary.md. If MODE=create, execute tk create/dep and record created IDs.",
      "reads": ["scout-context.md"],
      "output": "ticketize.md"
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
1. Confirm generated files:
   - `<SOURCE_DIR>/04-ticket-breakdown.md`
   - `<SOURCE_DIR>/tickets.yaml`
   - `<SOURCE_DIR>/ticketize-summary.md`
2. If mode=create, report created ticket IDs + dependency graph summary.
3. If mode=dry-run, recommend:
   - review + edits
   - then rerun with `--create`
