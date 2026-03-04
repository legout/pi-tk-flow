# Implementation Plan: External Ralph Wiggum Loop

**Status**: Draft
**Created**: 2026-03-04
**PRD**: 01-prd.md
**Spec**: 02-spec.md
**Design**: 00-design.md

---

## Overview

Implement an external bash script that continuously processes tickets from the tk queue using `tk ready` and `pi "/tk-implement <ID>"` with configurable execution modes.

**Total Effort**: ~4-6 hours
**Implementation Strategy**: Vertical slices, test-driven, incremental delivery

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
    TK_LOOP_MAX_RETRIES     Max retry attempts per ticket (default: 3)
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
MAX_RETRIES="${TK_LOOP_MAX_RETRIES:-3}"
STATE_DIR="${TK_LOOP_STATE_DIR:-.tk-loop-state}"

parse_flags() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clarify) MODE="clarify" ;;
            --hands-free) MODE="hands-free" ;;
            --dispatch) MODE="dispatch" ;;
            --interactive) MODE="interactive" ;;
            --dry-run) DRY_RUN=true ;;
            --verbose) VERBOSE=true ;;
            --help) show_help; exit 0 ;;
            *) error "Unknown flag: $1"; exit 1 ;;
        esac
        shift
    done

    if [[ "$VERBOSE" == "true" ]]; then
        log "Mode: $MODE"
        log "Poll interval: ${POLL_INTERVAL}s"
        log "Max retries: $MAX_RETRIES"
    fi
}
```

**Verification**:
- `./tk-loop.sh --clarify` sets MODE="clarify"
- `./tk-loop.sh --dispatch --verbose` logs mode and settings
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
        error "This prevents infinite recursion loops"
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
    # Format: "ptf-abc1 [status] - Title"
    echo "$tk_output" | grep -oE '\bptf-[a-z0-9]{4}\b' | sort -u
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
**Effort**: 20 minutes
**Dependencies**: Task 6

**Description**: Initialize and manage state directory for observability.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)
- `.tk-loop-state/` (new directory, gitignored)

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
            exit 1
        else
            log "Removing stale PID lock file"
            rm -f "$pid_file"
        fi
    fi

    echo $$ > "$pid_file"

    # Initialize log files
    touch "$STATE_DIR/processed.jsonl"
    touch "$STATE_DIR/failed.jsonl"
}

cleanup_state_dir() {
    rm -f "$STATE_DIR/pid.lock"
}
```

**Verification**:
- State directory created with correct structure
- PID lock prevents concurrent runs
- Stale lock files are cleaned up

**Rollback**: Remove state directory management

---

### Task 8: Main Loop Implementation
**Priority**: P0
**Effort**: 45 minutes
**Dependencies**: Task 7

**Description**: Implement the main polling and execution loop.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
record_success() {
    local ticket_id="$1"
    echo "{\"ticket\":\"$ticket_id\",\"status\":\"success\",\"timestamp\":\"$(date -Iseconds)\"}" \
        >> "$STATE_DIR/processed.jsonl"
}

record_failure() {
    local ticket_id="$1"
    local error_msg="$2"
    echo "{\"ticket\":\"$ticket_id\",\"status\":\"failed\",\"error\":\"$error_msg\",\"timestamp\":\"$(date -Iseconds)\"}" \
        >> "$STATE_DIR/failed.jsonl"
}

