---
name: tf-path-c
description: Deep post-anchor tf execution preset (research-first variant: research -> plan-deep -> worker -> review+test -> fixer -> quick re-check -> tf-closer)
---

## researcher
reads: anchor-context.md
output: research.md
progress: true

Research best practices and ecosystem guidance for task: {task}. Reuse existing .tf/knowledge first and fill only the real gaps.

## librarian
reads: anchor-context.md
output: library-research.md
progress: true

Produce source-backed library internals/history findings for task: {task} with permalinks.

## plan-deep
reads: anchor-context.md, research.md, library-research.md
output: plan.md
progress: true

Create an implementation plan for task: {task}, integrating anchored and external research.

## worker
reads: plan.md, anchor-context.md
output: implementation.md
progress: true

Implement task: {task} per plan.

## reviewer
reads: implementation.md, plan.md, anchor-context.md
output: review.md
progress: true

Initial review for task: {task}. Review only the changes introduced during this implementation and focus on ticket scope, acceptance criteria, and regressions.

## tester
reads: implementation.md, plan.md, anchor-context.md
output: test-results.md
progress: true

Initial tests for task: {task}. Run the most relevant ticket-scoped tests and checks with the highest signal.

## fixer
reads: implementation.md, review.md, test-results.md, plan.md
output: fixes.md
progress: true

Apply one fix pass for task: {task}. Prioritize test failures first, then critical/major review issues.

## reviewer
reads: implementation.md, review.md, test-results.md, fixes.md, plan.md, anchor-context.md
output: review-post-fix.md
progress: true

Quick re-check for task: {task}. Review only the changed files and hunks touched by implementation and fixes, and state clearly whether this is an unambiguous pass.

## tf-closer
reads: anchor-context.md, implementation.md, review.md, test-results.md, fixes.md, review-post-fix.md, research.md, library-research.md
output: close-summary.md
progress: true

Commit and close gate for task: {task}. maxFixPasses=1 per run. Use the quick re-check as the final go/no-go source of truth. Run tk close or tk status in_progress accordingly, and add blocker note when leaving ticket in_progress.
