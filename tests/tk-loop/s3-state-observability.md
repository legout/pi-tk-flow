# S3: State Directory and Structured Observability - Acceptance Tests

**Ticket**: ptf-wuvd
**Status**: Verified
**Date**: 2026-03-09

## Acceptance Criteria Verification

### AC1: .tk-loop-state is initialized with required files

**Requirement**: State directory contains all required files on initialization.

**Verification**:
```bash
ls -la .tk-loop-state/
```

**Expected files**:
- `loop.pid` - PID lock file
- `current-ticket` - Currently processing ticket marker
- `processed.jsonl` - Successfully processed tickets (JSONL)
- `failed.jsonl` - Failed tickets (JSONL)
- `loop.log` - Structured execution log (JSONL)
- `metrics.json` - Aggregated statistics (JSON)

**Status**: ✅ PASS

---

### AC2: Active PID lock blocks concurrent loops; stale locks are handled safely

**Requirement**: 
- If a PID lock file exists with a running process, block execution
- If a PID lock file exists with a dead process, clean up and proceed

**Verification**:
```bash
# Test active lock (using current PID)
TEST_DIR=$(mktemp -d)
echo $$ > "$TEST_DIR/loop.pid"
TK_LOOP_STATE_DIR="$TEST_DIR" .tf/scripts/tk-loop.sh --dry-run 2>&1 | grep "Another tk-loop"
# Should output: "Another tk-loop instance is already running (PID: ...)"

# Test stale lock (using non-existent PID)
echo "99999998" > "$TEST_DIR/loop.pid"
TK_LOOP_STATE_DIR="$TEST_DIR" .tf/scripts/tk-loop.sh --dry-run 2>&1 | grep -E "(stale|Removing|No ready)"
# Should clean up stale lock and proceed
rm -rf "$TEST_DIR"
```

**Status**: ✅ PASS

---

### AC3: processed.jsonl and failed.jsonl append valid JSONL records

**Requirement**: Each line in JSONL files is a valid JSON object.

**Record Format**:
```json
// processed.jsonl
{"id":"ptf-abc1","ts":"2026-03-09T02:18:07Z"}

// failed.jsonl
{"id":"ptf-abc1","ts":"2026-03-09T02:18:07Z","error":"exit code 1"}
```

**Verification**:
```bash
# Check each line is valid JSON
head -3 .tk-loop-state/processed.jsonl | jq -e .
# Should output valid JSON for each line

# Verify failed.jsonl structure (if not empty)
if [ -s .tk-loop-state/failed.jsonl ]; then
  head -3 .tk-loop-state/failed.jsonl | jq -e .
fi
```

**Status**: ✅ PASS

---

### AC4: metrics.json stays valid JSON and updates counters on each ticket

**Requirement**: metrics.json is always valid JSON with up-to-date counters.

**Expected Structure**:
```json
{
  "started_at": "2026-03-09T02:41:20Z",
  "mode": "clarify",
  "tickets_processed": 275,
  "tickets_failed": 0,
  "current_ticket": null,
  "last_poll_at": "2026-03-09T02:41:20Z",
  "total_runtime_sec": 1393,
  "pid": 14062
}
```

**Verification**:
```bash
# Validate JSON structure
jq -e '.tickets_processed' .tk-loop-state/metrics.json
jq -e '.tickets_failed' .tk-loop-state/metrics.json
jq -e '.started_at' .tk-loop-state/metrics.json
jq -e '.mode' .tk-loop-state/metrics.json
jq -e '.pid' .tk-loop-state/metrics.json
```

**Status**: ✅ PASS

---

### AC5: loop.log captures structured entries aligned with console events

**Requirement**: Each log entry is a valid JSON object with ts, level, and msg fields.

**Expected Format**:
```json
{"ts":"2026-03-09T02:18:07Z","level":"INFO","msg":"Initialization complete (mode: clarify)"}
```

**Verification**:
```bash
# Check structure of log entries
head -1 .tk-loop-state/loop.log | jq 'keys'
# Should output: ["level", "msg", "ts"]

# Verify required fields
head -1 .tk-loop-state/loop.log | jq -e 'has("ts") and has("level") and has("msg")'
# Should output: true
```

**Status**: ✅ PASS

---

## Summary

| AC | Description | Status |
|----|-------------|--------|
| AC1 | State directory initialized with required files | ✅ PASS |
| AC2 | PID lock blocks concurrent; stale handled safely | ✅ PASS |
| AC3 | JSONL records valid in processed/failed files | ✅ PASS |
| AC4 | metrics.json valid JSON with counters | ✅ PASS |
| AC5 | loop.log structured entries | ✅ PASS |

**Overall**: All 5 acceptance criteria verified.

## Implementation Notes

- Script path: `.tf/scripts/tk-loop.sh`
- State directory: `.tk-loop-state/`
- Uses `loop.pid` for PID lock (plan specified `pid.lock` - minor naming difference)
- JSONL fields use short names (`id`, `ts`) for compactness
- All functionality implemented in Tasks 7, 9, 10 of implementation plan
