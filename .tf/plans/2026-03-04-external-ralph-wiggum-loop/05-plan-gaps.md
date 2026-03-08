# Plan Gaps: External Ralph Wiggum Loop

## Verdict
- **Ready for ticketization:** yes
- **Reason:** Planning artifacts provide comprehensive coverage of requirements, architecture, and implementation tasks. The 12 identified gaps are minor and can be addressed during implementation or as subtasks. Core functionality is well-defined with clear acceptance criteria.

## Gap Summary
- Critical: 0
- Major: 2
- Minor: 6

## Gaps

### Major Gaps

1. **[Major] GAP-001: Missing Integration Testing Task**
   - **Where:** 03-implementation-plan.md, Task 11
   - **Issue:** No explicit task validates the complete end-to-end flow from flag parsing through ticket execution. Individual task verifications don't ensure components work together (e.g., Task 5's parser with Task 8's loop).
   - **Impact:** Risk of components working in isolation but failing when integrated. Could lead to late discovery of interface mismatches.
   - **Recommended fix:** Add Task 13 "Integration Testing" or extend Task 11 with an end-to-end test scenario that exercises: flag parsing → ticket parsing → command building → state recording.
   - **Blocks ticketization?:** no

2. **[Major] GAP-002: Mock Infrastructure Undefined**
   - **Where:** 03-implementation-plan.md, Task 11; 02-spec.md, Section 6.4
   - **Issue:** Task 11 mentions mocking `tk` and `pi` CLIs but doesn't specify: (a) where mock files live, (b) how they're activated (PATH manipulation?), (c) mock behavior configurability.
   - **Impact:** Test implementation will be blocked or inconsistent without clear mock infrastructure guidance.
   - **Recommended fix:** Add subtask to Task 11: "Create mock CLI infrastructure" with specifications for mock location (`.tf/scripts/test-mocks/`), PATH injection method, and configurable mock responses via environment variables or files.
   - **Blocks ticketization?:** no

### Minor Gaps

3. **[Minor] GAP-003: Log Rotation Not Addressed**
   - **Where:** 00-design.md, Risks table; 02-spec.md, Section 5.1
   - **Issue:** Design identifies log rotation as a risk but no task implements it or addresses unbounded log file growth in `.tk-loop-state/loop.log`.
   - **Impact:** Long-running loops could fill disk space; logs become unwieldy to parse.
   - **Recommended fix:** Add subtask to Task 7: "Implement basic log size limiting" - rotate when loop.log exceeds 10MB, keeping one backup (loop.log.1). Or document as known limitation in README.
   - **Blocks ticketization?:** no

4. **[Minor] GAP-004: Environment Variable Validation Missing**
   - **Where:** 03-implementation-plan.md, Task 2
   - **Issue:** Tasks validate flags but don't validate environment variables (TK_LOOP_POLL_INTERVAL, TK_LOOP_MAX_RETRIES) for valid ranges (e.g., negative values, non-numeric).
   - **Impact:** Invalid env vars could cause unexpected behavior (infinite sleep with negative interval, etc.).
   - **Recommended fix:** Add subtask to Task 2: "Validate environment variables" - check POLL_INTERVAL is positive integer, MAX_RETRIES is non-negative integer, STATE_DIR is writable.
   - **Blocks ticketization?:** no

5. **[Minor] GAP-005: Ticket ID Format Validation**
   - **Where:** 03-implementation-plan.md, Task 5
   - **Issue:** Task 5 parses tickets using regex but doesn't explicitly validate extracted IDs match expected format before processing. The regex in `parse_tickets` extracts IDs but no validation occurs before `process_ticket` uses them.
   - **Impact:** Malformed ticket IDs could be passed to `pi` command causing failures.
   - **Recommended fix:** Add validation in `parse_tickets` or `process_ticket` to verify ticket ID matches `^ptf-[a-z0-9]{4}$` before processing, logging a warning for invalid IDs.
   - **Blocks ticketization?:** no

6. **[Minor] GAP-006: Exit Code Standardization**
   - **Where:** 02-spec.md, Section 4.1; 03-implementation-plan.md, various tasks
   - **Issue:** Different failure scenarios don't have standardized exit codes documented. Design mentions "Exit 0" for success but doesn't define codes for: dependency missing, recursion detected, invalid flags, ticket failures.
   - **Impact:** Calling scripts can't programmatically determine failure reason; inconsistent with Unix conventions.
   - **Recommended fix:** Document exit codes in Task 1 (script header) or 02-spec.md: 0=success, 1=general error, 2=dependency missing, 3=recursion detected, 4=invalid flags, 5=concurrent instance running.
   - **Blocks ticketization?:** no

7. **[Minor] GAP-007: State Directory Permissions Not Validated**
   - **Where:** 03-implementation-plan.md, Task 7
   - **Issue:** Task 7 initializes state directory but doesn't validate it's writable or handle permission errors gracefully.
   - **Impact:** Cryptic errors if state directory is on read-only filesystem or lacks permissions.
   - **Recommended fix:** Add to Task 7: validate directory is writable before creating files, provide clear error message if not.
   - **Blocks ticketization?:** no

8. **[Minor] GAP-008: `--version` Flag Implementation Not Explicitly Covered**
   - **Where:** 02-spec.md, Appendix A (script skeleton shows `--version`); 03-implementation-plan.md, Task 2
   - **Issue:** The `--version` flag is in the skeleton but Task 2's verification only mentions mode flags, not `--version`.
   - **Impact:** May be overlooked during implementation.
   - **Recommended fix:** Add `--version` to Task 2 verification checklist.
   - **Blocks ticketization?:** no

## Quick Fix Plan

1. **GAP-001 (Major):** Add subtask to Task 11 for end-to-end integration test covering full flow
2. **GAP-002 (Major):** Add subtask to Task 11 defining mock infrastructure location and approach
3. **GAP-003 (Minor):** Document log rotation as known limitation in Task 12 README
4. **GAP-004 (Minor):** Add env var validation subtask to Task 2
5. **GAP-005 (Minor):** Add ticket ID validation to Task 5 implementation notes
6. **GAP-006 (Minor):** Add exit code documentation to Task 1 header comment
7. **GAP-007 (Minor):** Add permission check to Task 7 verification
8. **GAP-008 (Minor):** Add `--version` to Task 2 verification list

## Additional Observations

### Strengths
- Clear task dependencies and sequencing
- Comprehensive risk identification in design
- Good separation of concerns across components
- Rollback strategy is straightforward (no DB migrations)
- Test scenarios well-defined in PRD

### Implementation Notes for Ticketizer
- Tasks 1-10 are sequential dependencies; Tasks 11-12 can run in parallel after Task 10
- Task 8 (Main Loop) is highest risk - consider breaking into smaller subtasks
- Mock infrastructure (GAP-002) should be implemented early if possible to enable testing
- Consider adding a "smoke test" task between Task 10 and 11 for quick validation
