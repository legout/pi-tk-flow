---
name: tk-plan
description: Planning workflow (scout -> context-builder -> documenter(PRD) -> documenter(spec) -> documenter(design) -> planner)
---

## scout
output: scout-context.md
progress: true

Scout project context for planning task: {task}. Focus on current architecture, relevant files, constraints, and tests.

## context-builder
reads: scout-context.md
output: anchor-context.md
progress: true

Build anchored planning context for task: {task}. Include constraints from .tf/AGENTS.md and .tf/knowledge when present.

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

## planner
reads: anchor-context.md, prd-draft.md, spec-draft.md, design-draft.md
output: plan-draft.md
progress: true

Create an actionable implementation plan for task: {task} with small tasks, dependencies, verification steps, and rollback notes.
