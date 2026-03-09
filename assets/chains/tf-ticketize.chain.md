---
name: tf-ticketize
description: Ticketization workflow (scout -> ticketizer) from planning docs to tk-ready slices
---

Note: When `artifacts: true` is used, outputs may be written under run/session subdirectories (including `parallel-*` folders) instead of directly at `<CHAIN_DIR>/<file>`. Callers should materialize expected outputs to canonical `<CHAIN_DIR>/` paths and verify required files before final reporting.

## scout
output: scout-context.md
progress: true

Scout codebase context for ticketization task: {task}. Focus on architecture seams and independently verifiable slice boundaries.

## ticketizer
reads: scout-context.md
output: ticketize.md
progress: true

Create a vertical-slice ticket breakdown for task: {task}. Generate dry-run artifacts and, when explicitly requested, execute tk create + tk dep safely.
