# Refined Implementation Plan: External Ralph Wiggum Loop

**Status**: Refined
**Created**: 2026-03-04
**Refined**: 2026-03-05
**PRD**: 01-prd.md
**Spec**: 02-spec.md
**Design**: 00-design.md

---

## Overview

Implement an external bash script that continuously processes tickets from the tk queue using `tk ready` and `pi "/tk-implement <ID>"` with configurable execution modes.

**Total Effort**: ~5-7 hours
**Implementation Strategy**: Vertical slices, test-driven, incremental delivery

---

## Required Changes Summary

### Change 1: Resolve Retry-Policy Conflict ✅
**Issue**: PRD (Out of Scope) says "Failed tickets are logged but not automatically retried" but Spec and Plan implement retry logic with MAX_RETRIES=3.

**Resolution**: Follow PRD direction — remove retry logic from main loop. Failed tickets are recorded and the loop continues. A separate `--retry-failed` flag can be added in a future enhancement.

### Change 2: Expand Task 11 with End-to-End Integration Test ✅
**Issue**: Task 11 was under-specified for integration testing.

**Resolution**: Added comprehensive end-to-end test scenario with mock infrastructure that validates the full loop behavior.

### Change 3: Specify Mock Infrastructure Contract ✅
**Issue**: Mock infrastructure mentioned in Spec section 6.4 but not detailed in implementation plan.

**Resolution**: Added Task 11.5 with complete mock infrastructure contract and helper utilities.

### Change 4: Normalize Script Path and State-File Schema ✅
**Issue**: Inconsistent paths between documents (`.tf/scripts/` vs `scripts/`) and mixed JSON/JSONL formats.

**Resolution**: Standardized on:
- Script path: `.tf/scripts/tk-loop.sh`
- State directory: `.tk-loop-state/`
- Log format: JSONL (newline-delimited JSON) for `processed.jsonl` and `failed.jsonl`
- Metrics format: Single JSON object in `metrics.json`

---

## Task Breakdown

### Task 1: Bootstrap Script Structure
**Priority**: P0
**Effort**: 30 minutes
**Dependencies**: None

**Description**: Create the basic script scaffold with shebang, error handling, and help text.

**Files**:
- `.tf/scripts/tk-loop.sh` (new)

**Implementation**:
```bash
#!/usr/bin/env bash
set -euo pipefail

# Constants
SCRIPT_NAME="tk-loop"
VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Help text
show_help() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

External Ralph Wiggum Loop - Continuously process tk tickets

Options:
    --clarify       Run with clarify TUI (default)
    --hands-free    Run in hands-free mode
    --dispatch      Run in dispatch mode
    --interactive   Run in interactive mode
    --dry-run       Show what would be done without executing
    --verbose       Enable verbose logging
    --help          Show this help message

Environment Variables:
    TK_LOOP_POLL_INTERVAL   Seconds between polls (default: 5)
    TK_LOOP_STATE_DIR       State directory (default: .tk-loop-state)

Examples:
    $SCRIPT_NAME --clarify
    $SCRIPT_NAME --dispatch --verbose
EOF
}

# Logging
log() { echo "[$(date -Iseconds)] $*"; }
error() { echo "ERROR: $*" >&2; }

# Main entry point
main() {
    log "Starting $SCRIPT_NAME v$VERSION"
    # TODO: Implement
}

main "$@"
```

**Verification**:
- Script runs with `--help` flag
- Exits with error on unknown flags
- Has proper shebang and permissions (`chmod +x`)

**Rollback**: Delete `.tf/scripts/tk-loop.sh`

---

### Task 2: Flag Parser Implementation
**Priority**: P0
**Effort**: 30 minutes
**Dependencies**: Task 1

**Description**: Implement command-line flag parsing for mode selection and options.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
# Configuration (defaults)
MODE="clarify"
DRY_RUN=false
VERBOSE=false
POLL_INTERVAL="${TK_LOOP_POLL_INTERVAL:-5}"
STATE_DIR="${TK_LOOP_STATE_DIR:-.tk-loop-state}"

