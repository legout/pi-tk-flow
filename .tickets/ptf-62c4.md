---
id: ptf-62c4
status: closed
deps: [ptf-cb32]
links: []
created: 2026-03-04T15:54:14Z
type: feature
priority: 1
assignee: legout
parent: ptf-it5r
tags: [feature, vertical-slice, prompts, model-configuration]
---
# Apply prompt frontmatter model defaults across tk prompts

Add model frontmatter to all six prompt-backed tk commands and add thinking only where materially useful, keeping prompt body logic unchanged.

## Design

Refs: PRD US-1/US-2 + ID-2/ID-3; Spec Components §1; Implementation Plan Task 2.

## Acceptance Criteria

- [ ] prompts/tk-implement.md has model: claude-haiku-4-5, claude-sonnet-4-20250514.
- [ ] prompts/tk-brainstorm.md, prompts/tk-plan.md, and prompts/tk-plan-refine.md use model: claude-sonnet-4-20250514.
- [ ] prompts/tk-plan-check.md and prompts/tk-ticketize.md use model: claude-haiku-4-5.
- [ ] All six files keep valid YAML frontmatter; prompt bodies remain semantically unchanged.


## Notes

**2026-03-04T16:42:01Z**

Implementation complete:

- Added model frontmatter to all 6 prompt files:
  - tk-implement.md → claude-haiku-4-5, claude-sonnet-4-20250514
  - tk-brainstorm.md → claude-sonnet-4-20250514
  - tk-plan.md → claude-sonnet-4-20250514
  - tk-plan-refine.md → claude-sonnet-4-20250514
  - tk-plan-check.md → claude-haiku-4-5
  - tk-ticketize.md → claude-haiku-4-5
- All files have valid YAML frontmatter with description and model keys
- Prompt body content unchanged (only model line added)
- Commit: 67484a8
