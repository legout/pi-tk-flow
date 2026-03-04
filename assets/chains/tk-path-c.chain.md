---
name: tk-path-c
description: Deep tk workflow (sequential preset; convert research/validation to parallel in clarify when needed, includes one fixer pass + re-check, ends with tk-closer)
---

## scout
output: scout-context.md
progress: true

Scout codebase context for task: {task}. Focus on architecture, dependencies, and tests.

## context-builder
reads: scout-context.md
output: anchor-context.md
progress: true

Build re-anchored implementation context for task: {task}. Include constraints from .tf/AGENTS.md and .tf/knowledge when available.

## researcher
reads: anchor-context.md
output: research.md
progress: true

Research best practices and ecosystem guidance for task: {task}. Reuse existing .tf/knowledge first.

## librarian
reads: anchor-context.md
output: library-research.md
progress: true

Produce source-backed library internals/history findings for task: {task} with permalinks.

## planner-c
reads: anchor-context.md, research.md, library-research.md
output: plan.md
progress: true

Create implementation plan for task: {task}, integrating anchored and external research.

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

Initial tests for task: {task}.

## fixer
reads: implementation.md, review.md, test-results.md, plan.md
output: fixes.md
progress: true

Apply one fix pass for task: {task}. Prioritize test failures and critical review issues first.

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

## documenter
reads: implementation.md, review.md, fixes.md, review-post-fix.md, test-results-post-fix.md
output: docs-update.md
progress: true

Document externally visible changes for task: {task}.

## tk-closer
reads: anchor-context.md, implementation.md, review.md, test-results.md, fixes.md, review-post-fix.md, test-results-post-fix.md, research.md, library-research.md, docs-update.md
output: close-summary.md
progress: true

Commit and close gate for task: {task}. maxFixPasses=1 per run. Use post-fix review/test as source of truth when available. Run tk close or tk status in_progress accordingly, and add blocker note when leaving ticket in_progress.
