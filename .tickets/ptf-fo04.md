---
id: ptf-fo04
status: closed
deps: []
links: []
created: 2026-03-01T11:18:16Z
type: chore
priority: 1
assignee: legout
parent: ptf-21fw
tags: [ui, python, foundation, vertical-slice, tui]
---
# S1 Bootstrap optional UI runtime package

Create python/pi_tk_flow_ui package skeleton with python -m entrypoint and optional [ui] extras so UI remains opt-in.

## Design

Refs: PRD US-6, ID-6; Spec C-8, E-1, E-2; Plan Task 1.

## Acceptance Criteria

- [ ] python/pyproject.toml defines requires-python >=3.10 and [ui] extras (textual, pyyaml)\n- [ ] python/pi_tk_flow_ui/__init__.py and __main__.py support python -m pi_tk_flow_ui\n- [ ] Missing UI deps show actionable install guidance\n- [ ] Core non-UI workflows remain unaffected


## Notes

**2026-03-04T13:05:06Z**

Implementation complete: Python package skeleton created with opt-in UI deps (textual>=0.47.0, pyyaml>=6.0) via [ui] extra. Core dependencies remain empty. Entry point python -m pi_tk_flow_ui works with actionable error when UI deps missing. Files: python/pyproject.toml, python/pi_tk_flow_ui/__init__.py, python/pi_tk_flow_ui/__main__.py. Commit: 339e4a0