# Mode validation - ensure only one mode flag
parse_flags() {
    local mode_count=0
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clarify)     MODE="clarify"; ((mode_count++)) ;;
            --hands-free)  MODE="hands-free"; ((mode_count++)) ;;
            --dispatch)    MODE="dispatch"; ((mode_count++)) ;;
            --interactive) MODE="interactive"; ((mode_count++)) ;;
            --dry-run)     DRY_RUN=true ;;
            --verbose)     VERBOSE=true ;;
            --help)        show_help; exit 0 ;;
            --version)     echo "$SCRIPT_NAME v$VERSION"; exit 0 ;;
            *)             error "Unknown flag: $1"; exit 1 ;;
        esac
        shift
    done
    
    # Validate mutually exclusive modes
    if [[ $mode_count -gt 1 ]]; then
        error "Cannot combine multiple mode flags (--clarify, --hands-free, --dispatch, --interactive)"
        exit 1
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        log "Mode: $MODE"
        log "Poll interval: ${POLL_INTERVAL}s"
        log "State directory: $STATE_DIR"
    fi
}
```

**Verification**:
- `./tk-loop.sh --clarify` sets MODE="clarify"
- `./tk-loop.sh --dispatch --verbose` logs mode and settings
- `./tk-loop.sh --clarify --hands-free` exits with error (mutually exclusive)
- Invalid flags exit with error

**Rollback**: Revert flag parsing code

---

### Task 3: Recursion Guard
**Priority**: P0
**Effort**: 15 minutes
**Dependencies**: Task 2

**Description**: Prevent nested script invocations using environment variable.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
check_recursion_guard() {
    if [[ "${PI_TK_INTERACTIVE_CHILD:-}" == "1" ]]; then
        error "Nested tk-loop detected (PI_TK_INTERACTIVE_CHILD=1)"
        error "This prevents infinite recursion loops. Exiting."
        exit 1
    fi
}
```

**Verification**:
- `PI_TK_INTERACTIVE_CHILD=1 ./tk-loop.sh` exits with error
- Normal invocation succeeds

**Rollback**: Remove recursion guard check

---

### Task 4: Dependency Validation
**Priority**: P0
**Effort**: 15 minutes
**Dependencies**: Task 3

**Description**: Verify required CLI tools are available.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
validate_dependencies() {
    local missing=()

    command -v tk >/dev/null 2>&1 || missing+=("tk")
    command -v pi >/dev/null 2>&1 || missing+=("pi")

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing required dependencies: ${missing[*]}"
        error "Please install missing tools and try again"
        exit 1
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        log "Dependencies OK: tk=$(command -v tk), pi=$(command -v pi)"
    fi
}
```

**Verification**:
- Script exits with error if `tk` or `pi` not in PATH
- Verbose mode shows dependency paths

**Rollback**: Remove dependency validation

---

### Task 5: Ticket Parser
**Priority**: P0
**Effort**: 30 minutes
**Dependencies**: Task 4

**Description**: Parse `tk ready` output to extract ticket IDs.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
parse_tickets() {
    local tk_output="$1"

    # Parse ticket IDs from tk ready output
    # Format: "ptf-abc1 [status] - Title" or "TICKET-ID description"
    echo "$tk_output" | awk 'NF {print $1}' | grep -E '^[A-Za-z0-9-]+$' || true
}

get_ready_tickets() {
    local tk_output
    tk_output=$(tk ready 2>&1)

    if [[ $? -ne 0 ]]; then
        error "Failed to run 'tk ready': $tk_output"
        return 1
    fi

    parse_tickets "$tk_output"
}
```

**Verification**:
- `parse_tickets` extracts "ptf-abc1" from "ptf-abc1 [open] - Title"
- Handles empty output gracefully
- Handles multiple tickets

**Rollback**: Revert parser functions

---

### Task 6: Command Builder
**Priority**: P0
**Effort**: 20 minutes
**Dependencies**: Task 5

**Description**: Build pi command with appropriate flags based on mode.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
build_command() {
    local ticket_id="$1"
    local mode="$2"

    case "$mode" in
        clarify)
            echo "pi \"/tk-implement ${ticket_id} --clarify\""
            ;;
        hands-free)
            echo "pi \"/tk-implement ${ticket_id} --hands-free\""
            ;;
        dispatch)
            echo "pi \"/tk-implement ${ticket_id} --dispatch\""
            ;;
        interactive)
            echo "pi \"/tk-implement ${ticket_id} --interactive\""
            ;;
        *)
            error "Unknown mode: $mode"
            return 1
            ;;
    esac
}
```

**Verification**:
- `build_command "ptf-abc1" "clarify"` returns `pi "/tk-implement ptf-abc1 --clarify"`
- All modes produce correct commands

**Rollback**: Revert command builder

---

### Task 7: State Directory Management
**Priority**: P1
**Effort**: 30 minutes
**Dependencies**: Task 6

**Description**: Initialize and manage state directory for observability with normalized schema.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)
- `.tk-loop-state/` (new directory, gitignored)

**State Schema (Normalized)**:
```
.tk-loop-state/
├── pid.lock           # Single PID value, plain text
├── current-ticket     # Currently processing ticket ID, plain text
├── loop.log           # Structured logs, JSONL format
├── processed.jsonl    # Success records, JSONL format
├── failed.jsonl       # Failure records, JSONL format
└── metrics.json       # Single JSON object with aggregated stats
```

**JSONL Record Formats**:
```json
// processed.jsonl - one record per line
{"ticket":"ptf-abc1","timestamp":"2026-03-04T12:34:56Z"}
{"ticket":"ptf-def2","timestamp":"2026-03-04T12:35:12Z"}

