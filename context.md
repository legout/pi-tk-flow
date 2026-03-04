Done! I wrote the findings to `/Users/volker/coding/libs/pi-tk-flow/context.md`.

## Summary

**Found 3 key areas:**

1. **Existing Flag Parsing Code** (`extensions/tk-bootstrap.ts:35-44`):
   - `parseFlag(args, flag)` - regex-based boolean flag detection
   - `parseScope(args)` - extracts `--scope project|user` values
   - `parseCopyOptions(args)` - handles `--copy-all/--materialize` combinations

2. **Flag Validation Patterns** (documented in all `prompts/tk-*.md` files):
   - Required first argument check
   - Mutual exclusivity checks (e.g., `--fast` vs `--thorough`, `--create` vs `--dry-run`)
   - Preference logic: if both `--async` and `--clarify` set, prefer async
   - Unknown flag rejection with help message

3. **Flag Matrix Plans** (in `.tf/plans/2026-03-04-ralph-wiggum-method-implementation/`):
   - Upcoming flags: `--interactive`, `--hands-free`, `--dispatch`
   - Full mutual exclusivity matrix with error messages defined
   - Plan to create `tests/tk-implement/flag-matrix.md` documenting valid/invalid combos

**Key Finding**: There are two parsing approaches - TypeScript code in extensions (actual function), and Markdown prompts (rule-based, executed by LLMs). No shared library exists.