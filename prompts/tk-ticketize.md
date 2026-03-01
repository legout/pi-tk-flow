---
description: Convert planning docs into tk-ready vertical-slice tickets (creates by default, preview with --dry-run)
---

Create ticket breakdown from `$@`.

## 0) Parse Input

Treat `$@` as raw input.

Supported flags:
- `--fast` (default — lightweight scout with lighter analysis)
- `--thorough` (full codebase scout + deep architecture analysis)
- `--create` (default if no mode flag — actually runs `tk create` + `tk dep`)
- `--dry-run` (preview only, no ticket creation)
- `--epic "<title>"` optional explicit epic title override
- `--async` run chain in background
- `--clarify` open chain clarify UI

Rules:
1. First non-flag token is `SOURCE_PATH` (typically `.tf/plans/.../03-implementation-plan.md`).
2. If `SOURCE_PATH` is missing, STOP and ask for it.
3. If both `--create` and `--dry-run` are present, STOP and ask user to choose one.
4. If both `--fast` and `--thorough` are present, STOP and ask user to choose one.
5. Default analysis mode is `fast`.
6. Default action mode is `create`.
7. If both `--async` and `--clarify` are set, prefer async and set clarify=false.
8. Reject unknown flags with a short help message.

## 1) Validate Inputs

- Ensure `SOURCE_PATH` exists.
- Set:
  - `SOURCE_DIR = dirname(SOURCE_PATH)`
  - `CHAIN_DIR = .subagent-runs/tk-ticketize/<source-slug>`
  - `MODE = dry-run|create`
  - `ANALYSIS_MODE = fast|thorough`

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

Select chain by analysis profile:
- If `--thorough` is set, run the **Thorough Mode** chain.
- Otherwise (default, including explicit `--fast`), run the **Fast Mode** chain.

### Fast Mode (default)

Uses lighter scout focus; prioritizes plan document analysis over deep codebase exploration.

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
      "task": "Lightweight scout: verify plan context and key architecture seams for '<SOURCE_PATH>'. Focus on implementation plan structure and existing patterns. Skip deep file exploration.",
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

### Thorough Mode

Deep codebase recon for complex architecture or when plan documents need heavy interpretation.

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
      "task": "Scout codebase context relevant to planning source '<SOURCE_PATH>'. Focus on architecture boundaries, natural vertical slice seams, and existing patterns.",
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
3. If mode=dry-run, confirm preview completed and note:
   - review + edit `<SOURCE_DIR>/tickets.yaml` if needed
   - then rerun without `--dry-run` to create tickets
4. Note analysis mode used (fast/thorough).