// failed.jsonl - one record per line
{"ticket":"ptf-ghi3","timestamp":"2026-03-04T12:36:01Z","error":"Exit code: 1"}

// metrics.json - single object, overwritten on each update
{
  "started_at": "2026-03-04T12:34:00Z",
  "mode": "clarify",
  "tickets_processed": 5,
  "tickets_failed": 1,
  "last_updated": "2026-03-04T12:40:00Z",
  "pid": 12345
}
```

**Implementation**:
```bash
init_state_dir() {
    mkdir -p "$STATE_DIR"

    # Create PID lock file
    local pid_file="$STATE_DIR/pid.lock"
    if [[ -f "$pid_file" ]]; then
        local existing_pid
        existing_pid=$(cat "$pid_file")
        if kill -0 "$existing_pid" 2>/dev/null; then
            error "Another tk-loop instance is running (PID: $existing_pid)"
            error "If this is a stale lock, delete: $pid_file"
            exit 1
        else
            log "Removing stale PID lock file"
            rm -f "$pid_file"
        fi
    fi

    echo $$ > "$pid_file"

    # Initialize state files (JSONL format for logs)
    : > "$STATE_DIR/processed.jsonl"
    : > "$STATE_DIR/failed.jsonl"
    : > "$STATE_DIR/loop.log"
    
    # Initialize metrics.json with starting state
    cat > "$STATE_DIR/metrics.json" <<EOF
{
  "started_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "mode": "$MODE",
  "tickets_processed": 0,
  "tickets_failed": 0,
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "pid": $$
}
EOF
    
    # Clear current ticket marker
    : > "$STATE_DIR/current-ticket"
}

update_metrics() {
    local processed_count=$(wc -l < "$STATE_DIR/processed.jsonl" | tr -d ' ')
    local failed_count=$(wc -l < "$STATE_DIR/failed.jsonl" | tr -d ' ')
    
    cat > "$STATE_DIR/metrics.json" <<EOF
{
  "started_at": "$(jq -r '.started_at' "$STATE_DIR/metrics.json" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "mode": "$MODE",
  "tickets_processed": $processed_count,
  "tickets_failed": $failed_count,
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "pid": $$
}
EOF
}

