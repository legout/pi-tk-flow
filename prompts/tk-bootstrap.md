---
description: Install/update tk workflow templates (agents, chains, optionally prompts/skills)
model: minimax/m2.5
thinking: low
---

Run tk-bootstrap with `$@` args.

This command installs or updates the tk workflow templates:

```bash
/tk-bootstrap                    # install to user scope (~/.pi/agent/agents)
/tk-bootstrap --scope project    # install to project scope (.pi/agents)
/tk-bootstrap --dry-run          # preview changes without writing
/tk-bootstrap --copy-all         # also copy prompts and skills
/tk-bootstrap --no-overwrite     # preserve existing files
```

Execute the bootstrap extension command with the provided arguments.
