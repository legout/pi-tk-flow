---
name: tk-brainstorm
description: Brainstorm workflow (scout -> context-builder -> documenter) producing a decision-ready brief
---

## scout
output: scout-context.md
progress: true

Scout project context for brainstorming task: {task}. Focus on constraints, architecture seams, and existing test patterns.

## context-builder
reads: scout-context.md
output: anchor-context.md
progress: true

Build anchored brainstorming context for task: {task}. Include constraints from .tf/AGENTS.md and .tf/knowledge when present.

## documenter
reads: anchor-context.md
output: brainstorm-draft.md
progress: true

Draft a decision-ready brainstorming brief for task: {task} with options, trade-offs, recommendation, risks, and open questions.
