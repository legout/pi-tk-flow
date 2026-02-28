---
name: tk-path-b
description: Standard tk workflow (scout -> context-builder -> researcher -> planner -> worker -> reviewer -> tester -> tk-closer)
---

## scout
output: scout-context.md
progress: true

Scout codebase context for task: {task}. Focus on relevant files, patterns, and tests.

## context-builder
reads: scout-context.md
output: anchor-context.md
progress: true

Build re-anchored implementation context for task: {task}. Include constraints from .tf/AGENTS.md and .tf/knowledge when available.

## researcher
reads: anchor-context.md
output: research.md
progress: true

Research best practices for task: {task}. Reuse .tf/knowledge first and only fill gaps.

## planner
reads: anchor-context.md, research.md
output: plan.md
progress: true

Create implementation plan for task: {task} integrating anchored context and research.

## worker
reads: plan.md, anchor-context.md
output: implementation.md
progress: true

Implement task: {task} per plan.

## reviewer
reads: implementation.md, plan.md
output: review.md
progress: true

Review implementation for task: {task}.

## tester
reads: implementation.md, plan.md, review.md
output: test-results.md
progress: true

Test implementation for task: {task} and summarize pass/fail + gaps.

## tk-closer
reads: implementation.md, review.md, test-results.md
output: close-summary.md
progress: true

Commit and close gate for task: {task}. Determine ticket id, commit changes, and run tk close or tk status in-progress based on review/test outcomes.
