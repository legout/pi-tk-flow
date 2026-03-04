---
name: tk-plan-check
description: Plan quality gate (scout -> plan-gap-analyzer -> plan-reviewer)
---

## scout
output: scout-context.md
progress: true

Scout context for plan check task: {task}. Focus on architecture boundaries, dependencies, and test patterns relevant to the plan.

## plan-gap-analyzer
reads: scout-context.md
output: plan-gaps.md
progress: true

Analyze planning artifacts for task: {task}. Identify missing decisions, sequencing/dependency issues, test/validation gaps, and rollout/rollback/observability gaps.

## plan-reviewer
reads: scout-context.md, plan-gaps.md
output: plan-review.md
progress: true

Review plan readiness for task: {task}. Produce GO/NO-GO decision for ticketization with severity-ranked findings and required changes.
