---
name: tk-plan-refine
description: Refine plan from quality findings (scout -> plan-gap-analyzer -> plan-reviewer -> planner -> documenter)
---

## scout
output: scout-context.md
progress: true

Scout context for plan refinement task: {task}. Focus on architecture constraints, dependency ordering, and validation expectations.

## plan-gap-analyzer
reads: scout-context.md
output: plan-gaps.md
progress: true

Analyze planning artifacts for task: {task} and produce prioritized, actionable gaps.

## plan-reviewer
reads: scout-context.md, plan-gaps.md
output: plan-review.md
progress: true

Review plan readiness for task: {task} and define required changes before GO.

## planner
reads: plan-gaps.md, plan-review.md
output: plan-refined.md
progress: true

Refine the implementation plan for task: {task} using findings from plan-gaps and plan-review.

## documenter
reads: plan-gaps.md, plan-review.md, plan-refined.md
output: refinement-summary.md
progress: true

Summarize what was changed, what remains open, and why the refined plan is now ready (or still blocked).
