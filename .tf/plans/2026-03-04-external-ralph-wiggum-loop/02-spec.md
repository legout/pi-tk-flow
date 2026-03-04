# Technical Specification: External Ralph Wiggum Loop

**Status:** Draft  
**Created:** 2026-03-04  
**Ticket:** ptf-loop  
**Related:** `prompts/tk-implement.md`, `.tf/AGENTS.md`

---

## 1. Architecture

### 1.1 Overview

The External Ralph Wiggum Loop is a standalone bash script that continuously processes tickets from the tk queue. It operates outside pi's agent system, polling `tk ready` and dispatching implementation work via `pi "/tk-implement <ID> --clarify"`.

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Ralph Wiggum Loop                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐     ┌──────────────┐     ┌──────────────────┐   │
│   │ tk ready │────▶│  Parse IDs   │────▶│  For each ID:    │   │
│   │   (CLI)  │     │  from output │     │  pi "/tk-        │   │
│   └──────────┘     └──────────────┘     │  implement ID"   │   │
│        │                                 └────────┬─────────┘   │
│        │                                          │             │
│        ▼                                          ▼             │
│   ┌──────────────┐                      ┌──────────────────┐   │
│   │ Empty? Exit  │◀─────────────────────│ Re-check tk ready│   │
│   │ with success │                      │    after each    │   │
│   └──────────────┘                      └──────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **External to pi** | Pure bash script, no pi agent modifications |
| **Recursion-safe** | `PI_TK_INTERACTIVE_CHILD=1` guard on nested invocations |
| **Idempotent** | Can be stopped and restarted without data loss |
| **Observable** | Structured logging with timestamps and ticket IDs |
| **Fail-safe** | Individual ticket failures don't crash the loop |

### 1.3 Invocation Modes

```bash
# Mode 1: Clarify mode (interactive TUI for each ticket)
tk-loop --clarify

# Mode 2: Hands-free mode (agent-monitored, non-blocking)
tk-loop --hands-free

# Mode 3: Dispatch mode (fire-and-forget background)
tk-loop --dispatch

# Mode 4: Interactive mode (supervised, blocking)
tk-loop --interactive
```

---

## 2. Components

### 2.1 Core Script: `tk-loop.sh`

**Location:** `scripts/tk-loop.sh` (or project root)

**Responsibilities:**
- Parse command-line flags
- Initialize loop state
- Poll `tk ready` for ticket queue
- Dispatch implementation for each ticket
- Handle graceful shutdown

**Structure:**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Configuration
SCRIPT_NAME="tk-loop"
VERSION="1.0.0"
POLL_INTERVAL="${TK_LOOP_POLL_INTERVAL:-5}"  # seconds between checks
MAX_RETRIES="${TK_LOOP_MAX_RETRIES:-3}"

# State directory for observability and recovery
STATE_DIR="${TK_LOOP_STATE_DIR:-.tk-loop-state}"

# Flag defaults
MODE="clarify"  # clarify | hands-free | dispatch | interactive
DRY_RUN=false
VERBOSE=false

