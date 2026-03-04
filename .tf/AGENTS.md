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

### Opt-in UI Dependencies Pattern
- **When to apply:** When creating Python packages with optional heavy UI dependencies (TUI frameworks, web servers, visualization libs)
- **Lesson:** Keep core `dependencies = []` empty and move optional deps to `[project.optional-dependencies]` under an `[ui]` or similar extra. This ensures non-UI workflows don't pull heavy libraries. Provide clear error messages when optional deps are missing, showing both pip and uv install commands.
- **Source tickets:** ptf-fo04 (2026-03-04)

### Subagent Chain Output File Location
- **When to apply:** When using `subagent` tool with `chain` and specifying `output` files in chain steps
- **Lesson:** The subagent tool creates a session subdirectory (e.g., `<chainDir>/<session-id>/`) within `chainDir` and writes output files there, not directly to `chainDir`. After chain completion, locate the actual output file with `find <chainDir> -name "<filename>" -type f` and copy it to the expected location if needed. The main agent cannot assume files are at the root of `chainDir`.
- **Source tickets:** ptf-53pu (2026-03-04)

### Safe File Opening Without Shell Injection
- **When to apply:** When implementing file opening with user-configurable PAGER/EDITOR environment variables
- **Lesson:** Never use `os.system(cmd)` with shell-constructed command strings from environment variables. Instead, use `shlex.split()` to safely parse editor/pager commands (which may include flags like "code -w"), `shutil.which()` to find executables without shell, and `subprocess.run([...], shell=False)` to execute without shell interpolation. This prevents shell injection when file paths contain special characters.
- **Source tickets:** ptf-bv4b (2026-03-04)

### Single Source of Truth for Command→Model Mappings
- **When to apply:** When implementing prompt template extensions that map commands to specific models
- **Lesson:** Maintain a single authoritative command→model mapping table in documentation (README.md) and reference it from all prompts and extension configs. This prevents drift between prompts, documentation, and extension behavior. When adding new commands, always update the canonical table first.
- **Source tickets:** ptf-cb32 (2026-03-04)

### Extension Behavior Documentation Pattern
- **When to apply:** When documenting optional pi extensions that modify command behavior
- **Lesson:** Document extension behavior with four key aspects: (1) Switch - what happens when command is invoked, (2) Fallback - what happens when command has no mapping, (3) Restore - what happens after command completes, (4) No-extension - what happens when extension is not installed. This provides clear expectations for users and implementers.
- **Source tickets:** ptf-cb32 (2026-03-04)
