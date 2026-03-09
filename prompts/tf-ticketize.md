---
description: Convert planning docs into tf-ready vertical-slice tickets (creates by default, preview with --dry-run)
model: glm-5
thinking: medium
---

Create ticket breakdown from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--create` (default if no mode flag — actually runs `tk create` + `tk dep`)
- `--dry-run` (preview only, no ticket creation)
- `--epic "<title>"` optional explicit epic title override
- `--async` run chain in background
- `--clarify` open chain clarify UI

Rules:
1. First non-flag token is `SOURCE_PATH` (typically `.tf/plans/.../03-implementation-plan.md`).
2. If `SOURCE_PATH` is missing, STOP and ask for it.
3. If both `--create` and `--dry-run` are present, STOP and ask user to choose one.
4. Default action mode is `create`.
5. If both `--async` and `--clarify` are set, prefer async and set clarify=false.
6. Reject unknown flags with a short help message.

## 1) Validate Inputs

- Ensure `SOURCE_PATH` exists.
- Set:
  - `SOURCE_DIR = dirname(SOURCE_PATH)`
  - `CHAIN_DIR = .subagent-runs/tf-ticketize/<source-slug>`
  - `MODE = dry-run|create`

## 2) Subagent Scope Guardrails

- Use existing agents only.
- Never call subagent management actions create/update/delete.
- Determine `AGENT_SCOPE`:
  - if `.pi/agents/.tf-bootstrap.json` exists -> `project`
  - else -> `user`
- Preflight:
  - `subagent {"action":"list","agentScope":"<AGENT_SCOPE>"}`
  - Required agents: `ticketizer`
- If any required agent is missing, STOP and report missing names.

## 3) Ticketize Chain

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
      "agent": "ticketizer",
      "task": "SOURCE_PATH=<SOURCE_PATH> MODE=<MODE> OUTPUT_DIR=<SOURCE_DIR> PARENT_TITLE=<EPIC_TITLE_OR_EMPTY>. Read the implementation plan and related planning docs to build vertical-slice tickets. Write OUTPUT_DIR/04-ticket-breakdown.md, OUTPUT_DIR/tickets.yaml, OUTPUT_DIR/ticketize-summary.md. If MODE=create, execute tk create/dep and record created IDs.",
      "output": "ticketize.md"
    }
  ]
}
```

## 3.5) Materialize and verify expected artifacts (sync runs)

After synchronous completion, normalize `ticketize.md` to canonical root path in `<CHAIN_DIR>`.

```bash
if [ ! -f "<CHAIN_DIR>/ticketize.md" ]; then
  FOUND=$(find "<CHAIN_DIR>" -name "ticketize.md" -type f 2>/dev/null | head -1)
  if [ -n "$FOUND" ]; then
    cp "$FOUND" "<CHAIN_DIR>/ticketize.md"
  fi
fi
```

Verify final required outputs in `<SOURCE_DIR>`:
- `04-ticket-breakdown.md`
- `tickets.yaml`
- `ticketize-summary.md`

If any required output is missing, report it explicitly as a blocker.

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
3. If mode=dry-run, confirm preview completed and note:
   - review + edit `<SOURCE_DIR>/tickets.yaml` if needed
   - then rerun without `--dry-run` to create tickets