cleanup_state_dir() {
    rm -f "$STATE_DIR/pid.lock"
    : > "$STATE_DIR/current-ticket"
}
```

**Verification**:
- State directory created with correct structure
- PID lock prevents concurrent runs
- Stale lock files are cleaned up
- JSONL files have correct format (one JSON object per line)
- metrics.json is valid single JSON object

**Rollback**: Remove state directory management

---

### Task 8: Main Loop Implementation
**Priority**: P0
**Effort**: 45 minutes
**Dependencies**: Task 7

**Description**: Implement the main polling and execution loop (no retry logic per PRD).

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
record_success() {
    local ticket_id="$1"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"ticket\":\"$ticket_id\",\"timestamp\":\"$timestamp\"}" >> "$STATE_DIR/processed.jsonl"
    
    # Also log to loop.log
    log "TICKET_SUCCESS" "ticket=$ticket_id"
    
    # Update metrics
    update_metrics
}

record_failure() {
    local ticket_id="$1"
    local error_msg="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"ticket\":\"$ticket_id\",\"timestamp\":\"$timestamp\",\"error\":\"$error_msg\"}" >> "$STATE_DIR/failed.jsonl"
    
    # Also log to loop.log
    log "TICKET_FAILED" "ticket=$ticket_id error=\"$error_msg\""
    
    # Update metrics
    update_metrics
}

process_ticket() {
    local ticket_id="$1"
    local cmd
    cmd=$(build_command "$ticket_id" "$MODE")

    log "Processing ticket: $ticket_id (mode: $MODE)"
    echo "$ticket_id" > "$STATE_DIR/current-ticket"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would execute: $cmd"
        record_success "$ticket_id"
        : > "$STATE_DIR/current-ticket"
        return 0
    fi

    # Set recursion guard for nested invocation
    export PI_TK_INTERACTIVE_CHILD=1

    if eval "$cmd"; then
        record_success "$ticket_id"
        log "✓ Ticket $ticket_id completed successfully"
        : > "$STATE_DIR/current-ticket"
        return 0
    else
        local exit_code=$?
        record_failure "$ticket_id" "Exit code: $exit_code"
        error "✗ Ticket $ticket_id failed (exit code: $exit_code)"
        : > "$STATE_DIR/current-ticket"
        return 1
    fi
}

main_loop() {
    local iteration=0

    while true; do
        iteration=$((iteration + 1))

        if [[ "$VERBOSE" == "true" ]]; then
            log "Iteration $iteration: Checking for ready tickets..."
        fi

        local tickets
        tickets=$(get_ready_tickets)

        if [[ -z "$tickets" ]]; then
            log "No tickets remaining. Exiting."
            exit 0
        fi

        local ticket_count
        ticket_count=$(echo "$tickets" | wc -l | tr -d ' ')
        log "Found $ticket_count ready ticket(s)"

        local ticket
        for ticket in $tickets; do
            # Process ticket once - no retry per PRD (Out of Scope: "Failed tickets are logged but not automatically retried")
            process_ticket "$ticket" || true  # Continue on failure, don't retry
            
            # Brief pause between tickets
            sleep "$POLL_INTERVAL"
        done
    done
}
```

**Verification**:
- Loop exits when `tk ready` returns empty
- Processes tickets sequentially
- Records success/failure for each ticket
- Respects `--dry-run` flag
- **No retry logic** - matches PRD Out of Scope
- Continues to next ticket on failure

**Rollback**: Revert main loop implementation

---

### Task 9: Structured Logging
**Priority**: P1
**Effort**: 20 minutes
**Dependencies**: Task 8

**Description**: Implement JSONL structured logging to loop.log.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
log_structured() {
    local level="$1"
    local msg="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Console output
    echo "[$timestamp] [$level] $msg"
    
    # JSONL to log file
    echo "{\"timestamp\":\"$timestamp\",\"level\":\"$level\",\"message\":\"$msg\"}" >> "$STATE_DIR/loop.log"
}

log() { log_structured "INFO" "$*"; }
log_warn() { log_structured "WARN" "$*"; }
log_error() { log_structured "ERROR" "$*"; }
log_debug() { 
    [[ "$VERBOSE" == "true" ]] && log_structured "DEBUG" "$*"
}
```

**Verification**:
- Each log entry is valid JSON
- One JSON object per line (JSONL format)
- Console output is human-readable
- Log file contains structured data

**Rollback**: Revert logging implementation

---

### Task 10: Graceful Shutdown
**Priority**: P1
**Effort**: 20 minutes
**Dependencies**: Task 9

**Description**: Handle SIGINT/SIGTERM for graceful shutdown.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
cleanup() {
    log "Received shutdown signal. Cleaning up..."
    cleanup_state_dir
    log "Shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM
```

**Verification**:
- Ctrl+C triggers cleanup
- PID lock file removed on exit
- Graceful log message
- `kill <pid>` triggers cleanup

**Rollback**: Remove signal handlers

---

### Task 11: End-to-End Integration Test
**Priority**: P1
**Effort**: 1 hour
**Dependencies**: Task 10

**Description**: Create comprehensive end-to-end test suite covering all scenarios including full loop execution.

**Files**:
- `.tf/scripts/test-tk-loop.sh` (new)

