#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# tk-loop - External Ralph Wiggum Loop
# =============================================================================
# Continuously processes tickets from the tk queue using tk ready and
# pi "/tk-implement <ID>" with configurable execution modes.
#
# Usage: tk-loop [OPTIONS]
#
# Options:
#     --clarify       Run with clarify TUI (default)
#     --hands-free    Run in hands-free mode
#     --dispatch      Run in dispatch mode
#     --interactive   Run in interactive mode
#     --dry-run       Show what would be done without executing
#     --verbose       Enable verbose logging
#     --help          Show this help message
#     --version       Show version information
#
# Environment Variables:
#     TK_LOOP_POLL_INTERVAL   Seconds between polls (default: 5)
#     TK_LOOP_STATE_DIR       State directory (default: .tk-loop-state)
# =============================================================================

# =============================================================================
# Task 1: Bootstrap Script Structure
# =============================================================================

# Constants
SCRIPT_NAME="tk-loop"
VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
MODE="clarify"
DRY_RUN=false
VERBOSE=false
POLL_INTERVAL="${TK_LOOP_POLL_INTERVAL:-5}"
STATE_DIR="${TK_LOOP_STATE_DIR:-.tk-loop-state}"
START_TIME=""

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
    --version       Show version information

Environment Variables:
    TK_LOOP_POLL_INTERVAL   Seconds between polls (default: 5)
    TK_LOOP_STATE_DIR       State directory (default: .tk-loop-state)

Examples:
    $SCRIPT_NAME --clarify
    $SCRIPT_NAME --dispatch --verbose
    $SCRIPT_NAME --hands-free --dry-run
EOF
}

# =============================================================================
# Task 7: State Directory Management (S3)
# =============================================================================

# Get current ISO 8601 timestamp
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Get current Unix epoch seconds
get_epoch_seconds() {
    date +%s
}

# Calculate runtime in seconds
get_runtime_sec() {
    local now=$(get_epoch_seconds)
    echo $((now - START_TIME))
}

# Initialize state directory and required files
init_state_dir() {
    mkdir -p "$STATE_DIR"
    
    # Initialize PID lock file
    echo $$ > "$STATE_DIR/loop.pid"
    
    # Initialize current-ticket marker
    echo "" > "$STATE_DIR/current-ticket"
    
    # Initialize JSONL log files if they don't exist
    [ ! -f "$STATE_DIR/processed.jsonl" ] && touch "$STATE_DIR/processed.jsonl"
    [ ! -f "$STATE_DIR/failed.jsonl" ] && touch "$STATE_DIR/failed.jsonl"
    
    # Initialize loop.log if it doesn't exist
    [ ! -f "$STATE_DIR/loop.log" ] && touch "$STATE_DIR/loop.log"
    
    # Initialize metrics.json
    write_initial_metrics
}

# Check for existing PID lock and handle stale locks
check_pid_lock() {
    local pid_file="$STATE_DIR/loop.pid"
    
    if [[ -f "$pid_file" ]]; then
        local existing_pid=$(cat "$pid_file" 2>/dev/null || echo "")
        
        if [[ -n "$existing_pid" ]]; then
            # Check if the process is still running
            if kill -0 "$existing_pid" 2>/dev/null; then
                error "Another tk-loop instance is already running (PID: $existing_pid)"
                error "If this is incorrect, remove $pid_file manually"
                exit 1
            else
                # Stale lock file - remove it
                log "WARN" "Removing stale PID lock file (PID $existing_pid is not running)"
                rm -f "$pid_file"
            fi
        fi
    fi
}

# Write initial metrics.json
write_initial_metrics() {
    local timestamp=$(get_timestamp)
    cat > "$STATE_DIR/metrics.json" <<EOF
{
  "started_at": "$timestamp",
  "mode": "$MODE",
  "tickets_processed": 0,
  "tickets_failed": 0,
  "current_ticket": null,
  "pid": $$
}
EOF
}

