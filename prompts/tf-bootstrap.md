---
description: Install/update tf workflow templates (agents, chains, prompts, and optional bundled skills)
model: minimax/m2.5
thinking: low
---

Run tf-bootstrap with `$@` args.

This command installs or updates the tf workflow templates:

```bash
/tf-bootstrap                    # install to user scope (~/.pi/agent/agents)
/tf-bootstrap --scope project    # install to project scope (.pi/agents)
/tf-bootstrap --dry-run          # preview changes without writing
/tf-bootstrap --copy-all         # also copy prompts and skills
/tf-bootstrap --no-overwrite     # preserve existing files
```

Execute the bootstrap extension command with the provided arguments.
