---
name: tf-plan-refine
description: Refine plan from quality findings (plan-fast -> documenter). Run plan-check beforehand to generate gaps/review.
---

Note: When `artifacts: true` is used, outputs may be written under run/session subdirectories (including `parallel-*` folders) instead of directly at `<CHAIN_DIR>/<file>`. Callers should materialize expected outputs to canonical `<CHAIN_DIR>/` paths and verify required files before final reporting.

## plan-fast
reads: plan-gaps.md, plan-review.md
output: plan-refined.md
progress: true

Refine the implementation plan for task: {task} using findings from plan-gaps and plan-review.

## documenter
reads: plan-gaps.md, plan-review.md, plan-refined.md
output: refinement-summary.md
progress: true

Summarize what was changed, what remains open, and why the refined plan is now ready (or still blocked).
