---
id: ptf-bv4b
status: closed
deps: [ptf-1q8n]
links: []
created: 2026-03-01T11:18:33Z
type: feature
priority: 2
assignee: legout
parent: ptf-21fw
tags: [ui, knowledge, topics, vertical-slice, tui]
---
# S5 Add knowledge topic browser tab with live scanning

Implement TopicScanner plus Topics tab to scan .tf/knowledge/topics/*.md, group by prefix, and render topic details.

## Design

Refs: PRD US-2, ID-3; Spec C-4, C-7, E-6; Plan Tasks 4-5.

## Acceptance Criteria

- [ ] Topics are scanned from markdown files without index.json\n- [ ] Grouping by seed/plan/spike/baseline/other is stable\n- [ ] Selecting a topic shows title/content in detail panel\n- [ ] Missing or empty topic directory shows non-crashing empty state


## Notes

**2026-03-04T14:49:03Z**

Implementation complete:

- TopicScanner scans .tf/knowledge/topics/*.md live (no index.json)
- Topics grouped by prefix: seed/plan/spike/baseline/other
- Detail panel shows title, metadata, content on selection
- Empty/missing directory handled gracefully with "No topics found"
- Security fix: shell injection resolved via shlex.split + subprocess.run
- Sorting fix: case-insensitive topic ordering

Tests: 58/58 passed (16 topic scanner tests)
Commit: 6733bb3
