---
name: tf-plan-check
description: Plan quality gate (scout -> plan-gap-analyzer -> plan-reviewer)
---

Note: When `artifacts: true` is used, outputs may be written under run/session subdirectories (including `parallel-*` folders) instead of directly at `<CHAIN_DIR>/<file>`. Callers should materialize expected outputs to canonical `<CHAIN_DIR>/` paths and verify required files before final reporting.

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
