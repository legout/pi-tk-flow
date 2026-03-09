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

# Logging functions
log() { echo "[$(date -Iseconds)] $*"; }
error() { echo "ERROR: $*" >&2; }

# =============================================================================
# Task 2: Flag Parser with Mode Parsing and Mutual-Exclusion Validation
# =============================================================================

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
# Main Entry Point
# =============================================================================

main() {
    # Parse command-line flags first (handles --help/--version short-circuit)
    parse_flags "$@"

    log "Starting $SCRIPT_NAME v$VERSION"

    # Check recursion guard
    check_recursion_guard

    # Validate dependencies
    validate_dependencies

    log "Initialization complete (mode: $MODE)"
    log "Ready to process tickets"

    # Note: Tasks 5-12 would implement the main loop here
    # For now, this is a placeholder indicating successful initialization

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would start processing tickets in $MODE mode"
    else
        log "Ticket processing would begin here (Tasks 5-12 not yet implemented)"
    fi
}

main "$@"
