# Design: External Ralph Wiggum Loop

**Status**: Draft
**Created**: 2026-03-04
**Related**: PRD (01-prd.md), Spec (02-spec.md)

---

## Context

### Problem
Manual ticket-by-ticket orchestration is tedious and error-prone. Developers currently invoke `/tk-implement <ticket-id>` individually for each ticket, requiring constant monitoring and manual queuing.

### Solution
An external bash script that continuously polls `tk ready` for open tickets and processes each one via `pi "/tk-implement <ticket-id>"` with configurable execution modes.

### Constraints
- Must be external to pi's agent system (bash script)
- Must use `tk ready` CLI command to get ticket queue
- Must support `--clarify`, `--hands-free`, `--dispatch`, `--interactive` modes
- Must include recursion guard to prevent nested loops
- Must exit cleanly when no tickets remain

---

## Chosen Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    tk-loop.sh (Bash Script)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Parse flags (--clarify, --hands-free, etc.)                │
│  2. Check recursion guard (PI_TK_INTERACTIVE_CHILD)            │
│  3. Initialize state (.tk-loop-state/)                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    MAIN LOOP                              │  │
│  │                                                            │  │
│  │  4. Run `tk ready` → get ticket IDs                       │  │
│  │  5. If empty: exit with success                           │  │
│  │  6. For each ticket ID:                                   │  │
│  │     a. Set PI_TK_INTERACTIVE_CHILD=1                      │  │
│  │     b. Invoke `pi "/tk-implement <ID> --<mode>"`          │  │
│  │     c. Wait for completion                                │  │
│  │     d. Record result (success/failure)                    │  │
│  │     e. Sleep (poll interval)                              │  │
│  │  7. Go to step 4                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **Flag Parser** | Parse command-line arguments | Bash getopts |
| **Recursion Guard** | Prevent nested invocations | Environment variable check |
| **Ticket Parser** | Parse `tk ready` output | Bash text processing |
| **Command Builder** | Construct pi invocation | String interpolation |
| **State Manager** | Track processed/failed tickets | JSON files in `.tk-loop-state/` |
| **Retry Handler** | Exponential backoff on failures | Bash sleep with backoff logic |

---

## Component Contracts

### 1. Flag Parser
**Input**: Command-line arguments (`$@`)
**Output**: Environment variables (`MODE`, `DRY_RUN`, `VERBOSE`)

```bash
parse_flags() {
    MODE="clarify"  # default
    DRY_RUN=false
    VERBOSE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --clarify) MODE="clarify" ;;
            --hands-free) MODE="hands-free" ;;
            --dispatch) MODE="dispatch" ;;
            --interactive) MODE="interactive" ;;
            --dry-run) DRY_RUN=true ;;
            --verbose) VERBOSE=true ;;
            *) error "Unknown flag: $1" ;;
        esac
        shift
    done
}
```

### 2. Recursion Guard
**Input**: Environment (`PI_TK_INTERACTIVE_CHILD`)
**Output**: Exit if nested, or continue

```bash
check_recursion_guard() {
    if [[ "${PI_TK_INTERACTIVE_CHILD:-}" == "1" ]]; then
        error "Nested tk-loop detected. Exiting."
        exit 1
    fi
}
```

### 3. Ticket Parser
**Input**: `tk ready` output (stdout)
**Output**: Array of ticket IDs

```bash
parse_tickets() {
    local output="$1"
    # Parse ticket IDs from tk ready output
    # Assumes format: "ptf-abc1 [status] - Title"
    echo "$output" | grep -oE '\bptf-[a-z0-9]{4}\b' | sort -u
}
```

### 4. Command Builder
**Input**: Ticket ID, Mode
**Output**: Full pi command

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
    esac
}
```

### 5. State Manager
**Input**: Ticket ID, Result (success/failure)
**Output**: JSON files in `.tk-loop-state/`

```bash
record_success() {
    local ticket_id="$1"
    echo "{\"ticket\":\"$ticket_id\",\"timestamp\":\"$(date -Iseconds)\"}" \
        >> "$STATE_DIR/processed.jsonl"
}

