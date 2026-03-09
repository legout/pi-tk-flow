# Mock Infrastructure Contract

## Scope
This contract defines deterministic mock behavior for end-to-end testing of:
- `.tf/scripts/tk-loop.sh`
- `.tf/scripts/test-tk-loop.sh`

Mocks live in `.tf/scripts/test-mocks/` and shadow real CLIs by prepending that directory to `PATH`.

## Preconditions
- `PATH` includes `.tf/scripts/test-mocks` before real binaries.
- `TK_LOOP_STATE_DIR` points to a writable test state directory.
- `TK_MOCK_READY_FILE` points to a text file containing mock `tk ready` output.

## Mock `tk`

### Interface
- `tk ready`
- Optional no-op support: `tk show`, `tk close`, `tk blocked`, `tk status`

### Behavior
1. `tk ready` prints the exact content of `$TK_MOCK_READY_FILE` if it exists.
2. If `$TK_MOCK_READY_FILE` is missing or empty, `tk ready` prints nothing.
3. Ticket lines follow `<ticket-id> <description...>` format; `tk-loop.sh` parses only the first column.
4. `tk ready` exits `0` on success.
5. Unsupported commands exit non-zero with an error message.

## Mock `pi`

### Interface
- `pi "/tk-implement <ticket-id> --<mode>"`

### Behavior
1. Parses `<ticket-id>` from `/tk-implement` command string.
2. Deterministic failure rule:
   - ticket id containing `fail` (case-insensitive) -> exit `1`
   - otherwise -> exit `0`
3. Optional debug output when `TK_MOCK_PI_VERBOSE` is set.
4. Optional delay when `TK_MOCK_PI_SLEEP_SEC` is set.
5. Unparseable command exits `2`.

## Post-conditions / Assertions
After running `tk-loop.sh`, tests assert:
- Successes append JSON objects to `processed.jsonl` with keys: `id`, `ts`.
- Failures append JSON objects to `failed.jsonl` with keys: `id`, `ts`, `error`.
- `metrics.json` remains valid JSON and includes counters and metadata.
- `loop.log` remains JSONL with `ts`, `level`, `msg`.

## Determinism guarantees
- No network calls.
- No dependency on external ticket state.
- Test fixtures control all ready tickets via `TK_MOCK_READY_FILE`.
- Failure behavior depends only on ticket id pattern.
