---
name: tf-brainstorm
description: Brainstorm workflow with seeded anchoring (sequential preset: scout + context-builder + context-merger, then documenter)
---

## scout
output: scout-context.md
progress: true

Scout project context for brainstorming task: {task}. If `topic-seed.json` exists, read it first. If `from-seed.md` exists, prioritize concepts/files implied by it. Focus on constraints, architecture seams, and existing test patterns.

## context-builder
reads: false
output: anchor-context-base.md
progress: true

Build anchored brainstorming context base for task: {task}. If `topic-seed.json` exists, read it first. If `from-seed.md` exists, synthesize it. Include constraints from .tf/AGENTS.md and .tf/knowledge when present.

## context-merger
reads: scout-context.md, anchor-context-base.md
output: anchor-context.md
progress: true

Merge `scout-context.md` and `anchor-context-base.md` into final `anchor-context.md`. Preserve all anchor sections and append scout code context.

## documenter
reads: anchor-context.md
output: brainstorm-draft.md
progress: true

Draft a decision-ready brainstorming brief for task: {task} with options, trade-offs, recommendation, risks, and open questions.
