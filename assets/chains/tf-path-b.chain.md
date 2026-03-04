---
name: tf-path-b
description: Standard tf workflow (scout -> context-builder -> plan-fast -> worker -> reviewer+tester -> fixer -> reviewer+tester re-check -> tf-closer)
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

## plan-fast
reads: anchor-context.md
output: plan.md
progress: true

Create implementation plan for task: {task} using anchored context.

## worker
reads: plan.md, anchor-context.md
output: implementation.md
progress: true

Implement task: {task} per plan.

## reviewer
reads: implementation.md, plan.md
output: review.md
progress: true

Initial review for task: {task}.

## tester
reads: implementation.md, plan.md
output: test-results.md
progress: true

Initial tests for task: {task}. Summarize pass/fail + gaps.

## fixer
reads: implementation.md, review.md, test-results.md, plan.md
output: fixes.md
progress: true

Apply one fix pass for task: {task}. Prioritize test failures and critical/major review issues.

## reviewer
reads: implementation.md, plan.md, fixes.md
output: review-post-fix.md
progress: true

Post-fix re-check review for task: {task}.

## tester
reads: implementation.md, plan.md, fixes.md
output: test-results-post-fix.md
progress: true

Post-fix re-check tests for task: {task}.

## tf-closer
reads: anchor-context.md, implementation.md, review.md, test-results.md, fixes.md, review-post-fix.md, test-results-post-fix.md
output: close-summary.md
progress: true

Commit and close gate for task: {task}. maxFixPasses=1 per run. Use post-fix review/test as source of truth when available. Run tk close or tk status in_progress accordingly, and add blocker note when leaving ticket in_progress.
