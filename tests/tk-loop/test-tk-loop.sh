#!/usr/bin/env bash
# End-to-end integration test suite for tk-loop.sh
# Covers all acceptance criteria scenarios

set -euo pipefail

# =============================================================================
# Test Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOCKS_DIR="$SCRIPT_DIR/mocks"
TK_LOOP="${SCRIPT_DIR}/../../.tf/scripts/tk-loop.sh"
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
TESTS_TOTAL=9

# =============================================================================
# Cross-Platform Timeout Support
# =============================================================================

# Detect available timeout command
TIMEOUT_CMD=""
if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_CMD="timeout"
elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD="gtimeout"
fi

# Portable timeout function
# Usage: run_with_timeout <seconds> <command...>
run_with_timeout() {
    local seconds="$1"
    shift
    
    if [[ -n "$TIMEOUT_CMD" ]]; then
        "$TIMEOUT_CMD" "$seconds" "$@"
    else
        # Fallback: run without timeout (tests may hang if command loops forever)
        # At least check that timeout is needed and warn
        echo -e "${YELLOW}WARNING: No timeout command available (install GNU coreutils)${NC}" >&2
        "$@"
    fi
}

# =============================================================================
# Helper Functions
# =============================================================================

setup() {
    # Clear recursion guard env var to prevent false test failures
    unset PI_TK_INTERACTIVE_CHILD
    
    export TK_LOOP_STATE_DIR="$STATE_DIR"
    export TK_LOOP_POLL_INTERVAL=0
    export PATH="$MOCKS_DIR:$PATH"
    mkdir -p "$STATE_DIR"
    
    # Verify tk-loop.sh exists
    if [[ ! -f "$TK_LOOP" ]]; then
        echo -e "${RED}ERROR: tk-loop.sh not found at $TK_LOOP${NC}"
        echo "Make sure to run tests from the project root or tests/tk-loop/ directory"
        exit 1
    fi
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

# Check if jq is available for JSON validation
has_jq() {
    command -v jq >/dev/null 2>&1
}

# =============================================================================
# Test Scenarios (from Acceptance Criteria)
# =============================================================================

# -----------------------------------------------------------------------------
# Test 1: Empty queue - script exits with status 0
# -----------------------------------------------------------------------------
test_empty_queue() {
    echo "TEST 1/9: Empty queue - script exits with status 0"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    
    # Run with timeout to prevent hanging
    if run_with_timeout 10 "$TK_LOOP" --dry-run --verbose 2>/dev/null; then
        pass "Empty queue exits with status 0"
    else
        local exit_code=$?
        fail "Empty queue should exit with status 0, got $exit_code"
    fi
    
    teardown
}

# -----------------------------------------------------------------------------
# Test 2: Recursion guard - prevents nested execution
# -----------------------------------------------------------------------------
test_recursion_guard() {
    echo "TEST 2/9: Recursion guard - prevents nested execution"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    
    # Capture output and exit code separately (fix for pipefail issue)
    local output
    local exit_code
    output=$(PI_TK_INTERACTIVE_CHILD=1 "$TK_LOOP" --dry-run 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}
    
    if [[ $exit_code -ne 0 && "$output" == *"Nested tk-loop detected"* ]]; then
        pass "Recursion guard blocks nested execution"
    else
        fail "Recursion guard should block nested execution (exit=$exit_code, output contains nested msg: $(echo "$output" | grep -c "Nested"))"
    fi
    
    teardown
}

# -----------------------------------------------------------------------------
# Test 3: Single ticket - processed and exits
# -----------------------------------------------------------------------------
test_single_ticket() {
    echo "TEST 3/9: Single ticket - processed and exits"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/single.txt"
    echo "ptf-test1 Test ticket" > "$TK_MOCK_READY_FILE"
    
    if run_with_timeout 10 "$TK_LOOP" --dry-run 2>/dev/null; then
        if [[ -f "$STATE_DIR/processed.jsonl" ]] && grep -q "ptf-test1" "$STATE_DIR/processed.jsonl"; then
            pass "Single ticket processed and recorded"
        else
            fail "Single ticket should be recorded in processed.jsonl"
        fi
    else
        fail "Single ticket test should exit with status 0"
    fi
    
    teardown
}

# -----------------------------------------------------------------------------
# Test 4: Multiple tickets - processed sequentially
# -----------------------------------------------------------------------------
test_multiple_tickets() {
    echo "TEST 4/9: Multiple tickets - processed sequentially"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/multi.txt"
    cat > "$TK_MOCK_READY_FILE" <<EOF
ptf-test1 First ticket
ptf-test2 Second ticket
ptf-test3 Third ticket
EOF
    
    if run_with_timeout 15 "$TK_LOOP" --dry-run 2>/dev/null; then
        local count=0
        if [[ -f "$STATE_DIR/processed.jsonl" ]]; then
            count=$(wc -l < "$STATE_DIR/processed.jsonl" | tr -d ' ')
        fi
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

# -----------------------------------------------------------------------------
# Test 5: Failure handling - continues to next ticket
# -----------------------------------------------------------------------------
test_failure_continues() {
    echo "TEST 5/9: Failure handling - continues to next ticket"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/fail.txt"
    cat > "$TK_MOCK_READY_FILE" <<EOF
ptf-FAIL1 Will fail
ptf-pass1 Will pass
EOF
    
    # Run without dry-run to trigger mock failure behavior
    run_with_timeout 15 "$TK_LOOP" --clarify 2>/dev/null || true
    
    local passed=0 failed=0
    
    # Check that failed ticket is recorded
    if [[ -f "$STATE_DIR/failed.jsonl" ]] && grep -q "ptf-FAIL1" "$STATE_DIR/failed.jsonl"; then
        ((failed++)) || true
    fi
    
    # Check that passed ticket is recorded
    if [[ -f "$STATE_DIR/processed.jsonl" ]] && grep -q "ptf-pass1" "$STATE_DIR/processed.jsonl"; then
        ((passed++)) || true
    fi
    
    if [[ $failed -eq 1 && $passed -eq 1 ]]; then
        pass "Failed ticket recorded, next ticket processed"
    else
        fail "Expected 1 failed and 1 passed, got $failed failed and $passed passed"
    fi
    
    teardown
}

# -----------------------------------------------------------------------------
# Test 6: Mode mutex - flags are mutually exclusive
# -----------------------------------------------------------------------------
test_mode_mutex() {
    echo "TEST 6/9: Mode mutex - flags are mutually exclusive"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    
    # Capture output and exit code separately (fix for pipefail issue)
    local output
    local exit_code
    output=$("$TK_LOOP" --clarify --hands-free 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}
    
    if [[ $exit_code -ne 0 && "$output" == *"Cannot combine"* ]]; then
        pass "Mode flags are mutually exclusive"
    else
        fail "Should reject combined mode flags (exit=$exit_code)"
    fi
    
    teardown
}

# -----------------------------------------------------------------------------
# Test 7: State schema - JSONL format for logs
# -----------------------------------------------------------------------------
test_state_schema() {
    echo "TEST 7/9: State schema - JSONL format for logs"
    setup
    
    export TK_MOCK_READY_FILE="$TEST_DIR/single.txt"
    echo "ptf-test1 Test ticket" > "$TK_MOCK_READY_FILE"
    
    run_with_timeout 10 "$TK_LOOP" --dry-run 2>/dev/null || true
    
    local passed=0
    
    # Check processed.jsonl format (if jq available)
    if has_jq && [[ -f "$STATE_DIR/processed.jsonl" ]]; then
        if jq -e '.id' "$STATE_DIR/processed.jsonl" >/dev/null 2>&1; then
            ((passed++)) || true
        else
            echo "  Note: processed.jsonl missing 'id' field"
        fi
    else
        # Basic grep check if jq not available
        if [[ -f "$STATE_DIR/processed.jsonl" ]] && grep -q '"id"' "$STATE_DIR/processed.jsonl"; then
            ((passed++)) || true
        fi
    fi
    
    # Check metrics.json is valid single object
    if has_jq && [[ -f "$STATE_DIR/metrics.json" ]]; then
        if jq -e '.tickets_processed' "$STATE_DIR/metrics.json" >/dev/null 2>&1; then
            ((passed++)) || true
        else
            echo "  Note: metrics.json missing 'tickets_processed' field"
        fi
    else
        # Basic grep check if jq not available
        if [[ -f "$STATE_DIR/metrics.json" ]] && grep -q '"tickets_processed"' "$STATE_DIR/metrics.json"; then
            ((passed++)) || true
        fi
    fi
    
    if [[ $passed -eq 2 ]]; then
        pass "State files have correct schema"
    else
        fail "State schema validation incomplete (passed $passed/2 checks)"
    fi
    
    teardown
}

# -----------------------------------------------------------------------------
# Test 8: PID lock - prevents concurrent execution
# -----------------------------------------------------------------------------
test_pid_lock() {
    echo "TEST 8/9: PID lock - prevents concurrent execution"
    setup
    
    # Create a LIVE PID lock (not stale) using a background sleep process
    # This ensures the PID check actually detects a running process
    sleep 60 &
    local live_pid=$!
    
    mkdir -p "$STATE_DIR"
    echo "$live_pid" > "$STATE_DIR/loop.pid"
    
    export TK_MOCK_READY_FILE="$TEST_DIR/empty.txt"
    echo "" > "$TK_MOCK_READY_FILE"
    
    # Capture output and exit code separately
    local output
    local exit_code
    output=$("$TK_LOOP" --dry-run 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}
    
    # Clean up the background process
    kill "$live_pid" 2>/dev/null || true
    wait "$live_pid" 2>/dev/null || true
    
    if [[ $exit_code -ne 0 && "$output" == *"Another tk-loop instance is running"* ]]; then
        pass "PID lock prevents concurrent execution"
    else
        fail "Should detect existing PID lock (exit=$exit_code)"
    fi
    
    teardown
}

# -----------------------------------------------------------------------------
# Test 9: Signal handling - graceful shutdown on SIGINT
# -----------------------------------------------------------------------------
test_signal_handling() {
    echo "TEST 9/9: Signal handling - graceful shutdown on SIGINT"
    setup
    
    # Create a ticket to process so the loop stays alive long enough for signal
    export TK_MOCK_READY_FILE="$TEST_DIR/tickets.txt"
    echo "ptf-signal1 Signal test ticket" > "$TK_MOCK_READY_FILE"
    
    # Start loop in background
    "$TK_LOOP" --verbose 2>/dev/null &
    local pid=$!
    
    # Give it time to start and acquire the PID lock
    sleep 0.5
    
    # Verify process is running
    if ! kill -0 "$pid" 2>/dev/null; then
        fail "Loop process did not start or exited immediately"
        teardown
        return
    fi
    
    # Send SIGINT
    kill -INT $pid 2>/dev/null || true
    
    # Wait for process to exit (with timeout)
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ $waited -lt 10 ]]; do
        sleep 0.5
        ((waited++)) || true
    done
    
    # Check cleanup happened - PID file should be removed
    if [[ ! -f "$STATE_DIR/loop.pid" ]]; then
        pass "PID lock cleaned up on SIGINT"
    else
        fail "PID lock should be removed on graceful shutdown"
    fi
    
    teardown
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
    echo "═══════════════════════════════════════════════════"
    echo "  tk-loop.sh End-to-End Integration Tests"
    echo "  Testing acceptance criteria from ticket ptf-ucgi"
    echo "═══════════════════════════════════════════════════"
    echo ""
    
    # Check for timeout command availability
    if [[ -z "$TIMEOUT_CMD" ]]; then
        echo -e "${YELLOW}NOTE: No 'timeout' command found. Tests may hang if commands loop forever.${NC}"
        echo -e "${YELLOW}Install GNU coreutils for 'timeout' support: brew install coreutils${NC}"
        echo ""
    fi
    
    echo "Test scenarios:"
    echo "  1. Empty queue - script exits with status 0"
    echo "  2. Recursion guard - prevents nested execution"
    echo "  3. Single ticket - processed and exits"
    echo "  4. Multiple tickets - processed sequentially"
    echo "  5. Failure handling - continues to next ticket"
    echo "  6. Mode mutex - flags are mutually exclusive"
    echo "  7. State schema - JSONL format for logs"
    echo "  8. PID lock - prevents concurrent execution"
    echo "  9. Signal handling - graceful shutdown on SIGINT"
    echo ""
    
    # Verify mocks exist
    if [[ ! -f "$MOCKS_DIR/tk" || ! -f "$MOCKS_DIR/pi" ]]; then
        echo -e "${RED}ERROR: Mocks not found in $MOCKS_DIR${NC}"
        exit 1
    fi
    
    # Make sure mocks are executable
    chmod +x "$MOCKS_DIR/tk" "$MOCKS_DIR/pi"
    
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
    echo -e "  Results: ${GREEN}$TESTS_PASSED passed${NC}, ${RED}$TESTS_FAILED failed${NC} / $TESTS_TOTAL total"
    echo "═══════════════════════════════════════════════════"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}All acceptance criteria met!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed.${NC}"
        exit 1
    fi
}

main "$@"