# Main entry point
main() {
    parse_flags "$@"
    validate_dependencies
    init_state_dir
    run_loop
}
```

### 2.2 Flag Parser

**Supported Flags:**

| Flag | Mode | Description |
|------|------|-------------|
| `--clarify` | clarify | Open chain clarification TUI (default) |
| `--hands-free` | hands-free | Agent-monitored overlay, non-blocking |
| `--dispatch` | dispatch | Background execution, notification on complete |
| `--interactive` | interactive | Supervised blocking overlay |
| `--dry-run` | - | Parse and log without executing |
| `--verbose` | - | Enable debug logging |
| `--help` | - | Show usage |
| `--version` | - | Show version |

**Validation Matrix:**

| Combination | Valid | Error |
|-------------|-------|-------|
| `--clarify` + `--hands-free` | ❌ | Cannot combine clarify with hands-free |
| `--clarify` + `--dispatch` | ❌ | Cannot combine clarify with dispatch |
| `--clarify` + `--interactive` | ❌ | Cannot combine clarify with interactive |
| `--hands-free` + `--dispatch` | ❌ | Cannot combine hands-free with dispatch |
| `--hands-free` + `--interactive` | ❌ | Cannot combine hands-free with interactive |
| `--dispatch` + `--interactive` | ❌ | Cannot combine dispatch with interactive |

### 2.3 Ticket Parser

**Input:** Output from `tk ready`

**Expected Format:**
```
TICKET-ID-1  Short description
TICKET-ID-2  Another description
...
```

**Parsing Logic:**

```bash
parse_ticket_ids() {
    local output="$1"
    # Extract first column (ticket ID)
    echo "$output" | awk 'NF {print $1}' | grep -E '^[A-Za-z0-9-]+$' || true
}
```

**Safety Considerations:**
- Validate ticket IDs match expected pattern (alphanumeric + hyphens)
- Reject malformed IDs with warning log
- Handle empty output gracefully

### 2.4 Command Builder

**Builds the nested pi command with recursion guard:**

```bash
build_pi_command() {
    local ticket_id="$1"
    local mode_flag=""
    
    case "$MODE" in
        clarify)    mode_flag="--clarify" ;;
        hands-free) mode_flag="--hands-free" ;;
        dispatch)   mode_flag="--dispatch" ;;
        interactive) mode_flag="--interactive" ;;
    esac
    
    # Recursion guard prevents nested loop invocations
    echo "PI_TK_INTERACTIVE_CHILD=1 pi \"/tk-implement ${ticket_id} ${mode_flag}\""
}
```

### 2.5 State Manager

**State Directory Structure:**

```
.tk-loop-state/
├── loop.pid           # PID of running loop (for signal handling)
├── current-ticket     # Currently processing ticket ID
├── processed.json     # Array of processed ticket IDs with timestamps
├── failed.json        # Array of failed ticket IDs with error info
├── loop.log           # Structured log file
└── metrics.json       # Observability metrics
```

**State Files:**

| File | Format | Purpose |
|------|--------|---------|
| `loop.pid` | `12345\n` | Process ID for external monitoring |
| `current-ticket` | `TICKET-ID\n` | Currently processing (empty if idle) |
| `processed.json` | `[{"id":"TICKET-ID","ts":"ISO8601"}]` | Audit trail of successes |
| `failed.json` | `[{"id":"TICKET-ID","ts":"ISO8601","error":"msg"}]` | Failure history |
| `loop.log` | Lines of JSON | Structured log for debugging |
| `metrics.json` | `{"processed":N,"failed":M,"runtime_sec":T}` | Summary stats |

---

## 3. Data Flow

### 3.1 Main Loop Flow

```
                    ┌─────────────────┐
                    │   Start Loop    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Check for      │
                    │  running loop   │
                    │  (PID lock)     │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
        ┌───────────┐              ┌───────────────┐
        │  Exit:    │              │   Write PID   │
        │  Already  │              │   to lock     │
        │  running  │              └───────┬───────┘
        └───────────┘                      │
                                           ▼
                                  ┌─────────────────┐
                                  │  Poll tk ready  │◀────────┐
                                  └────────┬────────┘         │
                                           │                  │
                              ┌────────────┴────────────┐     │
                              │                         │     │
                              ▼                         ▼     │
                      ┌─────────────┐          ┌─────────────┐│
                      │ Empty?      │          │ Parse IDs   ││
                      │ Exit 0      │          │ from output ││
                      └─────────────┘          └──────┬──────┘│
                                                       │       │
                                                       ▼       │
                                              ┌─────────────┐ │
                                              │ For each    │ │
                                              │ ticket ID:  │ │
                                              └──────┬──────┘ │
                                                     │        │
                    ┌────────────────────────────────┼────────┘
                    │                                │
                    ▼                                │
           ┌─────────────────┐                       │
           │ Write ticket to │                       │
           │ current-ticket  │                       │
           └────────┬────────┘                       │
                    │                                │
                    ▼                                │
           ┌─────────────────┐                       │
           │ Build pi command│                       │
           │ with recursion  │                       │
           │ guard           │                       │
           └────────┬────────┘                       │
                    │                                │
                    ▼                                │
           ┌─────────────────┐                       │
           │ Execute command │                       │
           │ (with retry)    │                       │
           └────────┬────────┘                       │
                    │                                │
        ┌───────────┴───────────┐                    │
        │                       │                    │
        ▼                       ▼                    │
