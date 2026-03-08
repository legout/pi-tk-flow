---
id: ptf-gg6c
status: open
deps: [ptf-3nor]
links: []
created: 2026-03-06T06:55:48Z
type: feature
priority: 1
assignee: legout
parent: ptf-9c04
tags: [feature, vertical-slice, tk-loop, ralph]
---
# S2: Queue polling and sequential ticket dispatch

Implement queue polling and sequential dispatch: parse tk ready output, build mode-specific /tk-implement commands, process tickets in order, and exit cleanly when queue is empty.

## Design

PRD: US-1, US-2, US-3
Spec: 2.3 Ticket Parser, 2.4 Command Builder, 3.1 Main Loop Flow
Plan: Tasks 5, 6, 8

## Acceptance Criteria

- [ ] Ticket IDs are parsed from tk ready output first column.
- [ ] Command builder emits correct /tk-implement invocation for each mode.
- [ ] Tickets are processed one-at-a-time in queue order.
- [ ] --dry-run logs intended commands without invoking pi.
- [ ] Empty queue exits with status 0 and completion log.

