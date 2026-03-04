---
id: ptf-it5r
status: open
deps: []
links: []
created: 2026-03-04T15:54:14Z
type: epic
priority: 1
assignee: legout
tags: [planning, model-configuration, tk-flow]
---
# Add per-command model configuration via pi-prompt-template-model

Align tk-flow command defaults, precedence documentation, and validation evidence so per-command model behavior is consistent, documented, and safely verifiable with and without the optional extension.

## Design

Source docs: .tf/plans/2026-03-04-default-models-for-commands/{01-prd.md,02-spec.md,03-implementation-plan.md,07-refinement-summary.md}.

## Acceptance Criteria

- [ ] README contains canonical command→model mapping including /tk-bootstrap.
- [ ] Prompt-backed tk commands carry aligned model frontmatter defaults.
- [ ] Knowledge base defines canonical 5-level precedence and subagent behavior.
- [ ] Validation evidence confirms extension-on and extension-off behavior without regressions.