┌─────────────┐         ┌─────────────┐             │
│ Success:    │         │ Failure:    │             │
│ Record in   │         │ Record in   │             │
│ processed   │         │ failed      │             │
└──────┬──────┘         └──────┬──────┘             │
       │                       │                    │
       └───────────┬───────────┘                    │
                   │                                │
                   ▼                                │
          ┌─────────────────┐                       │
          │ Clear           │                       │
          │ current-ticket  │                       │
          └────────┬────────┘                       │
                   │                                │
                   ▼                                │
          ┌─────────────────┐                       │
          │ Sleep           │───────────────────────┘
          │ POLL_INTERVAL   │
          └─────────────────┘
```

### 3.2 Command Execution Flow

```
┌────────────────────────────────────────────────────────────────┐
│                     Command Execution                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  build_pi_command(TICKET-ID)                                   │
│           │                                                    │
│           ▼                                                    │
│  PI_TK_INTERACTIVE_CHILD=1 pi "/tk-implement TICKET-ID --mode"│
│           │                                                    │
│           ▼                                                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              pi internal processing                      │  │
│  │                                                          │  │
│  │  1. Fast anchoring (scout + context-builder)            │  │
│  │  2. Interactive mode router (sees PI_TK_INTERACTIVE_CHILD)│ │
│  │  3. Path selection (A/B/C)                              │  │
│  │  4. Subagent chain execution                            │  │
│  │  5. tk-closer finalization                              │  │
│  │                                                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│           │                                                    │
│           ▼                                                    │
│  Exit code: 0 = success, non-zero = failure                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Error Handling

### 4.1 Error Categories

| Category | Example | Recovery Action |
|----------|---------|-----------------|
| **Transient** | Network timeout, tk CLI unavailable | Retry with backoff |
| **Ticket Error** | Invalid ticket ID, blocked ticket | Log warning, skip ticket |
| **Execution Error** | pi command fails, agent crashes | Record failure, continue loop |
| **Fatal** | No disk space, permission denied | Exit loop with error |

### 4.2 Retry Logic

```bash
execute_with_retry() {
    local cmd="$1"
    local max_retries="${MAX_RETRIES:-3}"
    local retry=0
    local backoff=5
    
    while [ $retry -lt $max_retries ]; do
        if eval "$cmd"; then
            return 0
        fi
        
        retry=$((retry + 1))
        log "WARN" "Command failed, attempt $retry/$max_retries"
        
        if [ $retry -lt $max_retries ]; then
            sleep $backoff
            backoff=$((backoff * 2))  # Exponential backoff
        fi
    done
    
    return 1
}
```

### 4.3 Signal Handling

```bash
cleanup() {
    log "INFO" "Received shutdown signal, cleaning up..."
    
    # Clear current ticket marker
    echo "" > "$STATE_DIR/current-ticket"
    
    # Remove PID lock
    rm -f "$STATE_DIR/loop.pid"
    
    # Write final metrics
    write_metrics
    
    exit 0
}

trap cleanup SIGINT SIGTERM
```

### 4.4 Failure Recording

```bash
record_failure() {
    local ticket_id="$1"
    local error_msg="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Append to failed.json
    local record="{\"id\":\"$ticket_id\",\"ts\":\"$timestamp\",\"error\":\"$error_msg\"}"
    
    if [ -f "$STATE_DIR/failed.json" ]; then
        # Append to existing array
        local existing=$(cat "$STATE_DIR/failed.json")
        echo "${existing%]},$record]" > "$STATE_DIR/failed.json"
    else
        echo "[$record]" > "$STATE_DIR/failed.json"
    fi
    
    log "ERROR" "Ticket $ticket_id failed: $error_msg"
}
```

---

## 5. Observability

### 5.1 Structured Logging

**Log Format (JSON Lines):**

