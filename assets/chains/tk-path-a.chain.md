---
name: tk-path-a
description: Minimal tk workflow (scout -> context-builder -> worker -> reviewer -> tk-closer)
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

## worker
reads: anchor-context.md
output: implementation.md
progress: true

Implement task: {task} using the anchored context.

## reviewer
reads: implementation.md, anchor-context.md
output: review.md
progress: true

Review implementation for task: {task}. Report critical/major/minor issues and concrete fixes.

## tk-closer
reads: implementation.md, review.md
output: close-summary.md
progress: true

Commit and close gate for task: {task}. Determine ticket id, commit changes, and run tk close or tk status in-progress based on review outcomes.
