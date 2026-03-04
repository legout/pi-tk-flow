# Design: Ralph Wiggum Method Implementation

## Context
- `/tk-implement` only supports foreground (default) or fire-and-forget (`--async`) execution, leaving users without real-time visibility, takeover controls, or reliable session reattachment.
- Product requirements introduce three mutually exclusive execution flags—`--interactive`, `--hands-free`, `--dispatch`—that must coexist with existing `--async`/`--clarify` semantics and preserve the current anchoring + Path A/B/C chain flows when the new flags are absent.
- Guardrails constrain the work to prompt + documentation updates (no agent definition changes, no edits to `assets/chains/**`). All runs must continue writing artifacts under `.subagent-runs/<ticket>/` to keep `tk-close` and audits unaffected.
- Documentation surfaces (`.tf/plans/.../00-design.md`, `README.md`, `skills/tk-workflow/SKILL.md`) must explicitly describe mode semantics, shortcut affordances (Ctrl+T/B/Q), `/sessions`, `/attach`, and the compatibility matrix so users understand when to choose each mode.

## Chosen Architecture
1. **Flag Parsing & Validation** (in `prompts/tk-implement.md`)
   - Extend the existing CLI flag block to recognize the three new flags.
   - Enforce exclusivity: only one of the new flags at a time; none can combine with `--async`; `--interactive` cannot pair with `--clarify`, while `--dispatch` may.
   - Emit actionable errors before anchoring when invalid combinations appear.
2. **Fast Anchoring (unchanged)**
   - Always perform the current anchoring/context build so that downstream execution—interactive or legacy—has the same knowledge snapshot.
3. **Execution Router**
   - Immediately after anchoring, branch:
     - **Interactive** → call `interactive_shell` with `mode: "interactive"` and command `pi "/tk-implement <ticket> [--clarify=…]"`.
     - **Hands-Free** → same command, `mode: "hands-free"`, with explicit `handsFree` config (`updateMode: "on-quiet"`, `quietThreshold≈8000ms`, `updateInterval≈60000ms`).
     - **Dispatch** → `interactive_shell` `mode: "dispatch"`, `background: true`, rely on auto notifications.
     - **Legacy** → fall through to existing Path A/B/C `subagent` chains when no interactive flag is set.
   - Guard against recursive invocation by tagging the nested command (e.g., env var) and no-op if it re-enters the router with the tag set.
4. **Session Metadata**
   - For interactive branches, persist `session.json` in `.subagent-runs/<ticket>/` capturing `mode`, `sessionId`, timestamps, command, and eventual completion status.
   - Append a console + log breadcrumb block that repeats the session ID and `/attach`/`/sessions` guidance so users can rejoin later.
5. **Documentation + Spec Alignment**
   - Update `.tf/plans/.../00-design.md` (this file), `README.md`, and `skills/tk-workflow/SKILL.md` with the mode matrix, keyboard shortcuts, compatibility rules, and troubleshooting tips.

## Component Contracts
| Component | Inputs | Outputs / Guarantees |
| --- | --- | --- |
| `prompts/tk-implement.md` | CLI args (`ticket`, `--async`, `--clarify`, new flags); repo context | Validated flag matrix, fast anchoring, routing decision, invocation of `interactive_shell` or legacy chains. Emits human-friendly errors on invalid combos. |
| `interactive_shell` tool (invoked by prompt) | `command`, `mode`, optional `background`, `handsFree` struct | Launches nested `pi "/tk-implement ..."` session; returns `sessionId`, status metadata, and streams output per mode. |
| `.subagent-runs/<ticket>/session.json` (new) | Session metadata produced by interactive runs | Structured log consumed by `/attach`, `/sessions`, and audits; schema `{mode, sessionId, startedAt, command, status?}`. |
| Existing Path A/B/C chains | Ticket context, clarify/async flags | Remain untouched; receive execution only when no interactive flag is present, ensuring backward compatibility. |
| Documentation surfaces (`README.md`, `skills/tk-workflow/SKILL.md`) | Finalized behavior + guardrails | User-facing explanations of when/how to use each mode, shortcut cheatsheet, session management instructions. |

## Key Flows
1. **Interactive Supervision (`--interactive`)**
   1. User invokes `/tk-implement <ticket> --interactive`.
   2. Prompt validates the flag, performs anchoring, and short-circuits chains.
   3. `interactive_shell` runs with live overlay; user can Ctrl+T/B/Q. Session ID + instructions logged to console and `session.json`.
2. **Hands-Free Monitoring (`--hands-free`)**
   1. Same as above but `mode: hands-free`, explicit polling cadence so pi emits ~60s updates.
   2. User may take control by typing; session metadata identical.
3. **Dispatch Backgrounding (`--dispatch` [+ optional `--clarify`])**
   1. Clarify (if requested) still runs before dispatch branch.
   2. Router calls `interactive_shell` `mode: dispatch`, `background: true`; returns `sessionId` immediately and relies on pi notifications.
   3. `session.json` notes `status: pending` until completion callback updates it.
4. **Legacy Chains (default / `--async` / `--clarify`)**
   1. If no interactive flag, router defers to existing Path A/B/C selection logic.
   2. `--async` continues to use `subagent` `async: true`; `--clarify` continues to gate chain launch with the existing TUI.

## Risks
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Recursive nested `pi "/tk-implement"` calls leading to infinite loops | Run failure | Inject env flag (e.g., `PI_TK_INTERACTIVE_CHILD=1`) and skip router logic when set. |
| Divergent artifacts between interactive and legacy runs | Downstream tooling breaks | Enforce `.subagent-runs/<ticket>/` as the write location for all session metadata; add tests verifying file presence. |
| User confusion between `--async` and `--dispatch` | Misused flags | Update docs + console hints clarifying `--dispatch` = background + notification while `--async` remains legacy fire-and-forget. |
| Hands-free polling overwhelms logs or violates tool limits | Noise / throttling | Use documented defaults (`updateMode: on-quiet`, `updateInterval≈60s`, `quietThreshold≈8s`) and expose configuration constants for tuning. |
| Failure to write `session.json` causes silent loss of reattach info | Hard to resume sessions | Wrap writes in try/catch; on failure, emit warning instructing user to rely on console session ID blurb. |

## Decisions
1. **Adopt Flag-Based Extension (Option B)**: Integrate interactive modes directly into `/tk-implement` rather than creating new commands/scripts, preserving user muscle memory and minimizing surface area.
2. **Single-Entry Anchoring**: Even interactive runs must execute the same anchoring block to guarantee consistent context and artifact placement.
3. **Strict Flag Matrix**: Mutual exclusivity between the new flags and legacy `--async`, plus `--interactive` vs `--clarify` incompatibility, prevents ambiguous UX and aligns with PRD ID-1.
4. **Session Logging Standardization**: Introduce `session.json` + console breadcrumbs so `/sessions`/`/attach` workflows have canonical metadata (fulfills PRD US-4).
5. **Documentation as Acceptance Gate**: Treat README + skill updates as part of the feature definition so users receive explicit instructions on overlays, keyboard shortcuts, and compatibility rules.