# Update metrics.json with current state
update_metrics() {
    local processed="$1"
    local failed="$2"
    local current="${3:-null}"
    local timestamp=$(get_timestamp)
    local runtime_sec=$(get_runtime_sec)
    
    # Build current_ticket value
    local current_value
    if [[ -n "$current" && "$current" != "null" ]]; then
        current_value="\"$current\""
    else
        current_value="null"
    fi
    
    cat > "$STATE_DIR/metrics.json" <<EOF
{
  "started_at": "$(cat "$STATE_DIR/metrics.json" 2>/dev/null | grep -o '"started_at": *"[^"]*"' | cut -d'"' -f4 || echo "$timestamp")",
  "mode": "$MODE",
  "tickets_processed": $processed,
  "tickets_failed": $failed,
  "current_ticket": $current_value,
  "last_poll_at": "$timestamp",
  "total_runtime_sec": $runtime_sec,
  "pid": $$
}
EOF
}

# Escape string for JSON value context
json_escape() {
    local s="$1"
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\n'/\\n}
    s=${s//$'\r'/\\r}
    s=${s//$'\t'/\\t}
    printf '%s' "$s"
}

# Write structured log entry to loop.log
log_structured() {
    local level="$1"
    local msg="$2"
    shift 2
    local extra="$*"
    
    local timestamp=$(get_timestamp)
    local escaped_level
    local escaped_msg
    escaped_level=$(json_escape "$level")
    escaped_msg=$(json_escape "$msg")

    local entry="{\"ts\":\"$timestamp\",\"level\":\"$escaped_level\",\"msg\":\"$escaped_msg\""
    
    # Add extra fields if provided
    if [[ -n "$extra" ]]; then
        entry="$entry,$extra"
    fi
    
    entry="$entry}"
    
    # Append to loop.log
    echo "$entry" >> "$STATE_DIR/loop.log"
}

# Console logging with optional structured logging
log() {
    local level="INFO"
    local msg="$1"
    
    # Check if first arg is a level keyword
    case "$1" in
        INFO|WARN|ERROR|DEBUG)
            level="$1"
            msg="$2"
            ;;
    esac
    
    echo "[$(date -Iseconds)] [$level] $msg"
    
    # Also write to structured log if state dir is initialized
    if [[ -d "$STATE_DIR" ]]; then
        log_structured "$level" "$msg"
    fi
}

error() {
    echo "[$(date -Iseconds)] [ERROR] $*" >&2
    
    # Also write to structured log if state dir is initialized
    if [[ -d "$STATE_DIR" ]]; then
        log_structured "ERROR" "$*"
    fi
}

# =============================================================================
# Task 2: Flag Parser with Mode Parsing and Mutual-Exclusion Validation
# =============================================================================

parse_flags() {
    local mode_count=0

    while [[ $# -gt 0 ]]; do
        case $1 in
            --clarify)
                MODE="clarify"
                ((mode_count++))
                ;;
            --hands-free)
                MODE="hands-free"
                ((mode_count++))
                ;;
            --dispatch)
                MODE="dispatch"
                ((mode_count++))
                ;;
            --interactive)
                MODE="interactive"
                ((mode_count++))
                ;;
            --dry-run)
                DRY_RUN=true
                ;;
            --verbose)
                VERBOSE=true
                ;;
            --help)
                show_help
                exit 0
                ;;
            --version)
                echo "$SCRIPT_NAME v$VERSION"
                exit 0
                ;;
            *)
                error "Unknown flag: $1"
                echo "Use --help for usage information." >&2
                exit 1
                ;;
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
        log "Dry run: $DRY_RUN"
        log "Poll interval: ${POLL_INTERVAL}s"
        log "State directory: $STATE_DIR"
    fi
}

# =============================================================================
# Task 3: Recursion Guard
# =============================================================================

check_recursion_guard() {
    if [[ "${PI_TK_INTERACTIVE_CHILD:-}" == "1" ]]; then
        error "Nested tk-loop detected (PI_TK_INTERACTIVE_CHILD=1)"
        error "This prevents infinite recursion loops. Exiting."
        exit 1
    fi
}