process_ticket() {
    local ticket_id="$1"
    local cmd
    cmd=$(build_command "$ticket_id" "$MODE")

    log "Processing ticket: $ticket_id (mode: $MODE)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would execute: $cmd"
        return 0
    fi

    # Set recursion guard for nested invocation
    export PI_TK_INTERACTIVE_CHILD=1

    if eval "$cmd"; then
        record_success "$ticket_id"
        log "✓ Ticket $ticket_id completed successfully"
        return 0
    else
        local exit_code=$?
        record_failure "$ticket_id" "Exit code: $exit_code"
        error "✗ Ticket $ticket_id failed (exit code: $exit_code)"
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
            process_ticket "$ticket" || true  # Continue on failure
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

**Rollback**: Revert main loop implementation

---

### Task 9: Error Handling & Retry Logic
**Priority**: P1
**Effort**: 30 minutes
**Dependencies**: Task 8

**Description**: Add exponential backoff retry logic for failed tickets.

**Files**:
- `.tf/scripts/tk-loop.sh` (modify)

**Implementation**:
```bash
get_backoff_duration() {
    local attempt="$1"
    case "$attempt" in
        1) echo "5" ;;
        2) echo "10" ;;
        3) echo "20" ;;
        *) echo "0" ;;  # No more retries
    esac
}

process_ticket_with_retry() {
    local ticket_id="$1"
    local attempt=1

    while [[ $attempt -le $MAX_RETRIES ]]; do
        if process_ticket "$ticket_id"; then
            return 0
        fi

        if [[ $attempt -lt $MAX_RETRIES ]]; then
            local backoff
            backoff=$(get_backoff_duration "$attempt")
            log "Retry $attempt/$MAX_RETRIES for $ticket_id in ${backoff}s..."
            sleep "$backoff"
        fi

        attempt=$((attempt + 1))
    done

    error "Max retries ($MAX_RETRIES) exceeded for ticket $ticket_id"
    return 1
}
```

**Verification**:
- Failed tickets retry with exponential backoff
- Max retries respected
- Backoff timing correct (5s, 10s, 20s)

**Rollback**: Remove retry logic

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

trap cleanup SIGINT SIGTERM
```

**Verification**:
- Ctrl+C triggers cleanup
- PID lock file removed on exit
- Graceful log message

**Rollback**: Remove signal handlers

---

### Task 11: Testing Suite
**Priority**: P1
**Effort**: 1 hour
**Dependencies**: Task 10

**Description**: Create comprehensive test suite covering all scenarios.

**Files**:
- `.tf/scripts/test-tk-loop.sh` (new)
- `.tf/scripts/test-fixtures/` (new directory)

**Implementation**:
```bash
#!/usr/bin/env bash
# Test suite for tk-loop.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TK_LOOP="$SCRIPT_DIR/tk-loop.sh"

# Test fixtures
test_empty_queue() {
    echo "TEST: Empty queue"
    # Mock tk ready to return empty
    # Verify script exits with status 0
}

test_single_ticket() {
    echo "TEST: Single ticket"
    # Mock tk ready to return one ticket
    # Verify ticket processed and script exits
}

test_multiple_tickets() {
    echo "TEST: Multiple tickets"
    # Mock tk ready to return 3 tickets
    # Verify all processed in order
}

test_recursion_guard() {
    echo "TEST: Recursion guard"
    PI_TK_INTERACTIVE_CHILD=1 "$TK_LOOP" --dry-run
    # Verify exit with error
}

test_mode_selection() {
    echo "TEST: Mode selection"
    # Test each mode flag
}

# Run tests
test_empty_queue
test_single_ticket
test_multiple_tickets
test_recursion_guard
test_mode_selection
```

**Verification**:
- All tests pass
- Coverage includes all acceptance criteria
- Tests can run independently

**Rollback**: Delete test suite

---

### Task 12: Documentation
**Priority**: P2
**Effort**: 30 minutes
**Dependencies**: Task 11

**Description**: Create README with usage examples and troubleshooting.

**Files**:
- `.tf/scripts/README.md` (new)

**Content**:
- Installation instructions
- Usage examples for each mode
- Environment variable reference
- Troubleshooting guide
- State directory explanation
- Integration with tk workflow

**Verification**:
- README covers all use cases
- Examples are copy-pasteable
- Troubleshooting section helpful

**Rollback**: Delete README

---

## Verification Checklist

### Functional Requirements
- [ ] Script exits when no tickets remain
- [ ] Processes all tickets sequentially
- [ ] Supports all 4 execution modes
- [ ] Recursion guard prevents nested loops
- [ ] Records success/failure for each ticket
- [ ] Respects polling interval
- [ ] Handles individual ticket failures

### Non-Functional Requirements
- [ ] No external dependencies beyond bash, tk, pi
- [ ] Graceful shutdown on SIGINT/SIGTERM
- [ ] Structured logging (JSONL format)
- [ ] State directory for observability
- [ ] PID lock prevents concurrent runs

### Edge Cases
- [ ] Empty queue handled correctly
- [ ] Single ticket processed correctly
- [ ] Multiple tickets processed in order
- [ ] Failed ticket doesn't block queue
- [ ] Stale PID lock cleaned up
- [ ] Invalid flags show error message

---

## Rollback Strategy

If issues arise:
1. **Task-level**: Revert individual task commits
2. **Component-level**: Remove state directory, restore previous script version
3. **Full rollback**: Delete `.tf/scripts/tk-loop.sh`, remove `.tk-loop-state/`

No database migrations or external system changes, making rollback straightforward.

---

## Deployment Notes

1. **Prerequisites**: Ensure `tk` and `pi` are installed and in PATH
2. **Installation**: Copy `.tf/scripts/tk-loop.sh` to project or make globally available
3. **Permissions**: Ensure script is executable (`chmod +x tk-loop.sh`)
4. **Git ignore**: Add `.tk-loop-state/` to `.gitignore`
5. **First run**: Test with `--dry-run` to verify configuration

---

## Success Metrics

- ✅ All acceptance criteria from PRD met
- ✅ All tests pass
- ✅ Script handles all edge cases
- ✅ No regressions in existing tk/pi workflows
- ✅ Documentation complete and accurate
- ✅ Can process 10+ tickets without intervention
