# Lessons Learned (Reusable)

Add lessons here only when they are:
1. **New** (not already documented), and
2. **Useful** for later ticket implementations.

Avoid ticket-specific trivia and duplicates.

## Format

### <Short lesson title>
- **When to apply:** <situation>
- **Lesson:** <concise reusable guidance>
- **Source tickets:** <ticket-id list>

### Recursion Guard Pattern for Nested Commands
- **When to apply:** When implementing command wrappers that invoke themselves or similar commands (e.g., pi calling pi, nested tk-implement)
- **Lesson:** Use an environment variable as a recursion guard. Set `ENV_VAR=1` when invoking the nested command, check for its presence at entry to skip wrapper logic and pass through to core execution. This prevents infinite loops while allowing the nested call to run the actual implementation.
- **Source tickets:** ptf-53pu (2026-03-04)

### Pi Extension Command Registration
- **When to apply:** When creating new pi extension commands that spawn external processes or integrate external tools
- **Lesson:** Use the ExtensionAPI pattern: `export default function extensionName(pi: ExtensionAPI)` and register commands via `pi.registerCommand("namespace command", { description, examples, handler })`. The handler receives `(args: string, ctx)` where args is the raw command string after the command name. Check for dependencies (Python, packages) before spawning and provide actionable error messages.
- **Source tickets:** ptf-21fw (2026-03-04)
