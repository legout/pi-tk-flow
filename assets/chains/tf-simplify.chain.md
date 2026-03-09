---
name: tf-simplify
description: Static simplify preset (seeded anchoring + plan + simplifier + validation). Top-level /tf-simplify may swap the final summary step for tf-closer in ticket mode.
---

Note: When `artifacts: true` is used, outputs may be written under run/session subdirectories (including `parallel-*` folders) instead of directly at `<CHAIN_DIR>/<file>`. Callers should materialize expected outputs to canonical `<CHAIN_DIR>/` paths and verify required files before final reporting.

## scout
output: scout-context.md
progress: true

Scout codebase context for simplify task: {task}. Focus on complexity hotspots, affected files, relevant tests, and control-flow risk areas.

## context-builder
reads: false
output: anchor-context-base.md
progress: true

Build anchored simplification context for task: {task}. Read PROJECT.md when present, use AGENTS.md for repo operating guidance, and include lessons from .tf/AGENTS.md plus relevant .tf/knowledge when available.

## context-merger
reads: scout-context.md, anchor-context-base.md
output: anchor-context.md
progress: true

Merge `scout-context.md` and `anchor-context-base.md` into final `anchor-context.md`. Preserve all anchor sections and append scoped code context plus hotspot findings.

## plan-fast
reads: anchor-context.md
output: plan.md
progress: true

Create a behavior-preserving simplification plan for task: {task}. Emphasize readability, complexity reduction, and rollback safety.

## simplifier
reads: anchor-context.md, plan.md
output: implementation.md
progress: true

Execute the simplification for task: {task}. Preserve behavior, reduce complexity, improve clarity, and constrain changes to the intended scope.

## reviewer
reads: implementation.md, plan.md, anchor-context.md
output: review.md
progress: true

Initial review for task: {task}. Focus on behavior preservation, readability, regressions, and whether simplification made intent clearer rather than more obscure.

## tester
reads: implementation.md, plan.md, anchor-context.md
output: test-results.md
progress: true

Run the most relevant tests and checks for task: {task}. Prioritize changed modules, behavior-sensitive paths, and the highest-signal validations available.

## fixer
reads: implementation.md, review.md, test-results.md, plan.md, anchor-context.md
output: fixes.md
progress: true

Apply one fix pass for task: {task}. Prioritize test failures first, then critical/major review findings. Preserve the intended simplification scope.

## reviewer
reads: implementation.md, review.md, test-results.md, fixes.md, plan.md, anchor-context.md
output: review-post-fix.md
progress: true

Quick re-check for task: {task}. Review only the changed files and hunks touched by implementation and fixes, and state clearly whether behavior preservation and readability are an unambiguous pass.

## documenter
reads: anchor-context.md, implementation.md, review.md, test-results.md, fixes.md, review-post-fix.md
output: close-summary.md
progress: true

Write a close summary for task: {task}. Summarize what changed, what validations ran, whether behavior preservation and readability look clear, and what follow-up work (if any) remains.
