---
id: ptf-n5ir
status: closed
deps: [ptf-erm8]
links: []
created: 2026-03-01T11:18:41Z
type: feature
priority: 3
assignee: legout
parent: ptf-21fw
tags: [web-ui, docs, ui, vertical-slice, tui]
---
# S7 Add web mode entry and user-facing docs

Support /tf ui --web command output and document install/run/troubleshooting plus topic naming conventions.

## Design

Refs: PRD US-5, US-6; Spec C-1 web behavior; Plan Tasks 6 and 8.

## Acceptance Criteria

- [ ] /tf ui --web prints textual serve "python -m pi_tk_flow_ui"\n- [ ] Output includes host-binding security note\n- [ ] README includes install and run snippets for terminal + web\n- [ ] .tf/knowledge/README.md documents topic naming conventions


## Notes

**2026-03-04T16:10:27Z**

Implementation complete (verification-only):

• All 4 acceptance criteria verified:
  - AC1: /tf ui --web prints textual serve command with python -m pi_tk_flow_ui
  - AC2: Output includes host-binding and security warnings
  - AC3: README includes install/run snippets for terminal + web modes
  - AC4: .tf/knowledge/README.md documents topic naming conventions

• Files verified: extensions/tf-ui.ts, README.md, .tf/knowledge/README.md
• No code changes required - implementation already meets all criteria
• Tests: 4/4 acceptance criteria verified
• Commit: none (verification-only task)
