---
description: Install/update tf workflow templates (agents, chains, prompts, and optional bundled skills)
model: minimax/MiniMax-M2.5
thinking: low
---

Install tf workflow templates using the provided arguments: `$@`

Usage:
- `/tf-bootstrap-install` — install to user scope (~/.pi/agent/agents)
- `/tf-bootstrap-install --scope project` — install to project scope (.pi/agents)
- `/tf-bootstrap-install --dry-run` — preview changes without writing
- `/tf-bootstrap-install --copy-all` — also copy prompts and skills
- `/tf-bootstrap-install --no-overwrite` — preserve existing files

Execute the `/tf-bootstrap-install` extension command with the arguments provided by the user.
