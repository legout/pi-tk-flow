---
name: tk-plan-refine
description: Refine plan from quality findings (planner-b -> documenter). Run plan-check beforehand to generate gaps/review.
---

## planner-b
reads: plan-gaps.md, plan-review.md
output: plan-refined.md
progress: true

Refine the implementation plan for task: {task} using findings from plan-gaps and plan-review.

## documenter
reads: plan-gaps.md, plan-review.md, plan-refined.md
output: refinement-summary.md
progress: true

Summarize what was changed, what remains open, and why the refined plan is now ready (or still blocked).
