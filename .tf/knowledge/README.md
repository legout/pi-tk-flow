# Knowledge Cache

Reusable implementation knowledge for tk workflows.

## Directory Structure

```
.tf/knowledge/
├── topics/           # Reusable topic-level knowledge
│   ├── seed-*.md     # Project scaffolding topics
│   ├── plan-*.md     # Planning workflow topics
│   ├── spike-*.md    # Spike/research solutions
│   └── baseline-*.md # Baseline pattern topics
├── tickets/          # Ticket-level research and implementation
│   └── <ticket-id>/
│       ├── research.md
│       ├── implementation.md
│       └── review.md
└── index.md          # Optional topic index
```

## Topic Naming Conventions

Topics in `topics/*.md` are automatically categorized by the TUI based on filename prefix:

| Prefix | Type | Purpose | Example |
|--------|------|---------|---------|
| `seed-` | Seed | Project scaffolding, initial setup patterns | `seed-python-package.md` |
| `plan-` | Plan | Planning workflows and methodologies | `plan-implementation-workflow.md` |
| `spike-` | Spike | Research findings and technical spikes | `spike-auth-flow.md` |
| `baseline-` | Baseline | Baseline patterns and standards | `baseline-error-handling.md` |
| (none) | Other | Miscellaneous topics | `my-notes.md` |

### Best Practices

1. **Use kebab-case**: `plan-implementation-workflow.md` not `planImplementationWorkflow.md`
2. **Start with a heading**: Topics should have a `# Title` as the first line
3. **Include keywords**: Add YAML frontmatter with keywords for better searchability

Example topic file:

```markdown
---
keywords: [python, packaging, setup]
---

# Python Package Setup

This topic covers best practices for setting up Python packages...
```

## Ticket-Level Knowledge

Ticket directories follow the pattern `tickets/<ticket-id>/` and contain:

- `research.md` - Research notes and references
- `implementation.md` - Implementation notes
- `review.md` - Review findings
- `fixes.md` - Post-review fixes
- `close-summary.md` - Summary at ticket close

## TUI Integration

The `/tf ui` command (when installed with `[ui]` extras) provides:

- **Topics Tab**: Browse all topics with automatic grouping by type
- **Search**: Search topics by title or keywords
- **Preview**: View topic content in the detail panel
- **Open**: Press `o` to open the topic in your `$PAGER` or `$EDITOR`

Topics are scanned on-the-fly from `.tf/knowledge/topics/*.md` when the TUI loads.
