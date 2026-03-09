# Mock Infrastructure Contract

## Overview

This directory contains mock implementations of `tk` and `pi` CLIs for isolated testing of `tk-loop.sh`. These mocks provide deterministic behavior for integration tests without requiring actual ticket system infrastructure.

## Location

```
tests/tk-loop/mocks/
├── tk              # Mock tk CLI
├── pi              # Mock pi CLI
└── MOCK_CONTRACT.md # This document
```

## Mock: tk

### Interface

```bash
tk ready                    # Returns list of ready tickets
tk show <TICKET-ID>         # Returns ticket details (optional)
tk blocked                  # Returns blocked tickets (optional)
tk close <TICKET-ID>        # Closes a ticket (optional)
tk status                   # Returns CLI status
tk --help                   # Shows help
```

### Behavior Contract

#### `tk ready`

**Preconditions:**
- Environment variable `TK_MOCK_READY_FILE` may be set to a file path
- If set, the file contains zero or more lines of ticket data

**Behavior:**
1. If `TK_MOCK_READY_FILE` is unset or empty → returns empty output
2. If `TK_MOCK_READY_FILE` points to non-existent file → returns empty output
3. If file exists → outputs entire file contents to stdout
4. Each line format: `TICKET-ID description` (description is optional)
5. Exit code: always 0

**Post-conditions:**
- No state changes
- No side effects

**Example:**
```bash
export TK_MOCK_READY_FILE="/tmp/tickets.txt"
echo "ptf-abc1 Test ticket description" > "$TK_MOCK_READY_FILE"
tk ready  # Outputs: "ptf-abc1 Test ticket description"
```

#### `tk show <TICKET-ID>`

**Preconditions:**
- TICKET-ID argument must be provided

**Behavior:**
1. Outputs basic ticket information to stdout
2. Exit code: 0 on success, 1 if TICKET-ID missing

**Example:**
```bash
tk show ptf-abc1
# Output:
# Ticket: ptf-abc1
# Status: ready
```

#### `tk blocked`

**Behavior:**
1. Returns empty output (mock assumes no blocked tickets in test scenarios)
2. Exit code: 0

#### `tk close <TICKET-ID>`

**Preconditions:**
- TICKET-ID argument must be provided

**Behavior:**
1. Acknowledges close operation (logs to stderr if verbose)
2. Exit code: 0 on success, 1 if TICKET-ID missing

#### `tk status`

**Behavior:**
1. Outputs "tk mock: ready" to stdout
2. Exit code: 0

---

## Mock: pi

### Interface

```bash
pi "/tk-implement <TICKET-ID> --<MODE>"
```

### Behavior Contract

**Preconditions:**
- Command string must follow format: `pi "/tk-implement <TICKET-ID> --<MODE>"`
- **Mode is REQUIRED and must be one of**: `clarify`, `hands-free`, `dispatch`, `interactive`
- Environment variable `TK_MOCK_VERBOSE` may be set to "1" for debug output

**Behavior:**
1. Parses TICKET-ID from command string using regex pattern matching
2. Parses MODE flag from command string
3. **Validates MODE is present and valid** - rejects missing/invalid modes with exit 1
4. Determines success/failure based on TICKET-ID:
   - If TICKET-ID contains substring "FAIL" (case insensitive) → exit code 1
   - All other TICKET-IDs → exit code 0
5. If `TK_MOCK_VERBOSE=1`, outputs processing details to stderr

**Post-conditions:**
- No state changes (pure function of input)
- Exit code reflects simulated success/failure

**Exit Codes:**
- `0` - Success (ticket processed successfully with valid mode)
- `1` - Failure (ticket ID contains "FAIL", missing/invalid mode, or parse error)

