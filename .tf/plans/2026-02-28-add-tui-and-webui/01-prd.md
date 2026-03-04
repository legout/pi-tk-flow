# PRD: Add TUI and Optional Web UI

**Date**: 2026-02-28
**Status**: Draft
**Mode**: Feature

---

## Problem Statement

pi-tk-flow lacks visual tooling for ticket management. Users currently interact with tickets only through:
- The `tk` CLI (`tk ready`, `tk show`, `tk blocked`, `tk close`)
- Direct file editing of `tickets.yaml`
- Subagent-driven workflow prompts

This creates friction when:
- **Exploring ticket state** across multiple plans requires running multiple `tk` commands
- **Reviewing knowledge base** topics means navigating loose markdown files
- **Understanding dependencies** requires manual YAML parsing
- **Team members** prefer visual Kanban-style interfaces

## Solution

Adapt the reference Textual TUI from pi-tk-workflow with a new data layer for pi-tk-flow's storage format.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Approach** | Adapt reference code | 1423-line reference TUI is well-designed; UI layer is reusable |
| **Data Layer** | New loaders for YAML | pi-tk-flow uses `tickets.yaml`, not individual markdown files |
| **Status Source** | Query `tk` CLI on refresh | Single source of truth, avoids cache drift |
| **Topic Index** | Scan on-the-fly | No build step, simpler maintenance |
| **Web UI** | Via `textual serve` | Free with Textual framework |

### Package Structure

```
python/
├── pyproject.toml              # [ui] extra for optional deps
└── pi_tk_flow_ui/
    ├── app.py                  # Adapted TicketflowApp
    ├── ticket_loader.py        # YamlTicketLoader (new)
    ├── board_classifier.py     # BoardClassifier (reused)
    └── topic_scanner.py        # TopicScanner (new)
```

### Extension Command

```bash
/tf ui           # Launch terminal UI
/tf ui --web     # Print web command: textual serve "python -m pi_tk_flow_ui"
```

---

## User Stories

### US-1: Visual Kanban Board
**As a** developer using pi-tk-flow
**I want** to see all tickets in a Kanban board (Ready/Blocked/In Progress/Closed)
**So that** I can quickly understand project status at a glance

**Acceptance Criteria:**
- [ ] `/tf ui` displays 4-column Kanban layout
- [ ] Tickets grouped by status with dependency-aware classification
- [ ] Selected ticket shows full details in side panel
- [ ] Refresh (`r`) reloads ticket state from `tk` CLI

### US-2: Knowledge Topic Browser
**As a** developer
**I want** to browse knowledge topics grouped by type
**So that** I can discover relevant context without remembering file paths

**Acceptance Criteria:**
- [ ] Topics sidebar shows topics grouped by prefix (seed-, plan-, spike-, baseline-)
- [ ] Selecting a topic displays content in detail panel
- [ ] Key binding `o` opens topic in `$PAGER`
- [ ] No `index.json` required—topics scanned on load

### US-3: Ticket Filtering
**As a** developer with many tickets
**I want** to filter tickets by search, tag, and assignee
**So that** I can focus on relevant work

**Acceptance Criteria:**
- [ ] Search filters tickets by title/description
- [ ] Tag filter shows only tickets with selected tag
- [ ] Assignee filter shows tickets assigned to user
- [ ] Clear filters option available

### US-4: Quick Actions
**As a** developer
**I want** keyboard shortcuts for common actions
**So that** I can work efficiently without leaving the keyboard

**Acceptance Criteria:**
- [ ] `1-4` opens first documentation link in each category
- [ ] `o` opens primary documentation
- [ ] `e` opens ticket file in `$EDITOR`
- [ ] `r` refreshes ticket state
- [ ] `q` quits the application

### US-5: Web Access
**As a** remote developer
**I want** to access the UI via a web browser
**So that** I can manage tickets from any machine

**Acceptance Criteria:**
- [ ] `/tf ui --web` prints correct `textual serve` command
- [ ] Web UI functions identically to terminal UI
- [ ] Documentation explains web setup

### US-6: Optional Installation
**As a** minimal-install user
**I want** UI dependencies to be optional
**So that** I can use pi-tk-flow core without installing Textual