# =============================================================================
# Task 4: Dependency Validation
# =============================================================================

validate_dependencies() {
    local missing=()

    if ! command -v tk >/dev/null 2>&1; then
        missing+=("tk")
    fi

    if ! command -v pi >/dev/null 2>&1; then
        missing+=("pi")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing required dependencies: ${missing[*]}"
        error "Please install missing tools and try again"
        exit 1
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        log "Dependencies OK: tk=$(command -v tk), pi=$(command -v pi)"
    fi
}

# =============================================================================
# Task 5: Ticket Parser Implementation
# =============================================================================

# Parse ticket IDs from tk ready output
# Extracts the first column (ticket ID) from each line
# Filters for alphanumeric ticket ID format (e.g., ptf-abc1)
parse_tickets() {
    local input="$1"

    # Return empty if no input
    if [[ -z "$input" ]]; then
        return 0
    fi

    # Extract first column and filter for valid ticket ID format
    echo "$input" | awk '{print $1}' | grep -E '^[a-z]+-[a-z0-9]+$' || true
}

# Get ready tickets from tk ready command
# Returns error code 1 on tk ready failure
get_ready_tickets() {
    local output

    if ! output=$(tk ready 2>&1); then
        error "Failed to execute 'tk ready': $output"
        return 1
    fi

    parse_tickets "$output"
}

# =============================================================================
# Task 6: Command Builder Implementation
# =============================================================================

# Build the pi command for a ticket with specified mode
# Usage: build_command <ticket_id> <mode>
# Returns error code 1 for unknown mode
build_command() {
    local ticket_id="$1"
    local mode="$2"

    case "$mode" in
        clarify)
            echo "pi \"/tk-implement $ticket_id --clarify\""
            ;;
        hands-free)
            echo "pi \"/tk-implement $ticket_id --hands-free\""
            ;;
        dispatch)
            echo "pi \"/tk-implement $ticket_id --dispatch\""
            ;;
        interactive)
            echo "pi \"/tk-implement $ticket_id --interactive\""
            ;;
        *)
            error "Unknown mode: $mode"
            return 1
            ;;
    esac
}

# =============================================================================
# Task 9: Structured Logging and Observability (S3)
# =============================================================================

# Track metrics counters
TICKETS_PROCESSED=0
TICKETS_FAILED=0

# Record successful ticket processing
# Appends to processed.jsonl and updates metrics.json
record_success() {
    local ticket_id="$1"
    local timestamp=$(get_timestamp)
    
    # Append JSONL record to processed.jsonl
    echo "{\"id\":\"$ticket_id\",\"ts\":\"$timestamp\"}" >> "$STATE_DIR/processed.jsonl"
    
    # Update counter
    ((TICKETS_PROCESSED++))
    
    # Update metrics
    update_metrics "$TICKETS_PROCESSED" "$TICKETS_FAILED" "null"
    
    # Log to console and loop.log
    log "INFO" "✓ Successfully processed ticket: $ticket_id"
}

# Record failed ticket processing
# Appends to failed.jsonl and updates metrics.json
record_failure() {
    local ticket_id="$1"
    local exit_code="$2"
    local timestamp=$(get_timestamp)
    
    # Append JSONL record to failed.jsonl
    echo "{\"id\":\"$ticket_id\",\"ts\":\"$timestamp\",\"error\":\"exit code $exit_code\"}" >> "$STATE_DIR/failed.jsonl"
    
    # Update counter
    ((TICKETS_FAILED++))
    
    # Update metrics
    update_metrics "$TICKETS_PROCESSED" "$TICKETS_FAILED" "null"
    
    # Log to console and loop.log
    log "ERROR" "✗ Failed to process ticket: $ticket_id (exit code: $exit_code)"
}

# =============================================================================
# Task 8: Main Loop Implementation
# =============================================================================