**Implementation**:
```bash
#!/usr/bin/env bash
# End-to-end integration test suite for tk-loop.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TK_LOOP="$SCRIPT_DIR/tk-loop.sh"
TEST_DIR=$(mktemp -d)
STATE_DIR="$TEST_DIR/.tk-loop-state"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
setup() {
    export TK_LOOP_STATE_DIR="$STATE_DIR"
    export TK_LOOP_POLL_INTERVAL=0
    export PATH="$SCRIPT_DIR/test-mocks:$PATH"
    mkdir -p "$STATE_DIR"
}

teardown() {
    rm -rf "$TEST_DIR"
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++)) || true
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++)) || true
}

# Mock setup helpers
mock_tk_ready() {
    cat > "$SCRIPT_DIR/test-mocks/tk" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "ready" ]]; then
    cat "$TK_MOCK_READY_FILE" 2>/dev/null || echo ""
else
    echo "Mock tk: $*" >&2
    exit 1
fi
EOF
    chmod +x "$SCRIPT_DIR/test-mocks/tk"
}

mock_pi() {
    cat > "$SCRIPT_DIR/test-mocks/pi" <<'EOF'
#!/usr/bin/env bash
# Mock pi that succeeds or fails based on ticket ID
if [[ "$*" == *"FAIL"* ]]; then
    exit 1
else
    exit 0
fi
EOF
    chmod +x "$SCRIPT_DIR/test-mocks/pi"
}

# Test: Empty queue exits cleanly
test_empty_queue() {
    echo "TEST: Empty queue - script exits with status 0"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    mock_tk_ready
    mock_pi
    
    if timeout 5 "$TK_LOOP" --dry-run --verbose; then
        pass "Empty queue exits with status 0"
    else
        fail "Empty queue should exit with status 0, got $?"
    fi
    
    teardown
}

# Test: Recursion guard prevents nested execution
test_recursion_guard() {
    echo "TEST: Recursion guard - prevents nested execution"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    mock_tk_ready
    
    if PI_TK_INTERACTIVE_CHILD=1 "$TK_LOOP" --dry-run 2>&1 | grep -q "Nested tk-loop detected"; then
        pass "Recursion guard blocks nested execution"
    else
        fail "Recursion guard should block nested execution"
    fi
    
    teardown
}

# Test: Single ticket processed
test_single_ticket() {
    echo "TEST: Single ticket - processed and exits"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/single.txt"
    echo "ptf-test1 Test ticket" > "$TK_MOCK_READY_FILE"
    mock_tk_ready
    mock_pi
    
    if timeout 10 "$TK_LOOP" --dry-run; then
        if grep -q "ptf-test1" "$STATE_DIR/processed.jsonl"; then
            pass "Single ticket processed and recorded"
        else
            fail "Single ticket should be recorded in processed.jsonl"
        fi
    else
        fail "Single ticket test should exit with status 0"
    fi
    
    teardown
}

# Test: Multiple tickets processed sequentially
test_multiple_tickets() {
    echo "TEST: Multiple tickets - processed sequentially"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/multi.txt"
    cat > "$TK_MOCK_READY_FILE" <<EOF
ptf-test1 First ticket
ptf-test2 Second ticket
ptf-test3 Third ticket
EOF
    mock_tk_ready
    mock_pi
    
    if timeout 15 "$TK_LOOP" --dry-run; then
        local count
        count=$(wc -l < "$STATE_DIR/processed.jsonl" | tr -d ' ')
        if [[ "$count" -eq 3 ]]; then
            pass "All 3 tickets processed"
        else
            fail "Expected 3 tickets in processed.jsonl, found $count"
        fi
    else
        fail "Multiple tickets test should exit with status 0"
    fi
    
    teardown
}

# Test: Failed ticket continues to next
test_failure_continues() {
    echo "TEST: Failure handling - continues to next ticket"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/fail.txt"
    cat > "$TK_MOCK_READY_FILE" <<EOF
ptf-FAIL Will fail
ptf-pass Will pass
EOF
    mock_tk_ready
    mock_pi
    
    # Run without dry-run to trigger mock failure behavior
    timeout 15 "$TK_LOOP" --clarify 2>&1 || true
    
    # Check that failed ticket is recorded
    if grep -q "ptf-FAIL" "$STATE_DIR/failed.jsonl"; then
        pass "Failed ticket recorded in failed.jsonl"
    else
        fail "Failed ticket should be recorded"
    fi
    
    teardown
}

# Test: Mode flags are mutually exclusive
test_mode_mutex() {
    echo "TEST: Mode mutex - flags are mutually exclusive"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    mock_tk_ready
    
    if "$TK_LOOP" --clarify --hands-free 2>&1 | grep -q "Cannot combine"; then
        pass "Mode flags are mutually exclusive"
    else
        fail "Should reject combined mode flags"
    fi
    
    teardown
}

# Test: State file schema is correct
test_state_schema() {
    echo "TEST: State schema - JSONL format for logs"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/single.txt"
    echo "ptf-test1 Test ticket" > "$TK_MOCK_READY_FILE"
    mock_tk_ready
    mock_pi
    
    timeout 10 "$TK_LOOP" --dry-run
    
    # Check processed.jsonl format
    if jq -e '.ticket' "$STATE_DIR/processed.jsonl" >/dev/null 2>&1; then
        pass "processed.jsonl contains valid JSON with ticket field"
    else
        fail "processed.jsonl should contain valid JSON with ticket field"
    fi
    
    # Check metrics.json is single object
    if jq -e '.tickets_processed' "$STATE_DIR/metrics.json" >/dev/null 2>&1; then
        pass "metrics.json contains valid JSON with tickets_processed field"
    else
        fail "metrics.json should contain valid JSON with tickets_processed field"
    fi
    
    teardown
}

# Test: PID lock prevents concurrent runs
test_pid_lock() {
    echo "TEST: PID lock - prevents concurrent execution"
    setup
    
    mkdir -p "$STATE_DIR"
    echo "99999" > "$STATE_DIR/pid.lock"
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    mock_tk_ready
    
    if "$TK_LOOP" --dry-run 2>&1 | grep -q "Another tk-loop instance is running"; then
        pass "PID lock prevents concurrent execution"
    else
        fail "Should detect existing PID lock"
    fi
    
    teardown
}

# Test: Signal handling for graceful shutdown
test_signal_handling() {
    echo "TEST: Signal handling - graceful shutdown on SIGINT"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    mock_tk_ready
    mock_pi
    
    # Start loop in background
    "$TK_LOOP" --verbose &
    local pid=$!
    
    # Give it time to start
    sleep 0.5
    
    # Send SIGINT
    kill -INT $pid 2>/dev/null || true
    
    # Wait for process to exit
    wait $pid 2>/dev/null || true
    
    # Check cleanup happened
    if [[ ! -f "$STATE_DIR/pid.lock" ]]; then
        pass "PID lock cleaned up on SIGINT"
    else
        fail "PID lock should be removed on graceful shutdown"
    fi
    
    teardown
}

# Main test runner
main() {
    echo "═══════════════════════════════════════════════════"
    echo "  tk-loop.sh End-to-End Integration Tests"
    echo "═══════════════════════════════════════════════════"
    echo ""
    
    # Create mocks directory
    mkdir -p "$SCRIPT_DIR/test-mocks"
    
    # Run all tests
    test_empty_queue
    test_recursion_guard
    test_single_ticket
    test_multiple_tickets
    test_failure_continues
    test_mode_mutex
    test_state_schema
    test_pid_lock
    test_signal_handling
    
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo -e "  Results: ${GREEN}$TESTS_PASSED passed${NC}, ${RED}$TESTS_FAILED failed${NC}"
    echo "═══════════════════════════════════════════════════"
    
    # Cleanup mocks
    rm -rf "$SCRIPT_DIR/test-mocks"
    
    exit $TESTS_FAILED
}

main "$@"
```

