---
id: ptf-19a3
status: open
deps: [ptf-102j]
links: []
created: 2026-03-04T11:02:57Z
type: feature
priority: 2
assignee: legout
parent: ptf-53pu
tags: [documentation, tk-implement, vertical-slice, ralph]
---
# Document execution modes in README and tk-workflow skill

Add an Execution Modes section plus compatibility matrix, session guidance, and updated examples across README.md and skills/tk-workflow/SKILL.md.

## Design

PRD Solution & US-1..US-4; Spec Architecture §5; Implementation Plan Task 4.

## Acceptance Criteria

- [ ] README explains each mode, compatibility with --async/--clarify, overlay controls, and session breadcrumbs.
- [ ] README and the skill doc describe /sessions, /attach, and where session.json lives.
- [ ] skills/tk-workflow/SKILL.md advises when to choose interactive vs hands-free vs dispatch vs async, including troubleshooting tips.
- [ ] Examples include --hands-free and --dispatch flag usage matching implemented behavior.