```json
{"ts":"2026-03-04T12:34:56.789Z","level":"INFO","msg":"Loop started","mode":"clarify"}
{"ts":"2026-03-04T12:34:57.123Z","level":"INFO","msg":"Found 3 tickets","ids":["TICKET-1","TICKET-2","TICKET-3"]}
{"ts":"2026-03-04T12:34:57.456Z","level":"INFO","msg":"Processing ticket","id":"TICKET-1"}
{"ts":"2026-03-04T12:35:02.789Z","level":"INFO","msg":"Ticket completed","id":"TICKET-1","duration_sec":5.3}
{"ts":"2026-03-04T12:35:03.012Z","level":"WARN","msg":"Command failed, retrying","id":"TICKET-2","attempt":1}
```

**Log Levels:**

| Level | When to Use |
|-------|-------------|
| DEBUG | Detailed execution flow (with `--verbose`) |
| INFO | Normal operations (start, stop, ticket processed) |
| WARN | Recoverable errors (retry attempts, skipped tickets) |
| ERROR | Failures (ticket failed, command errors) |

### 5.2 Metrics

**File:** `$STATE_DIR/metrics.json`

```json
{
  "started_at": "2026-03-04T12:34:56.789Z",
  "mode": "clarify",
  "tickets_processed": 5,
  "tickets_failed": 1,
  "current_ticket": null,
  "total_runtime_sec": 342.5,
  "last_poll_at": "2026-03-04T12:40:39.289Z",
  "pid": 12345
}
```

### 5.3 Health Check

**External monitoring can check:**

```bash
# Check if loop is running
if [ -f "$STATE_DIR/loop.pid" ]; then
    pid=$(cat "$STATE_DIR/loop.pid")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Loop is running (PID: $pid)"
    else
        echo "Loop is NOT running (stale PID file)"
    fi
else
    echo "Loop is NOT running"
fi

# Check current status
cat "$STATE_DIR/metrics.json" | jq '.'
```

### 5.4 Console Output

**Standard Output Format:**

```
═══════════════════════════════════════════════════════════════
  tk-loop v1.0.0 started
  Mode: clarify
  State: .tk-loop-state/
  
  2026-03-04 12:34:57 INFO  Found 3 tickets to process
  2026-03-04 12:34:57 INFO  Processing: TICKET-1
  2026-03-04 12:35:02 INFO  Completed: TICKET-1 (5.3s)
  2026-03-04 12:35:02 INFO  Processing: TICKET-2
  ...
═══════════════════════════════════════════════════════════════
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Location:** `tests/test_tk_loop.sh`

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| Parse empty output | `""` | `[]` |
| Parse single ticket | `"TICKET-1 desc"` | `["TICKET-1"]` |
| Parse multiple tickets | Multi-line output | Array of IDs |
| Reject malformed ID | `"INVALID ID!"` | Filtered out |
| Flag validation | `--clarify --hands-free` | Error message |

### 6.2 Integration Tests

| Test Case | Setup | Expected Behavior |
|-----------|-------|-------------------|
| Empty queue | `tk ready` returns empty | Exit 0 immediately |
| Single ticket | One ticket in queue | Process once, exit |
| Multiple tickets | Three tickets in queue | Process all, exit |
| Ticket failure | pi returns non-zero | Log failure, continue |
| Interrupt handling | SIGINT during processing | Graceful cleanup |

### 6.3 Test Harness

```bash
#!/usr/bin/env bash
# tests/test_tk_loop.sh

setup() {
    export TK_LOOP_STATE_DIR=$(mktemp -d)
    export TK_LOOP_POLL_INTERVAL=0  # No sleep in tests
}

teardown() {
    rm -rf "$TK_LOOP_STATE_DIR"
}

test_empty_queue_exits() {
    # Mock tk ready to return empty
    export PATH="tests/mocks:$PATH"
    
    ./scripts/tk-loop.sh --clarify
    assertEquals 0 $?
}

