---
id: ptf-cb32
status: closed
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


## Notes

**2026-03-04T16:14:36Z**

Implementation completed:
- Added pi-prompt-template-model extension documentation to README
- Documented behavior: switch, fallback, restore, no-extension scenarios
- Created authoritative command→model mapping table for all tk-* commands
- Post-fix review: all issues resolved, no Critical/Major issues remaining
- Commit: 309c3de
