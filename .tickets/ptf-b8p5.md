---
id: ptf-b8p5
status: closed
deps: [ptf-fo04]
links: []
created: 2026-03-01T11:18:20Z
type: feature
priority: 1
assignee: legout
parent: ptf-21fw
tags: [ui, data-layer, vertical-slice, tui]
---
# S2 Build multi-plan ticket loading and classification backbone

Implement YamlTicketLoader and dependency-aware BoardClassifier to aggregate .tf/plans/*/tickets.yaml and classify tickets into board columns.

## Design

Refs: PRD US-1, ID-2, ID-4, ID-5; Spec C-5, C-6, E-3/E-4/E-5; Plan Tasks 2-3.

## Acceptance Criteria

- [ ] Loader parses all plan tickets.yaml files into a unified ticket model\n- [ ] Status lookup uses tk show <id> --format json with safe fallback to open\n- [ ] Malformed/missing YAML is skipped with warnings, not crashes\n- [ ] Classifier returns CLOSED/BLOCKED/IN_PROGRESS/READY per dependency rules\n- [ ] Unknown dependencies are handled safely

