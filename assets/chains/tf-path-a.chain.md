---
name: tf-path-a
description: Minimal post-anchor tf execution preset (worker -> reviewer -> fixer -> quick re-check -> tf-closer)
---

Note: When `artifacts: true` is used, outputs may be written under run/session subdirectories (including `parallel-*` folders) instead of directly at `<CHAIN_DIR>/<file>`. Callers should materialize expected outputs to canonical `<CHAIN_DIR>/` paths and verify required files before final reporting.

## worker
reads: anchor-context.md
output: implementation.md
progress: true

Implement task: {task} using the existing anchored context.

## reviewer
reads: implementation.md, anchor-context.md
output: review.md
progress: true

Initial review for task: {task}. Review only the changes introduced during implementation and focus on ticket scope, regressions, and acceptance criteria.

## fixer
reads: implementation.md, review.md, anchor-context.md
output: fixes.md
progress: true

Apply one fix pass for task: {task} based on review.md. If no critical/major issues exist, record a no-op rationale.

## reviewer
reads: implementation.md, review.md, fixes.md, anchor-context.md
output: review-post-fix.md
progress: true

Quick re-check for task: {task}. Review only the changed files and hunks touched by implementation and fixes, and state clearly whether this is an unambiguous pass.

## tf-closer
reads: anchor-context.md, implementation.md, review.md, fixes.md, review-post-fix.md
output: close-summary.md
progress: true

Commit and close gate for task: {task}. maxFixPasses=1 per run. Use the quick re-check as the final go/no-go source of truth. Run tk close or tk status in_progress accordingly, and add blocker note when leaving ticket in_progress.