test_processes_single_ticket() {
    # Mock tk ready to return one ticket
    echo "TICKET-1 Test ticket" > "$TK_LOOP_STATE_DIR/tk_ready_mock"
    
    ./scripts/tk-loop.sh --dry-run --clarify
    assertContains "$(cat $TK_LOOP_STATE_DIR/processed.json)" "TICKET-1"
}
```

### 6.4 Mock Infrastructure

**Mock tk CLI:**

```bash
#!/usr/bin/env bash
# tests/mocks/tk

case "$1" in
    ready)
        cat "$TK_LOOP_STATE_DIR/tk_ready_mock" 2>/dev/null || echo ""
        ;;
    *)
        echo "Mock tk: $@" >&2
        ;;
esac
```

### 6.5 Test Scenarios

| Scenario | Duration | Validates |
|----------|----------|-----------|
| Smoke test | 30s | Basic loop functionality |
| Stress test | 5min | 100+ tickets without crash |
| Recovery test | 2min | Restart after kill -9 |
| Network flake | 3min | Retry behavior on transient errors |

---

## 7. Rollout & Risks

### 7.1 Rollout Phases

| Phase | Scope | Duration | Success Criteria |
|-------|-------|----------|------------------|
| **Alpha** | Developer testing only | 1 day | No crashes on happy path |
| **Beta** | Small team (3-5 users) | 3 days | Process 50+ tickets without manual intervention |
| **GA** | All users | - | Documented, tested, integrated |

### 7.2 Installation

```bash
# Option 1: Direct execution
./scripts/tk-loop.sh --clarify

# Option 2: Install to PATH
cp scripts/tk-loop.sh /usr/local/bin/tk-loop
chmod +x /usr/local/bin/tk-loop
tk-loop --clarify

# Option 3: Via package manager (future)
pip install pi-tk-flow[loop]
tk-loop --clarify
```

### 7.3 Configuration

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `TK_LOOP_POLL_INTERVAL` | `5` | Seconds between tk ready polls |
| `TK_LOOP_MAX_RETRIES` | `3` | Retry attempts per ticket |
| `TK_LOOP_STATE_DIR` | `.tk-loop-state` | State directory path |
| `TK_LOOP_LOG_LEVEL` | `INFO` | Log verbosity (DEBUG/INFO/WARN/ERROR) |

### 7.4 Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Infinite loop** | Low | High | Recursion guard (`PI_TK_INTERACTIVE_CHILD=1`) |
| **Ticket stuck in processing** | Medium | Medium | Timeout per ticket, skip on failure |
| **State corruption** | Low | Medium | Atomic writes, temp file pattern |
| **Resource exhaustion** | Low | High | Max tickets per run option |
| **tk CLI changes** | Low | Medium | Version check, graceful degradation |
| **pi crashes** | Medium | Medium | Retry with backoff, record failures |

### 7.5 Rollback Plan

```bash
# If issues detected:
# 1. Kill running loops
pkill -f tk-loop

# 2. Clear state
rm -rf .tk-loop-state

# 3. Revert to manual process
tk ready
pi "/tk-implement TICKET-ID --clarify"
```

### 7.6 Monitoring in Production

**Dashboard Metrics:**

- Tickets processed per hour
- Average processing time
- Failure rate
- Loop uptime

**Alerts:**

- Failure rate > 20% over 1 hour
- No tickets processed in 24 hours (if queue has items)
- Loop process not running (if expected to be always-on)

---

## Appendix A: Full Script Skeleton

```bash
#!/usr/bin/env bash
#
# tk-loop - Continuously process tk tickets via pi /tk-implement
#
# Usage: tk-loop [OPTIONS]
#
# Options:
#   --clarify      Open chain clarification TUI (default)
#   --hands-free   Agent-monitored overlay
#   --dispatch     Background execution
#   --interactive  Supervised blocking overlay
#   --dry-run      Parse without executing
#   --verbose      Enable debug logging
#   --help         Show this message
#   --version      Show version
#
# Environment:
#   TK_LOOP_POLL_INTERVAL  Seconds between polls (default: 5)
#   TK_LOOP_MAX_RETRIES    Max retries per ticket (default: 3)
#   TK_LOOP_STATE_DIR      State directory (default: .tk-loop-state)
#