record_failure() {
    local ticket_id="$1"
    local error_msg="$2"
    echo "{\"ticket\":\"$ticket_id\",\"error\":\"$error_msg\",\"timestamp\":\"$(date -Iseconds)\"}" \
        >> "$STATE_DIR/failed.jsonl"
}
```

### 6. Retry Handler
**Input**: Attempt number
**Output**: Sleep duration

```bash
get_backoff_duration() {
    local attempt="$1"
    case "$attempt" in
        1) echo "5" ;;
        2) echo "10" ;;
        3) echo "20" ;;
        *) echo "0" ;;  # no more retries
    esac
}
```

---

## Key Flows

### Flow 1: Main Loop Execution

```
Start
  │
  ├─ parse_flags()
  ├─ check_recursion_guard()
  ├─ validate_dependencies()
  ├─ init_state_dir()
  │
  └─┬─ while true; do
     │
     ├─┬─ tickets=$(tk ready | parse_tickets)
     │ │
     │ ├─ if [[ -z "$tickets" ]]; then
     │ │     log "No tickets remaining"
     │ │     exit 0
     │ │   fi
     │ │
     │ └─┬─ for ticket in $tickets; do
     │   │
     │   ├─ cmd=$(build_command "$ticket" "$MODE")
     │   ├─ log "Processing $ticket"
     │   │
     │   ├─┬─ PI_TK_INTERACTIVE_CHILD=1 eval "$cmd"
     │   │ │
     │   │ ├─ if [[ $? -eq 0 ]]; then
     │   │ │     record_success "$ticket"
     │   │ │   else
     │   │ │     record_failure "$ticket" "Exit code $?"
     │   │ │   fi
     │   │ │
     │   │ └─ sleep "$POLL_INTERVAL"
     │   │
     │   └─ done
     │   │
     │   └─ done
     │
     └─ End
```

### Flow 2: Error Recovery

```
Ticket Execution Fails
  │
  ├─ record_failure(ticket, error_msg)
  │
  ├─┬─ if attempt < MAX_RETRIES; then
  │ │   backoff=$(get_backoff_duration "$attempt")
  │ │   sleep "$backoff"
  │ │   retry ticket execution
  │ │ else
  │ │   log "Max retries exceeded for $ticket"
  │ │   continue to next ticket
  │ └─ done
```

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Infinite Loop** | Low | High | Empty queue check, max iteration limit |
| **Stuck Ticket** | Medium | Medium | Retry with exponential backoff, skip after max attempts |
| **State Corruption** | Low | Medium | Use append-only JSONL files, atomic writes |
| **Recursion** | Low | High | Environment variable guard, PID lock file |
| **Resource Exhaustion** | Low | Medium | Polling interval, sequential processing |
| **tk CLI Changes** | Low | High | Version check, graceful error messages |
| **pi Invocation Failure** | Medium | Medium | Validate pi in PATH, check exit codes |
| **Concurrent Runs** | Medium | Medium | PID lock file in state directory |
| **Log Rotation** | Low | Low | Optional log rotation, size limits |

---

## Decisions

### Decided
1. ✅ **Bash script** - Simple, portable, no dependencies beyond standard Unix tools
2. ✅ **Sequential processing** - One ticket at a time, simpler error handling
3. ✅ **State directory** - `.tk-loop-state/` for observability and debugging
4. ✅ **Recursion guard** - `PI_TK_INTERACTIVE_CHILD=1` environment variable
5. ✅ **Exponential backoff** - 5s → 10s → 20s retry delays
6. ✅ **Exit on empty queue** - Batch processing, not a daemon
7. ✅ **JSONL for logs** - Append-only, easy to parse, line-delimited JSON

### Deferred
1. ⏸️ **Parallel processing** - Could add worker pool in future
2. ⏸️ **Checkpoint resumption** - Could persist state across restarts
3. ⏸️ **Priority ordering** - Could respect ticket priority fields
4. ⏸️ **Dependency resolution** - Could analyze ticket dependencies
5. ⏸️ **Web dashboard** - Could add visualization layer

### Rejected
1. ❌ **Python implementation** - Bash is simpler for this use case
2. ❌ **Daemon mode** - Batch processing model is clearer
3. ❌ **Database state** - File-based state is sufficient

---

## Implementation Approach

### Phase 1: Core Loop (MVP)
- Flag parsing
- Recursion guard
- Main polling loop
- Ticket parsing
- Command execution
- Basic logging

### Phase 2: State & Observability
- State directory
- Success/failure tracking
- Structured logging (JSONL)
- PID lock file

### Phase 3: Error Handling
- Exponential backoff
- Max retries
- Graceful degradation
- Error messages

### Phase 4: Testing & Documentation
- Unit tests (bash)
- Integration tests (end-to-end)
- README documentation
- Usage examples

---

## Success Criteria

1. ✅ Script exits cleanly when no tickets remain
2. ✅ Processes all tickets in queue sequentially
3. ✅ Records success/failure for each ticket
4. ✅ Prevents nested invocations via recursion guard
5. ✅ Supports all four execution modes (clarify, hands-free, dispatch, interactive)
6. ✅ Logs progress to console and JSONL files
7. ✅ Handles individual ticket failures gracefully
8. ✅ No external dependencies beyond bash, tk, pi
