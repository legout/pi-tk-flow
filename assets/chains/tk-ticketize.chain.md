---
name: tk-ticketize
description: Ticketization workflow (scout -> ticketizer) from planning docs to tk-ready slices
---

## scout
output: scout-context.md
progress: true

Scout codebase context for ticketization task: {task}. Focus on architecture seams and independently verifiable slice boundaries.

## ticketizer
reads: scout-context.md
output: ticketize.md
progress: true

Create a vertical-slice ticket breakdown for task: {task}. Generate dry-run artifacts and, when explicitly requested, execute tk create + tk dep safely.
