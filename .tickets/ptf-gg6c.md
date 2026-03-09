---
id: ptf-gg6c
status: closed
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


## Notes

**2026-03-09T02:19:34Z**

Implementation complete for Tasks 5,6,8 (S2: Queue polling and sequential dispatch):

• Ticket parser: parse_tickets() extracts IDs from tk ready first column with regex validation
• Command builder: build_command() generates mode-specific /tk-implement invocations for all 4 modes
• Main loop: Sequential processing with empty-queue exit (status 0), poll interval support, and --dry-run mode
• Fixed exit code capture: Changed from if ! eval to eval || exit_code=$? pattern to capture actual command exit code
• Fixed set -e handling: Added || true after process_ticket() to continue to next ticket on failure per PRD

All 5 acceptance criteria verified:
✓ AC1: Ticket IDs parsed from tk ready first column
✓ AC2: Command builder emits correct /tk-implement invocations for all 4 modes
✓ AC3: Tickets processed sequentially in queue order
✓ AC4: --dry-run logs intended commands without executing
✓ AC5: Empty queue exits with status 0 and completion log

Key files: .tf/scripts/tk-loop.sh
Commit: 8eaeb7a
Tests: All acceptance criteria verified (manual testing)