**Verification**:
- All 9 test scenarios pass
- Tests can run independently
- Tests cover acceptance criteria from PRD
- Mock infrastructure allows controlled testing

**Rollback**: Delete test suite

---

### Task 11.5: Mock Infrastructure Contract
**Priority**: P1
**Effort**: 30 minutes
**Dependencies**: Task 11

**Description**: Specify and implement the mock infrastructure contract for testing.

**Files**:
- `.tf/scripts/test-mocks/` (new directory)
- `.tf/scripts/test-mocks/MOCK_CONTRACT.md` (new)

**Mock Contract Document**:
```markdown
# Mock Infrastructure Contract

## Overview
Mock implementations of `tk` and `pi` CLIs for isolated testing of tk-loop.sh.

## Location
`.tf/scripts/test-mocks/`

## Mock: tk

### Interface
```bash
tk ready    # Returns list of ready tickets
tk show     # (optional) Show ticket details
tk close    # (optional) Close a ticket
```

### Behavior Contract
1. `tk ready` reads ticket list from `$TK_MOCK_READY_FILE` environment variable
2. Returns empty string if file doesn't exist or is empty
3. Each line format: `<TICKET-ID> <description>`
4. Exit code 0 on success

### Example
```bash
export TK_MOCK_READY_FILE="/tmp/tickets.txt"
echo "ptf-abc1 Test ticket" > "$TK_MOCK_READY_FILE"
tk ready  # Outputs: "ptf-abc1 Test ticket"
```

## Mock: pi

### Interface
```bash
pi "/tk-implement <TICKET-ID> --<MODE>"
```

### Behavior Contract
1. Parses ticket ID from command string
2. Success/failure determined by ticket ID pattern:
   - IDs containing "FAIL" (case insensitive) → exit 1
   - All other IDs → exit 0
3. Respects `--clarify`, `--hands-free`, `--dispatch`, `--interactive` flags
4. Outputs command received to stderr in verbose mode

### Example
```bash
pi "/tk-implement ptf-abc1 --clarify"   # Exit 0
pi "/tk-implement ptf-FAIL --dispatch" # Exit 1
```

## State Assertions

### Pre-conditions
- `$TK_LOOP_STATE_DIR` is set and directory exists
- `$TK_MOCK_READY_FILE` points to valid ticket list (or empty)

### Post-conditions
- On success: ticket appears in `$STATE_DIR/processed.jsonl`
- On failure: ticket appears in `$STATE_DIR/failed.jsonl`
- Metrics updated in `$STATE_DIR/metrics.json`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TK_MOCK_READY_FILE` | Yes | Path to file containing mock ticket list |
| `TK_LOOP_STATE_DIR` | Yes | Path to state directory for assertions |
| `TK_MOCK_VERBOSE` | No | Enable verbose mock output |
```

**Mock Implementation**:
```bash
#!/usr/bin/env bash
# .tf/scripts/test-mocks/tk
# Mock tk CLI for testing

