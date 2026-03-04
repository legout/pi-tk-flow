---
id: ptf-it5r
status: closed
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


## Notes

**2026-03-04T17:08:27Z**

Implementation complete:
- Added thinking: frontmatter to 4 prompt files (high for tk-plan/tk-brainstorm, medium for tk-implement/tk-plan-refine)
- Created .tf/knowledge/topics/model-configuration.md with 5-level model precedence ladder
- Added README.md cross-link and precedence summary in extension section
- Created validation evidence in 04-progress.md with static grep checks and extension-on/off tests
- Post-fix review: all issues resolved, no blockers
- Commit: 45a637b
