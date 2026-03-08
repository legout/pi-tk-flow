---
name: tf-refactor
description: Static refactor preset (seeded anchoring + plan + refactorer + validation). Top-level /tf-refactor may swap the final summary step for tf-closer in ticket mode.
---

## scout
output: scout-context.md
progress: true

Scout codebase context for refactor task: {task}. Focus on structural boundaries, affected files, relevant tests, and public API seams.

## context-builder
reads: false
output: anchor-context-base.md
progress: true

Build anchored refactor context for task: {task}. Read PROJECT.md when present, use AGENTS.md for repo operating guidance, and include lessons from .tf/AGENTS.md plus relevant .tf/knowledge when available.

## context-merger
reads: scout-context.md, anchor-context-base.md
output: anchor-context.md
progress: true

Merge `scout-context.md` and `anchor-context-base.md` into final `anchor-context.md`. Preserve all anchor sections and append scoped code context.

## plan-fast
reads: anchor-context.md
output: plan.md
progress: true

Create a behavior-preserving refactor plan for task: {task}. Emphasize structure improvement, API stability, and rollback safety.

## refactorer
reads: anchor-context.md, plan.md
output: implementation.md
progress: true

Execute the refactor for task: {task}. Preserve behavior, keep public APIs stable unless explicitly allowed, and constrain changes to the intended scope.

## reviewer
reads: implementation.md, plan.md, anchor-context.md
output: review.md
progress: true

Initial review for task: {task}. Focus on behavior preservation, API stability, regressions, and scope control.

## tester
reads: implementation.md, plan.md, anchor-context.md
output: test-results.md
progress: true

Run the most relevant tests and checks for task: {task}. Prioritize changed modules, public interfaces, and the highest-signal validations available.

## fixer
reads: implementation.md, review.md, test-results.md, plan.md, anchor-context.md
output: fixes.md
progress: true

Apply one fix pass for task: {task}. Prioritize test failures first, then critical/major review findings. Preserve the intended refactor scope.

## reviewer
reads: implementation.md, review.md, test-results.md, fixes.md, plan.md, anchor-context.md
output: review-post-fix.md
progress: true

Quick re-check for task: {task}. Review only the changed files and hunks touched by implementation and fixes, and state clearly whether behavior preservation is an unambiguous pass.

## documenter
reads: anchor-context.md, implementation.md, review.md, test-results.md, fixes.md, review-post-fix.md
output: close-summary.md
progress: true

Write a close summary for task: {task}. Summarize what changed, what validations ran, whether behavior preservation looks clear, and what follow-up work (if any) remains.
