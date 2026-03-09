#!/usr/bin/env bash
# End-to-end integration tests for .tf/scripts/tk-loop.sh

set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TK_LOOP="$SCRIPT_DIR/tk-loop.sh"
MOCK_DIR="$SCRIPT_DIR/test-mocks"

TESTS_PASSED=0
TESTS_FAILED=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TEMP_ROOT=""
TEST_TMP=""
STATE_DIR=""
READY_FILE=""

log() {
  echo -e "${YELLOW}[$(date +%H:%M:%S)]${NC} $*"
}

pass() {
  echo -e "${GREEN}✓ PASS${NC} - $*"
  TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
  echo -e "${RED}✗ FAIL${NC} - $*"
  TESTS_FAILED=$((TESTS_FAILED + 1))
}

cleanup_case() {
  if [[ -n "$TEST_TMP" && -d "$TEST_TMP" ]]; then
    rm -rf "$TEST_TMP"
  fi
  TEST_TMP=""
  STATE_DIR=""
  READY_FILE=""

  unset TK_LOOP_STATE_DIR TK_LOOP_POLL_INTERVAL TK_MOCK_READY_FILE TK_MOCK_PI_VERBOSE TK_MOCK_PI_SLEEP_SEC
}

setup_case() {
  cleanup_case

  TEST_TMP="$(mktemp -d "$TEMP_ROOT/case.XXXXXX")"
  STATE_DIR="$TEST_TMP/state"
  READY_FILE="$TEST_TMP/ready.txt"

  mkdir -p "$STATE_DIR"
  : > "$READY_FILE"

  export TK_LOOP_STATE_DIR="$STATE_DIR"
  export TK_LOOP_POLL_INTERVAL=0
  export TK_MOCK_READY_FILE="$READY_FILE"
  export PATH="$MOCK_DIR:$PATH"

  # Ensure parent environment doesn't trip recursion guard unexpectedly.
  unset PI_TK_INTERACTIVE_CHILD
}

json_has_keys() {
  local file="$1"
  shift
  python3 - "$file" "$@" <<'PY'
import json, sys
path = sys.argv[1]
keys = sys.argv[2:]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
for key in keys:
    if key not in data:
        raise SystemExit(1)
print("ok")
PY
}

jsonl_lines_have_keys() {
  local file="$1"
  shift
  python3 - "$file" "$@" <<'PY'
import json, sys
path = sys.argv[1]
keys = sys.argv[2:]
with open(path, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]
if not lines:
    raise SystemExit(1)
for line in lines:
    row = json.loads(line)
    for key in keys:
        if key not in row:
            raise SystemExit(1)
print("ok")
PY
}

run_test() {
  local name="$1"
  shift
  log "Running: $name"
  if "$@"; then
    pass "$name"
  else
    fail "$name"
  fi
}

scenario_empty() {
  setup_case
  "$TK_LOOP" --dry-run >/dev/null 2>&1
  local rc=$?

  [[ $rc -eq 0 ]] || return 1
  [[ -f "$STATE_DIR/metrics.json" ]] || return 1
  [[ -f "$STATE_DIR/processed.jsonl" ]] || return 1
  [[ -f "$STATE_DIR/failed.jsonl" ]] || return 1

  local processed_count
  processed_count=$(wc -l < "$STATE_DIR/processed.jsonl" | tr -d ' ')
  [[ "$processed_count" -eq 0 ]]
}

scenario_single() {
  setup_case
  cat > "$READY_FILE" <<EOF
ptf-a111 Single ticket
EOF

  "$TK_LOOP" --dry-run >/dev/null 2>&1

  local processed_count
  processed_count=$(wc -l < "$STATE_DIR/processed.jsonl" | tr -d ' ')
  [[ "$processed_count" -eq 1 ]] || return 1

  grep -q '"id":"ptf-a111"' "$STATE_DIR/processed.jsonl"
}

scenario_multi() {
  setup_case
  cat > "$READY_FILE" <<EOF
ptf-a111 First
ptf-b222 Second
ptf-c333 Third
EOF

  "$TK_LOOP" --dry-run >/dev/null 2>&1

  local processed_count
  processed_count=$(wc -l < "$STATE_DIR/processed.jsonl" | tr -d ' ')
  [[ "$processed_count" -eq 3 ]] || return 1

  grep -q '"id":"ptf-c333"' "$STATE_DIR/processed.jsonl"
}

