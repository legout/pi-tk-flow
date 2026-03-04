---
id: ptf-cb32
status: open
deps: []
links: []
created: 2026-03-04T15:54:14Z
type: feature
priority: 1
assignee: legout
parent: ptf-it5r
tags: [feature, vertical-slice, documentation, model-configuration]
---
# Publish canonical README model mapping and extension behavior

Update README with optional pi-prompt-template-model guidance and one authoritative command→model mapping table including /tk-bootstrap.

## Design

Refs: PRD Solution + ID-1/ID-2; Spec Components §2; Implementation Plan Task 1.

## Acceptance Criteria

- [ ] README includes extension install instructions and behavior notes (switch, fallback, restore).
- [ ] Mapping table includes all required commands, including /tk-bootstrap → claude-haiku-4-5.
- [ ] README states commands still execute normally when extension is not installed.
- [ ] Mapping is presented as canonical source for prompt/docs alignment.

