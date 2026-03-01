---
name: tk-path-a
description: Minimal tk workflow (scout -> context-builder -> worker -> reviewer -> fixer -> reviewer re-check -> tk-closer)
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

Initial review for task: {task}. Report critical/major/minor issues and concrete fixes.

## fixer
reads: implementation.md, review.md, anchor-context.md
output: fixes.md
progress: true

Apply one fix pass for task: {task} based on review.md. If no critical/major issues exist, record a no-op rationale.

## reviewer
reads: implementation.md, fixes.md, anchor-context.md
output: review-post-fix.md
progress: true

Post-fix re-check for task: {task}. Validate whether critical/major issues are resolved.

## tk-closer
reads: implementation.md, review.md, fixes.md, review-post-fix.md
output: close-summary.md
progress: true

Commit and close gate for task: {task}. maxFixPasses=1 per run. Use post-fix review as source of truth when available. Run tk close or tk status in_progress accordingly, and add blocker note when leaving ticket in_progress.