scenario_failure() {
  setup_case
  cat > "$READY_FILE" <<EOF
ptf-fail1 Should fail
ptf-pass2 Should pass
EOF

  "$TK_LOOP" --clarify >/dev/null 2>&1

  grep -q '"id":"ptf-fail1"' "$STATE_DIR/failed.jsonl" || return 1
  grep -q '"id":"ptf-pass2"' "$STATE_DIR/processed.jsonl"
}

scenario_guard() {
  setup_case
  PI_TK_INTERACTIVE_CHILD=1 "$TK_LOOP" --dry-run >"$TEST_TMP/out.log" 2>&1
  local rc=$?

  [[ $rc -ne 0 ]] || return 1
  grep -q "Nested tk-loop detected" "$TEST_TMP/out.log"
}

scenario_mutex() {
  setup_case
  "$TK_LOOP" --clarify --hands-free >"$TEST_TMP/out.log" 2>&1
  local rc=$?

  [[ $rc -ne 0 ]] || return 1
  grep -q "Cannot combine multiple mode flags" "$TEST_TMP/out.log"
}

scenario_schema() {
  setup_case
  cat > "$READY_FILE" <<EOF
ptf-a111 Schema check
EOF

  "$TK_LOOP" --dry-run >/dev/null 2>&1

  jsonl_lines_have_keys "$STATE_DIR/processed.jsonl" id ts >/dev/null || return 1
  jsonl_lines_have_keys "$STATE_DIR/loop.log" ts level msg >/dev/null || return 1
  json_has_keys "$STATE_DIR/metrics.json" started_at mode tickets_processed tickets_failed pid >/dev/null || return 1

  return 0
}

scenario_pid() {
  setup_case

  # Active lock should block
  sleep 60 &
  local sleeper=$!
  echo "$sleeper" > "$STATE_DIR/loop.pid"

  "$TK_LOOP" --dry-run >"$TEST_TMP/active.log" 2>&1
  local active_rc=$?
  kill "$sleeper" >/dev/null 2>&1 || true
  wait "$sleeper" >/dev/null 2>&1 || true

  [[ $active_rc -ne 0 ]] || return 1
  grep -q "already running" "$TEST_TMP/active.log" || return 1

  # Stale lock should be cleaned and run should succeed
  echo "999999" > "$STATE_DIR/loop.pid"
  "$TK_LOOP" --dry-run >"$TEST_TMP/stale.log" 2>&1 || return 1
  grep -q "Removing stale PID lock file" "$TEST_TMP/stale.log"
}

scenario_signal() {
  setup_case
  cat > "$READY_FILE" <<EOF
ptf-a111 Signal check
EOF
  export TK_LOOP_POLL_INTERVAL=30

  "$TK_LOOP" --dry-run >"$TEST_TMP/signal.log" 2>&1 &
  local loop_pid=$!

  # Wait for lock file creation
  local i
  for i in {1..20}; do
    [[ -f "$STATE_DIR/loop.pid" ]] && break
    sleep 0.1
  done

  kill -TERM "$loop_pid" >/dev/null 2>&1 || true
  wait "$loop_pid" >/dev/null 2>&1 || true

  [[ ! -f "$STATE_DIR/loop.pid" ]] || return 1
  grep -q "Loop shutdown complete" "$STATE_DIR/loop.log"
}

main() {
  if [[ ! -x "$TK_LOOP" ]]; then
    echo "tk-loop script not found or not executable: $TK_LOOP"
    exit 2
  fi
  if [[ ! -x "$MOCK_DIR/tk" || ! -x "$MOCK_DIR/pi" ]]; then
    echo "Mock binaries missing or not executable in: $MOCK_DIR"
    exit 2
  fi

  TEMP_ROOT="$(mktemp -d)"
  trap 'cleanup_case; rm -rf "$TEMP_ROOT"' EXIT

  echo "=============================================="
  echo "tk-loop end-to-end scenarios"
  echo "=============================================="

  run_test "empty" scenario_empty
  run_test "single" scenario_single
  run_test "multi" scenario_multi
  run_test "failure" scenario_failure
  run_test "guard" scenario_guard
  run_test "mutex" scenario_mutex
  run_test "schema" scenario_schema
  run_test "pid" scenario_pid
  run_test "signal" scenario_signal

  echo "----------------------------------------------"
  echo "Passed: $TESTS_PASSED"
  echo "Failed: $TESTS_FAILED"
  echo "----------------------------------------------"

  if [[ "$TESTS_FAILED" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

main "$@"