set -euo pipefail

# Version
VERSION="1.0.0"

# Defaults
MODE="clarify"
DRY_RUN=false
VERBOSE=false
POLL_INTERVAL="${TK_LOOP_POLL_INTERVAL:-5}"
MAX_RETRIES="${TK_LOOP_MAX_RETRIES:-3}"
STATE_DIR="${TK_LOOP_STATE_DIR:-.tk-loop-state}"

# Logging
log() {
    local level="$1"
    shift
    local msg="$*"
    local ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    if [ "$level" = "DEBUG" ] && [ "$VERBOSE" = false ]; then
        return
    fi
    
    echo "{\"ts\":\"$ts\",\"level\":\"$level\",\"msg\":\"$msg\"}"
    echo "{\"ts\":\"$ts\",\"level\":\"$level\",\"msg\":\"$msg\"}" >> "$STATE_DIR/loop.log"
}

# Flag parsing
parse_flags() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --clarify)     MODE="clarify" ;;
            --hands-free)  MODE="hands-free" ;;
            --dispatch)    MODE="dispatch" ;;
            --interactive) MODE="interactive" ;;
            --dry-run)     DRY_RUN=true ;;
            --verbose)     VERBOSE=true ;;
            --help)        show_help; exit 0 ;;
            --version)     echo "tk-loop v$VERSION"; exit 0 ;;
            *)             echo "Unknown flag: $1" >&2; exit 1 ;;
        esac
        shift
    done
}

# Validate flag combinations
validate_flags() {
    local mode_count=0
    [ "$MODE" = "clarify" ] && ((mode_count++)) || true
    [ "$MODE" = "hands-free" ] && ((mode_count++)) || true
    [ "$MODE" = "dispatch" ] && ((mode_count++)) || true
    [ "$MODE" = "interactive" ] && ((mode_count++)) || true
    
    if [ $mode_count -gt 1 ]; then
        echo "Error: Cannot combine multiple mode flags" >&2
        exit 1
    fi
}

# Dependency checks
validate_dependencies() {
    command -v tk >/dev/null 2>&1 || { echo "Error: tk CLI not found" >&2; exit 1; }
    command -v pi >/dev/null 2>&1 || { echo "Error: pi CLI not found" >&2; exit 1; }
}

# Initialize state directory
init_state_dir() {
    mkdir -p "$STATE_DIR"
    echo $$ > "$STATE_DIR/loop.pid"
    echo "" > "$STATE_DIR/current-ticket"
    [ ! -f "$STATE_DIR/processed.json" ] && echo "[]" > "$STATE_DIR/processed.json"
    [ ! -f "$STATE_DIR/failed.json" ] && echo "[]" > "$STATE_DIR/failed.json"
}

# Parse ticket IDs from tk ready output
parse_ticket_ids() {
    local output="$1"
    echo "$output" | awk 'NF {print $1}' | grep -E '^[A-Za-z0-9-]+$' || true
}

# Build pi command with recursion guard
build_pi_command() {
    local ticket_id="$1"
    local mode_flag=""
    
    case "$MODE" in
        clarify)     mode_flag="--clarify" ;;
        hands-free)  mode_flag="--hands-free" ;;
        dispatch)    mode_flag="--dispatch" ;;
        interactive) mode_flag="--interactive" ;;
    esac
    
    echo "PI_TK_INTERACTIVE_CHILD=1 pi \"/tk-implement ${ticket_id} ${mode_flag}\""
}

# Execute with retry
execute_with_retry() {
    local cmd="$1"
    local retry=0
    local backoff=5
    
    while [ $retry -lt $MAX_RETRIES ]; do
        if eval "$cmd"; then
            return 0
        fi
        
        retry=$((retry + 1))
        log "WARN" "Command failed, attempt $retry/$MAX_RETRIES"
        
        if [ $retry -lt $MAX_RETRIES ]; then
            sleep $backoff
            backoff=$((backoff * 2))
        fi
    done
    
    return 1
}

