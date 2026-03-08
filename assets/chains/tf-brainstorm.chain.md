---
name: tf-brainstorm
description: Brainstorm preset with seeded anchoring (static sequential chain; top-level /tf-brainstorm may add dynamic routing)
---

## scout
output: scout-context.md
progress: true

Scout project context for brainstorming task: {task}. If `topic-seed.json` exists, read it first. If `from-seed.md` exists, prioritize concepts/files implied by it. Focus on constraints, architecture seams, and existing test patterns.

## context-builder
reads: false
output: anchor-context-base.md
progress: true

Build anchored brainstorming context base for task: {task}. If `topic-seed.json` exists, read it first. Read PROJECT.md when present, use AGENTS.md for repo operating guidance, and include lessons from .tf/AGENTS.md plus relevant .tf/knowledge when present. If `from-seed.md` exists, synthesize it.

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