case "$1" in
    ready)
        if [[ -n "${TK_MOCK_READY_FILE:-}" && -f "$TK_MOCK_READY_FILE" ]]; then
            cat "$TK_MOCK_READY_FILE"
        fi
        exit 0
        ;;
    show|close|blocked|complete)
        echo "Mock tk: $1 not fully implemented" >&2
        exit 0
        ;;
    *)
        echo "Mock tk: Unknown command: $1" >&2
        exit 1
        ;;
esac
```

```bash
#!/usr/bin/env bash
# .tf/scripts/test-mocks/pi
# Mock pi CLI for testing

# Extract ticket ID from command
# Format: pi "/tk-implement <ID> --<MODE>"
cmd="$*"

if [[ "$cmd" =~ /tk-implement[[:space:]]+([A-Za-z0-9-]+) ]]; then
    ticket_id="${BASH_REMATCH[1]}"
    
    # Check for failure pattern
    if [[ "${ticket_id^^}" == *"FAIL"* ]]; then
        [[ "${TK_MOCK_VERBOSE:-}" == "1" ]] && echo "Mock pi: Failing ticket $ticket_id" >&2
        exit 1
    fi
    
    [[ "${TK_MOCK_VERBOSE:-}" == "1" ]] && echo "Mock pi: Succeeding ticket $ticket_id" >&2
    exit 0
else
    echo "Mock pi: Could not parse ticket ID from: $cmd" >&2
    exit 1
fi
```

**Verification**:
- Mock contract documented
- Mock implementations follow contract
- Tests use mocks successfully

**Rollback**: Delete mock infrastructure

---

### Task 12: Documentation
**Priority**: P2
**Effort**: 30 minutes
**Dependencies**: Task 11.5

**Description**: Create README with usage examples and troubleshooting.

**Files**:
- `.tf/scripts/README.md` (new)

**Content**:
```markdown
# tk-loop - External Ralph Wiggum Loop

Continuously process tk tickets via `pi /tk-implement` with configurable execution modes.

## Installation

```bash
# Make executable
chmod +x .tf/scripts/tk-loop.sh

# Optional: Add to PATH
ln -s $(pwd)/.tf/scripts/tk-loop.sh ~/.local/bin/tk-loop
```

## Usage

### Basic Usage
```bash
# Process all ready tickets with clarify TUI (default)
.tf/scripts/tk-loop.sh --clarify

# Hands-free mode (agent-monitored, non-blocking)
.tf/scripts/tk-loop.sh --hands-free

# Dispatch mode (fire-and-forget background)
.tf/scripts/tk-loop.sh --dispatch

# Interactive mode (supervised blocking)
.tf/scripts/tk-loop.sh --interactive
```

### Dry Run
```bash
# See what would be done without executing
.tf/scripts/tk-loop.sh --dry-run --verbose
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TK_LOOP_POLL_INTERVAL` | `5` | Seconds between ticket polls |
| `TK_LOOP_STATE_DIR` | `.tk-loop-state` | State directory path |

### State Directory

The loop maintains state in `.tk-loop-state/`:

