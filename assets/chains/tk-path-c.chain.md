---
name: tk-path-c
description: Deep tk workflow (sequential preset; convert research/validation to parallel in clarify when needed, ends with tk-closer)
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

## planner
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

Review implementation for task: {task}.

## tester
reads: implementation.md, plan.md, review.md
output: test-results.md
progress: true

Test implementation for task: {task}.

## fixer
reads: implementation.md, review.md, test-results.md
output: fixes.md
progress: true

Fix critical/major issues for task: {task}. Prioritize test failures and critical review issues first.

## documenter
reads: implementation.md, review.md, fixes.md
output: docs-update.md
progress: true

Document externally visible changes for task: {task}.

## tk-closer
reads: implementation.md, review.md, test-results.md, fixes.md, docs-update.md
output: close-summary.md
progress: true

Commit and close gate for task: {task}. Determine ticket id, commit changes, and run tk close or tk status in-progress based on review/test/fix outcomes.