# Record success
record_success() {
    local ticket_id="$1"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local record="{\"id\":\"$ticket_id\",\"ts\":\"$timestamp\"}"
    local existing=$(cat "$STATE_DIR/processed.json")
    echo "${existing%]},$record]" > "$STATE_DIR/processed.json"
    
    log "INFO" "Ticket completed: $ticket_id"
}

# Record failure
record_failure() {
    local ticket_id="$1"
    local error_msg="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local record="{\"id\":\"$ticket_id\",\"ts\":\"$timestamp\",\"error\":\"$error_msg\"}"
    local existing=$(cat "$STATE_DIR/failed.json")
    echo "${existing%]},$record]" > "$STATE_DIR/failed.json"
    
    log "ERROR" "Ticket failed: $ticket_id - $error_msg"
}

# Cleanup on exit
cleanup() {
    log "INFO" "Loop shutting down"
    echo "" > "$STATE_DIR/current-ticket"
    rm -f "$STATE_DIR/loop.pid"
    exit 0
}

# Main loop
run_loop() {
    log "INFO" "Loop started (mode: $MODE)"
    
    while true; do
        # Get tickets
        local tickets
        tickets=$(tk ready 2>/dev/null || echo "")
        local ids=$(parse_ticket_ids "$tickets")
        
        # Check if empty
        if [ -z "$ids" ]; then
            log "INFO" "No tickets in queue, exiting"
            exit 0
        fi
        
        # Process each ticket
        while IFS= read -r ticket_id; do
            [ -z "$ticket_id" ] && continue
            
            log "INFO" "Processing ticket: $ticket_id"
            echo "$ticket_id" > "$STATE_DIR/current-ticket"
            
            local cmd=$(build_pi_command "$ticket_id")
            log "DEBUG" "Command: $cmd"
            
            if [ "$DRY_RUN" = true ]; then
                log "INFO" "Dry run, skipping execution"
                record_success "$ticket_id"
            elif execute_with_retry "$cmd"; then
                record_success "$ticket_id"
            else
                record_failure "$ticket_id" "Command failed after $MAX_RETRIES retries"
            fi
            
            echo "" > "$STATE_DIR/current-ticket"
            
        done <<< "$ids"
        
        # Brief pause before re-polling
        sleep "$POLL_INTERVAL"
    done
}

# Show help
show_help() {
    cat << 'EOF'
tk-loop - Continuously process tk tickets via pi /tk-implement

Usage: tk-loop [OPTIONS]

Options:
  --clarify      Open chain clarification TUI (default)
  --hands-free   Agent-monitored overlay
  --dispatch     Background execution
  --interactive  Supervised blocking overlay
  --dry-run      Parse without executing
  --verbose      Enable debug logging
  --help         Show this message
  --version      Show version

Environment:
  TK_LOOP_POLL_INTERVAL  Seconds between polls (default: 5)
  TK_LOOP_MAX_RETRIES    Max retries per ticket (default: 3)
  TK_LOOP_STATE_DIR      State directory (default: .tk-loop-state)

Examples:
  tk-loop --clarify        # Interactive TUI for each ticket
  tk-loop --hands-free     # Agent-monitored, non-blocking
  tk-loop --dispatch       # Fire-and-forget background mode
EOF
}

# Entry point
main() {
    parse_flags "$@"
    validate_flags
    validate_dependencies
    init_state_dir
    trap cleanup SIGINT SIGTERM
    run_loop
}

main "$@"
```

---

## Appendix B: Integration with pi Extension

The loop can optionally be registered as a pi extension command:

```typescript
// extensions/tk-loop.ts
import type { ExtensionAPI } from "@mariozechner/pi";

export default function tkLoopExtension(pi: ExtensionAPI) {
  pi.registerCommand("tk loop", {
    description: "Continuously process tk tickets",
    examples: [
      "tk loop --clarify",
      "tk loop --hands-free",
    ],
    handler: async (args: string, ctx) => {
      // Delegate to bash script
      const result = await ctx.spawn("scripts/tk-loop.sh", args.split(" "));
      return result;
    },
  });
}
```

This allows users to run `pi "/tk loop --clarify"` from within pi sessions.