- `pid.lock` - PID of running loop (prevents concurrent runs)
- `current-ticket` - Currently processing ticket ID
- `processed.jsonl` - Successfully processed tickets (JSONL format)
- `failed.jsonl` - Failed tickets with error info (JSONL format)
- `loop.log` - Structured execution log (JSONL format)
- `metrics.json` - Aggregated statistics (single JSON object)

## Troubleshooting

### "Another tk-loop instance is running"
If the script exits with this error but no loop is running:
```bash
rm -f .tk-loop-state/pid.lock
```

### "Nested tk-loop detected"
You cannot run tk-loop from within a ticket being processed by tk-loop.
This prevents infinite recursion.

### Failed tickets
Failed tickets are recorded in `.tk-loop-state/failed.jsonl`.
The loop continues processing remaining tickets.

To retry failed tickets (future enhancement):
```bash
# Extract failed ticket IDs and re-queue
cat .tk-loop-state/failed.jsonl | jq -r '.ticket'
```

### Debugging
```bash
# Run with verbose logging
.tf/scripts/tk-loop.sh --verbose --clarify

# View structured logs
cat .tk-loop-state/loop.log | jq .

# View metrics
cat .tk-loop-state/metrics.json | jq .
```

## Testing

```bash
# Run integration tests
.tf/scripts/test-tk-loop.sh
```

## Integration with tk Workflow

The loop integrates with the standard tk workflow:

1. Create tickets with `tk create` or ticket files
2. Run `tk-loop.sh --clarify` to process all ready tickets
3. Each ticket opens in clarify TUI for review
4. Loop exits when no tickets remain
5. Check `.tk-loop-state/failed.jsonl` for any failures
```

**Verification**:
- README covers all use cases
- Examples are copy-pasteable
- Troubleshooting section helpful
- State directory format documented

**Rollback**: Delete README

---

## Verification Checklist

### Functional Requirements
- [x] Script exits when no tickets remain
- [x] Processes all tickets sequentially
- [x] Supports all 4 execution modes
- [x] Recursion guard prevents nested loops
- [x] Records success/failure for each ticket
- [x] Respects polling interval
- [x] Handles individual ticket failures gracefully (continues, no retry)

### Non-Functional Requirements
- [x] No external dependencies beyond bash, tk, pi
- [x] Graceful shutdown on SIGINT/SIGTERM
- [x] Structured logging (JSONL format)
- [x] State directory for observability
- [x] PID lock prevents concurrent runs
- [x] Consistent state file schema (JSONL for logs, single JSON for metrics)

### Edge Cases
- [x] Empty queue handled correctly
- [x] Single ticket processed correctly
- [x] Multiple tickets processed in order
- [x] Failed ticket doesn't block queue (no retry)
- [x] Stale PID lock cleaned up
- [x] Invalid flags show error message
- [x] Mode flags are mutually exclusive

### Documentation
- [x] Implementation plan complete
- [x] Mock infrastructure contract specified
- [x] README with usage and troubleshooting
- [x] Test suite with end-to-end coverage

---

## Rollback Strategy

If issues arise:
1. **Task-level**: Revert individual task commits
2. **Component-level**: Remove state directory, restore previous script version
3. **Full rollback**: 
   ```bash
   rm -f .tf/scripts/tk-loop.sh
   rm -rf .tf/scripts/test-*.sh .tf/scripts/test-mocks/
   rm -rf .tk-loop-state/
   ```

No database migrations or external system changes, making rollback straightforward.

---

## Deployment Notes

1. **Prerequisites**: Ensure `tk` and `pi` are installed and in PATH
2. **Installation**: Copy `.tf/scripts/tk-loop.sh` to project or make globally available
3. **Permissions**: Ensure script is executable (`chmod +x .tf/scripts/tk-loop.sh`)
4. **Git ignore**: Add `.tk-loop-state/` to `.gitignore`
5. **First run**: Test with `--dry-run` to verify configuration

---

## Success Metrics

- ✅ All acceptance criteria from PRD met
- ✅ All tests pass (9 end-to-end scenarios)
- ✅ Script handles all edge cases
- ✅ No regressions in existing tk/pi workflows
- ✅ Documentation complete and accurate
- ✅ Can process 10+ tickets without intervention
- ✅ Retry policy aligned with PRD (no automatic retry)
- ✅ Mock infrastructure contract documented
- ✅ State file schemas normalized (JSONL for logs, JSON for metrics)
