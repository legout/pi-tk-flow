# tk-loop - External Ralph Wiggum Loop

Continuously process tickets from the tk queue using `tk ready` and `pi "/tk-implement"` with configurable execution modes.

## Installation

Copy `tk-loop.sh` to a location in your PATH:

```bash
cp tk-loop.sh /usr/local/bin/tk-loop
chmod +x /usr/local/bin/tk-loop
```

Or use directly from the scripts directory:

```bash
./tk-loop.sh [OPTIONS]
```

## Requirements

- `tk` - Ticket CLI installed and in PATH
- `pi` - Pi coding agent installed and in PATH
- Bash 4.0+

## Usage

### Basic Usage

```bash
# Default mode (clarify)
tk-loop

# Process current queue once and exit
tk-loop --once

# Dry-run to see what would be executed
tk-loop --dry-run --once
```

### Execution Modes

#### Clarify Mode (Default)
Opens TUI for user review before each ticket:

```bash
tk-loop --clarify
```

#### Hands-Free Mode
Auto-approves tickets without user interaction:

```bash
tk-loop --hands-free
```

#### Dispatch Mode
Non-blocking execution with notification on completion:

```bash
tk-loop --dispatch
```

#### Interactive Mode
Full interactive control:

```bash
tk-loop --interactive
```

### Common Options

```bash
# Verbose logging
tk-loop --verbose

# Process queue once and exit (don't loop)
tk-loop --once

# Show what would be done without executing
tk-loop --dry-run --once

# Custom state directory
tk-loop --once  # Uses $TK_LOOP_STATE_DIR or .tk-loop-state

# Show help
tk-loop --help

# Show version
tk-loop --version
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TK_LOOP_POLL_INTERVAL` | `5` | Seconds between ticket polls |
| `TK_LOOP_STATE_DIR` | `.tk-loop-state` | State directory path |
| `PI_TK_INTERACTIVE_CHILD` | - | Recursion guard (set internally) |

## State Directory Schema

The state directory (default: `.tk-loop-state/`) contains:

```
.tk-loop-state/
├── loop.pid          # PID lock file (prevents concurrent runs)
├── current-ticket    # Currently processing ticket ID
├── processed.jsonl   # Successfully processed tickets
├── failed.jsonl      # Failed ticket records
├── loop.log          # Structured JSONL log
└── metrics.json      # Runtime metrics
```

### File Formats

**processed.jsonl**:
```json
{"id":"ptf-abc1","ts":"2026-03-09T04:00:00Z"}
```

**failed.jsonl**:
```json
{"id":"ptf-abc2","ts":"2026-03-09T04:01:00Z","error":"exit code 1"}
```

**loop.log** (structured JSONL):
```json
{"ts":"2026-03-09T04:00:00Z","level":"INFO","msg":"Processing ticket: ptf-abc1"}
```

**metrics.json**:
```json
{
  "started_at": "2026-03-09T04:00:00Z",
  "mode": "clarify",
  "tickets_processed": 5,
  "tickets_failed": 1,
  "current_ticket": "ptf-abc3",
  "last_poll_at": "2026-03-09T04:05:00Z",
  "total_runtime_sec": 300,
  "pid": 12345
}
```

## Troubleshooting

### Stale Lock File

**Symptom**: "Another tk-loop instance is already running"

If the previous instance crashed without cleanup:

```bash
# Check if the PID is actually running
ps -p $(cat .tk-loop-state/loop.pid) 2>/dev/null || echo "Process not running"

# Remove stale lock manually
rm .tk-loop-state/loop.pid
```

The script automatically detects and removes stale locks on startup.

### Recursion Guard Triggered

**Symptom**: "Nested tk-loop detected (PI_TK_INTERACTIVE_CHILD=1)"

This prevents infinite loops when tk-loop is invoked from within pi. To override (for testing only):

```bash
unset PI_TK_INTERACTIVE_CHILD
tk-loop
```

### Failed Tickets Not Retrying

**Expected Behavior**: tk-loop does NOT automatically retry failed tickets. This is by design to prevent infinite loops with failing tickets.

**Solution**: Manually retry failed tickets:

```bash
# Check failed tickets
cat .tk-loop-state/failed.jsonl

# Re-run for a specific ticket
tk ready  # Ensure ticket is in ready state
pi "/tk-implement FAILED_TICKET_ID"
```

### tk or pi Not Found

**Symptom**: "Missing required dependencies: tk pi"

```bash
# Verify installations
which tk
which pi

# Or check if in PATH
tk --help
pi --help
```

## Testing

Run the integration test suite:

```bash
cd .tf/scripts
./test-tk-loop.sh
```

### Test Scenarios

The test suite covers:

- **empty** - Handles empty ticket queue
- **single** - Processes single ticket
- **multi** - Processes multiple tickets sequentially
- **failure** - Continues after ticket failure
- **guard** - Recursion guard prevents nested loops
- **mutex** - Prevents concurrent loop execution
- **schema** - Validates output format
- **pid** - PID lock management
- **signal** - Graceful shutdown on SIGINT/SIGTERM

### Mock Infrastructure

Tests use deterministic mocks for `tk` and `pi` in `test-mocks/`:

| Mock | Behavior |
|------|----------|
| `test-mocks/tk` | Returns test tickets based on `MOCK_TICKET_FILE` |
| `test-mocks/pi` | Simulates pi execution with configurable delays |

See `MOCK_CONTRACT.md` for full mock behavior specification.

## Design Notes

### No Automatic Retry

tk-loop intentionally does NOT retry failed tickets automatically. This prevents:
- Infinite loops with permanently failing tickets
- Resource exhaustion from repeated failures
- Confusion about which attempts failed

Failed tickets are logged to `failed.jsonl` for manual review.

### Sequential Processing

Tickets are processed one-at-a-time in queue order. This ensures:
- Predictable resource usage
- Clear logs and metrics
- Safe failure isolation

### Atomic State Updates

All state file writes use atomic temp-file + rename pattern to prevent corruption:

```bash
cat > "$temp_file" <<EOF
{ ... }
EOF
mv "$temp_file" "$STATE_DIR/metrics.json"
```

## License

Part of pi-tk-flow project.
