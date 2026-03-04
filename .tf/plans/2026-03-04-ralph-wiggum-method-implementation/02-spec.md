# Technical Spec: Ralph Wiggum Method Implementation
**Date:** 2026-03-04  
**Author:** Documentation Specialist  
**Status:** Draft

---

## Architecture
1. **Entry Point (`prompts/tk-implement.md`)**
   - Extend the existing flag parsing stanza to recognize `--interactive`, `--hands-free`, and `--dispatch`.
   - Enforce mutual exclusivity between the new flags, `--async`, and (for `--interactive` only) `--clarify` before any anchoring occurs. Violations short-circuit with actionable error text (PRD ID-1, ID-2).
2. **Fast Anchoring Block**
   - Reuse today’s anchoring/context build sequence for *all* invocations so that localized knowledge is prepared regardless of execution mode (Architecture constraint from anchor context).
3. **Execution Router**
   - Introduce a dedicated routing section immediately after anchoring:
     - **Interactive path**: call `interactive_shell` with `mode: "interactive"`, constructed command `pi "/tk-implement <ticket-id> --clarify=<value?>"`, and pass through env/context variables so artifacts continue landing in `.subagent-runs/<ticket>/` (PRD ID-3, ID-4).
     - **Hands-free path**: same command as above but `mode: "hands-free"` plus `handsFree.updateMode="on-quiet"`, `handsFree.quietThreshold≈8000ms`, `handsFree.updateInterval≈60000ms` (per default tool guidance). No backgrounding so the overlay remains visible.
     - **Dispatch path**: invoke `interactive_shell` with `mode: "dispatch"` and `background: true`, ensuring `autoExitOnQuiet` stays true. Record returned `sessionId` for logging.
     - **Legacy path**: when no interactive flag is present, continue selecting Path A/B/C chains via `subagent` exactly as today.
4. **Session Metadata Logging**
   - Standardize metadata payload written into `.subagent-runs/<ticket-id>/session.json` (new file) capturing `mode`, `sessionId`, `startedAt`, and `command`. Append a short human-readable note to the existing run log so `/attach` instructions surface alongside IDs (User Story US-4).
5. **Documentation Surfaces**
   - Update `.tf/plans/.../00-design.md`, `README.md`, and `skills/tk-workflow/SKILL.md` with flow diagrams, flag matrix, and overlay controls (Ctrl+T/B/Q, `/sessions`, `/attach`). Chain definitions (`assets/chains/tk-path-*.chain.md`) remain untouched per guardrail.

## Components
| Component | Responsibility | Key Changes |
| --- | --- | --- |
| `prompts/tk-implement.md` | Collect CLI args, perform fast anchoring, orchestrate execution | Add interactive flag parsing, routing logic, `interactive_shell` invocations, and error messages. |
| `interactive_shell` tool | Provides interactive/hands-free/dispatch execution | Consume new parameters (`mode`, `background`, `handsFree` settings) and return `sessionId` back to the prompt layer. |
| `.subagent-runs/<ticket>/` artifacts | Persistent record of runs | Add `session.json` + log entries describing mode, `sessionId`, and user follow-up commands. |
| Documentation (`00-design.md`, `README.md`, `skills/tk-workflow/SKILL.md`) | Communicate functionality | Describe new flags, compatibility rules, overlay controls, and troubleshooting steps. |
| Existing Path A/B/C chains | Default execution flow | Remain unchanged but must stay reachable when no new flags are provided. |

## Data Flow
1. User invokes `/tk-implement <ticket> [flags]`.
2. Prompt parses flags and immediately validates combinations. Invalid combos throw before anchoring.
3. Prompt performs fast anchoring/context staging.
4. Router selects branch:
   - **Interactive/Hands-free/Dispatch**: prompt crafts a nested `pi "/tk-implement <ticket> [--clarify]"` command string, calls `interactive_shell` with mode-specific options, and captures the returned `sessionId` + status. The shell process runs the *same* CLI entrypoint but under pi’s overlay management, so any emitted artifacts still flow into `.subagent-runs/<ticket>/`.
   - **Legacy**: `subagent` executes the selected tk-path chain (A/B/C) as before.
5. Prompt writes/update `session.json` + run logs (interactive modes) or the usual chain outputs (legacy).
6. User can later run `/sessions` to list active overlays or `/attach <sessionId>` to rejoin, guided by the logged instructions.

## Error Handling
- **Flag Conflicts**: Validation matrix rejects combinations of multiple interactive flags, any interactive flag with `--async`, and `--interactive` with `--clarify`. Error messages follow the format `"Cannot combine --interactive with --async; use --hands-free/--dispatch if you need backgrounding."`
- **Missing Ticket / Command Construction Errors**: Guard the nested `pi` command builder so that missing ticket IDs or shell escaping issues raise clear exceptions before invoking `interactive_shell`.
- **Interactive Shell Failures**: Wrap `interactive_shell` calls in try/catch; on error, log the failure, emit remediation tips ("rerun without --dispatch"), and ensure no partial `session.json` is written.
- **Session Logging Failures**: If writing `session.json` fails, fall back to console warnings but continue execution; legacy flows must never be blocked by log persistence errors.

## Observability
- **Structured Session Logs**: `session.json` captures `mode`, `sessionId`, timestamps, and the nested command. Include optional `status` field updated when dispatch completes.
- **Console Breadcrumbs**: For every interactive run, print a standardized block: session ID, mode description, `/attach` instructions, overlay keybindings recap.
- **Hands-free Polling Visibility**: Ensure the hands-free branch sets `handsFree.updateInterval`/`quietThreshold` explicitly so pi emits periodic updates (PRD TD-2).
- **Dispatch Notifications**: Confirm dispatch runs rely on pi’s native notification system; document expected behavior and how to retrieve logs afterward.

## Testing Strategy
1. **Unit Tests (TD-1)**
   - Mock flag parser to cover: single valid flag, all invalid pairs, `--dispatch + --clarify` allowed, default path unaffected.
2. **Integration Tests / Manual Scripts (TD-2 & TD-3)**
   - Execute `/tk-implement <ticket> --interactive` and verify overlay, Ctrl+T/B/Q instructions, and `session.json` content.
   - Run `--hands-free` to confirm 60s cadence updates and manual takeover capability.
   - Run `--dispatch` and confirm background execution, notification, and ability to `/attach` later.
3. **Regression (TD-4)**
   - Rerun base `/tk-implement` and existing `--async`, `--clarify` flows to ensure Path A/B/C chains execute unchanged and artifact layouts match previous snapshots.
4. **Documentation Verification**
   - Cross-check README + skill updates against actual behavior (flag matrix, shortcuts, session commands).

## Rollout & Risks
- **Rollout Plan**
  1. Implement flag parsing + routing behind feature-complete state.
  2. Add session logging + documentation updates.
  3. Run integration smoke tests on a sample ticket.
  4. Publish updated docs and merge once PRD acceptance criteria are met.
- **Risks & Mitigations**
  - *Recursive Invocation Risk*: Guard nested `pi "/tk-implement ..."` command to detect already-interactive contexts (e.g., environment variable flag) and avoid infinite loops.
  - *Artifact Divergence*: Write tests ensuring interactive runs still populate `.subagent-runs/<ticket>/` as expected.
  - *User Confusion with Modes*: Provide clear docs + console hints differentiating `--interactive`, `--hands-free`, `--dispatch`.
  - *Dispatch Visibility*: Ensure logged session IDs persist even if notifications are missed; `/sessions` instructions must always be present.
