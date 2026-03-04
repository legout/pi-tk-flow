# PRD: External Ralph Wiggum Loop

**Feature**: Automated Ticket Processing Loop
**Date**: 2026-03-04
**Status**: Draft

---

## Problem Statement

1. **Manual Orchestration Tedium**: Developers must manually invoke `/tk-implement <ticket-id>` for each open ticket, monitoring progress and queuing the next one.
2. **No Batch Processing**: There is no way to process multiple tickets automatically in sequence.
3. **Context Switching Overhead**: Constant context switching between ticket selection and implementation monitoring reduces productivity.
4. **Missing Automation**: The tk workflow lacks an automated "process all ready tickets" capability.

## Solution

Introduce an external bash script that continuously polls `tk ready` for open tickets and processes each one via `pi "/tk-implement <ticket-id> --clarify"` until the queue is empty.

**Key Design Elements:**
- External bash script (not a pi agent)
- Polls `tk ready` to get ticket IDs
- Sequential processing (one ticket at a time)
- Supports multiple execution modes (clarify, hands-free, dispatch, interactive)
- Recursion guard to prevent nested loops
- Clean exit when queue is empty

## User Stories

### US-1: Batch Ticket Processing
**As a** developer
**I want** to run a single command that processes all open tickets
**So that** I don't have to manually orchestrate ticket-by-ticket execution

**Acceptance Criteria:**
- Script runs `tk ready` to detect open tickets
- Processes each ticket sequentially via `/tk-implement <ID>`
- Exits cleanly when no tickets remain
- Logs progress to console and/or file

### US-2: Clarify Mode Integration
**As a** developer
**I want** each ticket to open with the clarify TUI
**So that** I can review and adjust the execution plan before proceeding

**Acceptance Criteria:**
- Script invokes `pi "/tk-implement <ID> --clarify"` for each ticket
- Clarify TUI opens as expected
- User can interact with clarify UI normally
- Loop continues after clarify session completes

### US-3: Clean Exit on Empty Queue
**As a** developer
**I want** the loop to exit cleanly when there are no more tickets
**So that** I know the batch is complete

**Acceptance Criteria:**
- Script checks `tk ready` before each iteration
- Exits with status 0 when queue is empty
- Logs "No tickets remaining" message
- Does not hang or loop indefinitely

### US-4: Recursion Safety
**As a** developer
**I want** protection against nested loop invocations
**So that** the script doesn't accidentally spawn multiple competing loops

**Acceptance Criteria:**
- Uses `PI_TK_INTERACTIVE_CHILD=1` environment variable as guard
- Detects if already running in a loop context
- Exits with clear error if nested invocation detected
- Documented in script help text

### US-5: Multiple Execution Modes
**As a** developer
**I want** to choose how each ticket is executed
**So that** I can balance between supervision and automation

**Acceptance Criteria:**
- Supports `--clarify` (default): interactive TUI for planning
- Supports `--hands-free`: agent-monitored, non-blocking
- Supports `--dispatch`: fire-and-forget background execution
- Supports `--interactive`: supervised, blocking
- Mode selection via command-line flag

## Implementation Decisions

### ID-1: Script Location
**Decision**: Place script at `.tf/scripts/tk-loop.sh`
**Rationale**: Keeps automation scripts organized under `.tf/` with other tk workflow artifacts
**Alternatives Considered**: Project root, `scripts/` directory

### ID-2: Execution Mode
**Decision**: Sequential processing (one ticket at a time)
**Rationale**: Simpler error handling, clearer state management, avoids resource contention
**Alternatives Considered**: Parallel processing with worker pool

### ID-3: Recursion Guard
**Decision**: Use `PI_TK_INTERACTIVE_CHILD=1` environment variable
**Rationale**: Consistent with existing Ralph Wiggum interactive mode patterns
**Implementation**: Check at script startup, set before invoking pi

### ID-4: State Management
**Decision**: Maintain state in `.tk-loop-state/` directory
**Rationale**: Enables observability, debugging, and potential recovery features
**Contents**: PID lock file, processed tickets log, failed tickets log

### ID-5: Error Handling
**Decision**: Record failures and continue processing remaining tickets
**Rationale**: One stuck ticket shouldn't block the entire queue
**Implementation**: Log failed ticket IDs to `.tk-loop-state/failed.json`

### ID-6: Polling Interval
**Decision**: Configurable via `TK_LOOP_POLL_INTERVAL` env var (default: 5 seconds)
**Rationale**: Balances responsiveness with system load
**Implementation**: Sleep between `tk ready` checks

## Testing Decisions

### TD-1: Empty Queue Test
**Scenario**: Run script when no tickets are open
**Expected**: Script exits immediately with success status
**Verification**: Check exit code (0), verify log message "No tickets remaining"

### TD-2: Single Ticket Test
**Scenario**: Run script with one open ticket
**Expected**: Script processes the ticket, then exits
**Verification**: Verify ticket was implemented, check exit code (0)

### TD-3: Multiple Tickets Test
**Scenario**: Run script with 3+ open tickets
**Expected**: Script processes all tickets sequentially, then exits
**Verification**: Verify all tickets implemented, check processing order matches queue

### TD-4: Failure Recovery Test
**Scenario**: Run script with one failing ticket and one succeeding ticket
**Expected**: Script records failure for first ticket, processes second ticket, then exits
**Verification**: Check failed.json contains first ticket ID, verify second ticket succeeded

### TD-5: Recursion Guard Test
**Scenario**: Run script from within another script invocation
**Expected**: Nested invocation exits with error
**Verification**: Set `PI_TK_INTERACTIVE_CHILD=1`, verify script detects and exits

### TD-6: Mode Selection Test
**Scenario**: Run script with different mode flags
**Expected**: Each mode invokes pi with correct parameters
**Verification**: Verify `--clarify` opens TUI, `--dispatch` runs in background, etc.

## Out of Scope

1. **Parallel Processing**: Script processes one ticket at a time (no concurrent workers)
2. **Error Recovery**: Failed tickets are logged but not automatically retried in the same run
3. **State Persistence Across Restarts**: Each run starts fresh (no checkpoint resumption)
4. **Windows Support**: Bash script targets Unix-like systems only
5. **Priority Ordering**: Tickets processed in `tk ready` output order (no custom prioritization)
6. **Dependency Resolution**: Script does not analyze ticket dependencies before processing
7. **Resource Limits**: No CPU/memory throttling or concurrent execution limits
8. **Web UI/Dashboard**: No visualization of loop progress or state
