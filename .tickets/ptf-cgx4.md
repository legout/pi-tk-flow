---
id: ptf-cgx4
status: open
deps: [ptf-cb32]
links: []
created: 2026-03-04T15:54:14Z
type: feature
priority: 2
assignee: legout
parent: ptf-it5r
tags: [feature, vertical-slice, knowledge-base, model-configuration]
---
# Document canonical 5-level model precedence and subagent behavior

Create .tf/knowledge/topics/model-configuration.md with the exact precedence ladder and examples that separate main-loop prompt model selection from subagent runtime overrides, then cross-link from README.

## Design

Refs: PRD US-4/US-5 + ID-4; Spec Components §3; Implementation Plan Task 3.

## Acceptance Criteria

- [ ] New knowledge topic exists at .tf/knowledge/topics/model-configuration.md.
- [ ] The 5-level precedence ladder appears verbatim in required order.
- [ ] Examples distinguish subagent tool call model overrides from main-loop prompt-frontmatter model selection.
- [ ] README references the topic and contains no conflicting precedence text.

