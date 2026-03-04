---
id: ptf-102j
status: open
deps: [ptf-vln5]
links: []
created: 2026-03-04T11:02:54Z
type: feature
priority: 2
assignee: legout
parent: ptf-53pu
tags: [interactive, tk-implement, vertical-slice, ralph]
---
# Persist interactive session metadata and breadcrumbs

Write .subagent-runs/<ticket>/session.json with mode/sessionId/timestamps/command/status, emit /sessions + /attach instructions, and keep legacy runs free of stray artifacts.

## Design

PRD US-4; Spec Architecture §4 & Observability; Implementation Plan Task 3.

## Acceptance Criteria

- [ ] Interactive, hands-free, and dispatch runs write session.json with mode, sessionId, startedAt, command, and status.
- [ ] Console/log output includes a standardized block referencing /sessions, /attach <sessionId>, and Ctrl+T/B/Q shortcuts.
- [ ] Failure paths clean up partial files and guide remediation without impacting legacy runs.
- [ ] Non-interactive executions do not create session artifacts.

