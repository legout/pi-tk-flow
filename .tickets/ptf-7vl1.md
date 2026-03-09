---
id: ptf-7vl1
status: closed
deps: [ptf-ucgi]
links: []
created: 2026-03-06T06:55:48Z
type: chore
priority: 3
assignee: legout
parent: ptf-9c04
tags: [chore, vertical-slice, tk-loop, documentation]
---
# S6: Usage documentation and troubleshooting runbook

Publish operator-facing README documentation for installation, execution modes, state artifacts, troubleshooting, and test execution aligned to implemented behavior.

## Design

PRD: US-5, ID-4, Out of Scope
Spec: 7.2 Installation, 7.3 Configuration, 7.5 Rollback Plan
Plan: Task 12

## Acceptance Criteria

- [ ] README includes copy-paste examples for clarify, hands-free, dispatch, and interactive.
- [ ] Environment variables and .tk-loop-state schema are documented accurately.
- [ ] Troubleshooting covers stale lock files, recursion guard, and failed tickets.
- [ ] Testing section explains how to run integration tests.
- [ ] Documentation reflects no automatic retry behavior.


## Notes

**2026-03-09T04:13:41Z**

Documentation complete. README created at .tf/scripts/README.md with: installation, 4 mode examples, env vars, state schema, troubleshooting (stale locks, recursion guard, failed tickets), testing guide, and no-retry behavior documentation. All 5 AC met.