**Example:**
```bash
# Success cases
pi "/tk-implement ptf-abc1 --clarify"      # Exit 0
pi "/tk-implement ptf-def2 --hands-free"   # Exit 0
pi "/tk-implement ptf-ghi3 --dispatch"     # Exit 0

# Failure cases (case insensitive)
pi "/tk-implement ptf-FAIL --clarify"      # Exit 1
pi "/tk-implement FAIL-123 --hands-free"   # Exit 1
pi "/tk-implement ptf-fail-456 --dispatch" # Exit 1

# Mode contract violations (now enforced)
pi "/tk-implement ptf-abc1"                # Exit 1 (missing mode)
pi "/tk-implement ptf-abc1 --invalid"      # Exit 1 (invalid mode)

# Verbose mode
TK_MOCK_VERBOSE=1 pi "/tk-implement ptf-abc1 --clarify"
# stderr: "Mock pi: Processing ticket=ptf-abc1 mode=clarify"
# stderr: "Mock pi: Simulating success for ptf-abc1"
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TK_MOCK_READY_FILE` | No | "" | Path to file containing mock ticket list for `tk ready` |
| `TK_MOCK_VERBOSE` | No | "0" | Enable verbose output to stderr when set to "1" |

---

## State Assertions

### Pre-conditions for Test Scenarios

1. **Environment Setup:**
   - `$TK_LOOP_STATE_DIR` must be set to a writable directory path
   - `$TK_MOCK_READY_FILE` must point to a valid file (or be unset for empty queue)
   - Mocks directory must be in `$PATH`
   - `PI_TK_INTERACTIVE_CHILD` must be unset (recursion guard)

2. **File Formats:**
   - Ticket list file (for `tk ready`): One ticket per line, format: `TICKET-ID [description]`

### Post-conditions for Test Scenarios

1. **On Success:**
   - Ticket appears in `$STATE_DIR/processed.jsonl` as JSONL record
   - Format: `{"id":"TICKET-ID","ts":"ISO8601_TIMESTAMP"}`

2. **On Failure:**
   - Ticket appears in `$STATE_DIR/failed.jsonl` as JSONL record
   - Format: `{"id":"TICKET-ID","ts":"ISO8601_TIMESTAMP","error":"exit code N"}`

3. **Metrics Update:**
   - `$STATE_DIR/metrics.json` updated with current counts
   - Format: Single JSON object with fields: `started_at`, `mode`, `tickets_processed`, `tickets_failed`, `current_ticket`, `pid`

---

## Test Integration

### Using Mocks in Tests

```bash
# Setup
export TK_LOOP_STATE_DIR="$(mktemp -d)/.tk-loop-state"
export TK_MOCK_READY_FILE="$(mktemp)/tickets.txt"
export PATH="tests/tk-loop/mocks:$PATH"
unset PI_TK_INTERACTIVE_CHILD  # Clear recursion guard
mkdir -p "$TK_LOOP_STATE_DIR"

# Create test tickets
cat > "$TK_MOCK_READY_FILE" <<EOF
ptf-test1 First ticket
ptf-test2 Second ticket
ptf-FAIL1 Ticket that will fail
ptf-test3 Third ticket
EOF

# Run loop
.tf/scripts/tk-loop.sh --clarify

# Verify results
grep -q "ptf-test1" "$TK_LOOP_STATE_DIR/processed.jsonl"
grep -q "ptf-FAIL1" "$TK_LOOP_STATE_DIR/failed.jsonl"
```

### Cleanup

```bash
rm -rf "$TK_LOOP_STATE_DIR"
rm -f "$TK_MOCK_READY_FILE"
```

---

## Determinism Guarantees

The mock infrastructure provides deterministic behavior:

1. **tk ready**: Output is deterministic based on `TK_MOCK_READY_FILE` contents
2. **pi**: Success/failure is deterministic based on ticket ID pattern and mode validity
3. **No external dependencies**: Mocks don't call external services
4. **No timing dependencies**: All operations complete immediately
5. **Reproducible**: Same inputs always produce same outputs and exit codes

This enables reliable, fast integration tests without flakiness.