**Acceptance Criteria:**
- [ ] `pip install pi-tk-flow` works without UI deps
- [ ] `pip install pi-tk-flow[ui]` installs Textual
- [ ] Missing UI deps show helpful error message

---

## Implementation Decisions

### ID-1: Adapt Reference Code (Not Rewrite)
**Decision**: Port the reference TUI with a new data layer rather than building from scratch.
**Rationale**: The UI layer (widgets, CSS, bindings) is well-designed and generic. Only the data loaders need replacement.
**Alternatives Considered**: Fresh implementation would duplicate 1000+ lines of working UI code.

### ID-2: YAML Ticket Loader
**Decision**: Create `YamlTicketLoader` that parses `tickets.yaml` slices into `Ticket` objects.
**Rationale**: pi-tk-flow stores tickets in `tickets.yaml`, not individual markdown files.
**Mapping**:
- `slices[].key` → `Ticket.id`
- `slices[].title` → `Ticket.title`
- `slices[].blocked_by` → `Ticket.deps`
- Status queried from `tk` CLI

### ID-3: Topic Scanner (No Index File)
**Decision**: Scan `topics/*.md` files on load rather than maintaining `index.json`.
**Rationale**: Simpler maintenance, no build step, works with existing topic files.
**Trade-off**: Slightly slower startup with many topics (acceptable for knowledge base sizes).

### ID-4: tk CLI as Status Source
**Decision**: Query `tk status <id>` for ticket status rather than parsing local state.
**Rationale**: `tk` CLI is the single source of truth; avoids cache drift and sync issues.
**Implementation**: Cache status for session, refresh on `r` key.

### ID-5: Multi-Plan Aggregation
**Decision**: Aggregate tickets from all `.tf/plans/*/tickets.yaml` files.
**Rationale**: Users may have multiple active plans; showing all tickets in one view is more useful.
**Implementation**: Include plan name in ticket display.

### ID-6: Optional [ui] Extra
**Decision**: Make Textual an optional dependency via `[ui]` extra in pyproject.toml.
**Rationale**: Core pi-tk-flow should work without UI; not all users need visual tooling.

---

## Testing Decisions

### TD-1: Manual UI Testing
**Approach**: Manual testing via `/tf ui` launch and interaction verification.
**Rationale**: Textual TUIs are difficult to unit test; visual verification is practical.
**Coverage**:
- [ ] Kanban columns render correctly
- [ ] Topic browser loads and displays
- [ ] Filters work as expected
- [ ] Key bindings function correctly
- [ ] Web mode launches via `textual serve`

### TD-2: Data Loader Unit Tests
**Approach**: Unit tests for `YamlTicketLoader` and `TopicScanner`.
**Rationale**: Data transformation logic is well-suited to unit testing.
**Coverage**:
- [ ] Parse sample `tickets.yaml` correctly
- [ ] Handle missing files gracefully
- [ ] Extract topic metadata from markdown headers

### TD-3: Integration Test with Sample Plan
**Approach**: Create a sample plan with known tickets, verify UI displays correctly.
**Rationale**: End-to-end verification of data loading and display pipeline.

---

## Out of Scope

- **Ticket creation/editing via UI** — Use `tk` CLI or edit `tickets.yaml` directly
- **Real-time ticket sync** — Status refreshed on demand via `r` key
- **Mobile-responsive web UI** — Textual's web mode is desktop-oriented
- **Custom themes/styling** — Use default Textual styling initially
- **Ticket comments/threads** — Not in current ticket schema
- **Multiple knowledge bases** — Single `.tf/knowledge/` directory per project
- **Plugin system for UI extensions** — Future consideration if needed
- **Performance optimization for 1000+ tickets** — Expected use case is <100 tickets

---

## Success Metrics

1. **Launch Success**: `/tf ui` starts without errors after `[ui]` installation
2. **Visual Accuracy**: Kanban columns correctly classify tickets by status/dependencies
3. **Topic Discovery**: All knowledge topics visible and accessible
4. **Filter Correctness**: Filters narrow ticket list accurately
5. **Documentation**: README explains installation and usage clearly
