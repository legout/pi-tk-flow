---
name: tk-plan-thorough
description: Thorough planning workflow with seeded anchoring (sequential preset: scout + context-builder + context-merger, then PRD→Spec→Design→Plan)
---

## scout
output: scout-context.md
progress: true

Scout project context for planning task: {task}. If `topic-seed.json` exists, read it first. If `from-seed.md` exists, prioritize concepts/files implied by it. Focus on current architecture, relevant files, constraints, and tests.

## context-builder
reads: false
output: anchor-context-base.md
progress: true

Build anchored planning context base for task: {task}. If `topic-seed.json` exists, read it first. If `from-seed.md` exists, synthesize it. Include constraints from .tf/AGENTS.md and .tf/knowledge when present.

## context-merger
reads: scout-context.md, anchor-context-base.md
output: anchor-context.md
progress: true

Merge `scout-context.md` and `anchor-context-base.md` into final `anchor-context.md`. Preserve all anchor sections and append scout code context.

## documenter
reads: anchor-context.md
output: prd-draft.md
progress: true

Draft a PRD for task: {task} with Problem Statement, Solution, User Stories, Implementation Decisions, Testing Decisions, and Out of Scope.

## documenter
reads: anchor-context.md, prd-draft.md
output: spec-draft.md
progress: true

Draft a technical spec for task: {task} with Architecture, Components, Data Flow, Error Handling, Testing Strategy, and Risks.

## documenter
reads: anchor-context.md, prd-draft.md, spec-draft.md
output: design-draft.md
progress: true

Create a canonical design brief for task: {task}. Include chosen architecture, component contracts, key flows, risks, and explicit decisions.

## planner-c
reads: anchor-context.md, prd-draft.md, spec-draft.md, design-draft.md
output: plan-draft.md
progress: true

Create an actionable implementation plan for task: {task} with small tasks, dependencies, verification steps, and rollback notes.
