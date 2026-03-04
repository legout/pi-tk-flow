---
id: ptf-niv3
status: open
deps: []
links: []
created: 2026-03-04T11:02:46Z
type: feature
priority: 1
assignee: legout
parent: ptf-53pu
tags: [interactive, tk-implement, vertical-slice, ralph]
---
# Extend /tk-implement flag parsing for interactive modes

Teach the prompt to parse --interactive/--hands-free/--dispatch, enforce exclusivity with --async/--clarify, and keep existing defaults untouched.

## Design

PRD Solution table & US-5; Spec Architecture §1; Implementation Plan Task 1.

## Acceptance Criteria

- [ ] Parser recognizes the new flags and documents them in usage/help output.
- [ ] Invalid combos (multiple interactive flags, interactive+--async, --interactive+--clarify) emit actionable errors while --dispatch+--clarify stays valid.
- [ ] Unknown-flag rejection rules and default/--async flows work as before.
- [ ] Parser verification runs are appended to model-test-output.md.