# Process a single ticket
# Sets PI_TK_INTERACTIVE_CHILD=1 for recursion guard
# Handles dry-run mode
# Returns exit code from command execution
process_ticket() {
    local ticket_id="$1"
    local command

    log "INFO" "Processing ticket: $ticket_id"
    
    # Update current-ticket marker
    echo "$ticket_id" > "$STATE_DIR/current-ticket"
    update_metrics "$TICKETS_PROCESSED" "$TICKETS_FAILED" "$ticket_id"

    # Build the command
    if ! command=$(build_command "$ticket_id" "$MODE"); then
        record_failure "$ticket_id" 1
        echo "" > "$STATE_DIR/current-ticket"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would execute: $command"
        record_success "$ticket_id"
        echo "" > "$STATE_DIR/current-ticket"
        return 0
    fi

    # Set recursion guard and execute command
    export PI_TK_INTERACTIVE_CHILD=1

    log "Executing: $command"
    # Capture exit code without triggering set -e
    local exit_code=0
    eval "$command" || exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        record_success "$ticket_id"
    else
        record_failure "$ticket_id" "$exit_code"
    fi
    
    # Clear current-ticket marker
    echo "" > "$STATE_DIR/current-ticket"

    # Clear recursion guard
    unset PI_TK_INTERACTIVE_CHILD

    return "$exit_code"
}

# =============================================================================
# Task 10: Graceful Shutdown with Cleanup (S4 partial - needed for S3)
# =============================================================================

# Cleanup function for graceful shutdown
cleanup() {
    log "INFO" "Received shutdown signal, cleaning up..."
    
    # Clear current ticket marker
    echo "" > "$STATE_DIR/current-ticket" 2>/dev/null || true
    
    # Remove PID lock
    rm -f "$STATE_DIR/loop.pid" 2>/dev/null || true
    
    # Write final metrics
    update_metrics "$TICKETS_PROCESSED" "$TICKETS_FAILED" "null" 2>/dev/null || true
    
    log "INFO" "Loop shutdown complete"
    exit 0
}

# Main processing loop
# Polls tk ready and processes tickets sequentially
# Exits cleanly when no tickets remain
# Sleeps POLL_INTERVAL seconds between tickets
main_loop() {
    log "INFO" "Starting main loop (mode: $MODE, interval: ${POLL_INTERVAL}s)"

    while true; do
        local tickets

        # Get ready tickets
        if ! tickets=$(get_ready_tickets); then
            log "WARN" "Failed to fetch ready tickets, will retry in ${POLL_INTERVAL}s"
            sleep "$POLL_INTERVAL"
            continue
        fi

        # Exit cleanly if no tickets
        if [[ -z "$tickets" ]]; then
            log "INFO" "No ready tickets found. Exiting."
            exit 0
        fi

        # Count and log tickets
        local ticket_count
        ticket_count=$(echo "$tickets" | wc -l | tr -d ' ')
        log "INFO" "Found $ticket_count ready ticket(s)"

        # Process each ticket sequentially
        while IFS= read -r ticket_id; do
            [[ -z "$ticket_id" ]] && continue

            process_ticket "$ticket_id" || true
            # Continue to next ticket even on failure (no retry per PRD)

            sleep "$POLL_INTERVAL"
        done <<< "$tickets"
    done
}

# =============================================================================
# Main Entry Point
# =============================================================================

main() {
    # Record start time for metrics
    START_TIME=$(get_epoch_seconds)
    
    # Parse command-line flags first (handles --help/--version short-circuit)
    parse_flags "$@"

    log "Starting $SCRIPT_NAME v$VERSION"

    # Check recursion guard
    check_recursion_guard

    # Validate dependencies
    validate_dependencies
    
    # Check for existing PID lock (prevent concurrent runs)
    check_pid_lock

    # Initialize state directory
    init_state_dir
    
    log "Initialization complete (mode: $MODE)"

    # Set up trap for graceful shutdown
    trap cleanup INT TERM

    # Start the main loop
    main_loop
}

main "$@"
