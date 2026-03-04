# Design Brief: Add TUI and Optional Web UI

**Feature**: Textual-based TUI for pi-tk-flow ticket management
**Mode**: Feature
**Date**: 2026-02-28

---

## Context

pi-tk-flow lacks visual tooling for ticket management. Users currently interact with tickets only through `tk` CLI commands, direct YAML editing, or subagent prompts. This creates friction when exploring ticket state across multiple plans or understanding dependencies.

**Solution**: Adapt the reference Textual TUI (1423 lines) from pi-tk-workflow with a new data layer for pi-tk-flow's `tickets.yaml` format. Web access comes free via `textual serve`.

**Key Insight**: The UI layer (widgets, CSS, bindings) is reusable; only data loaders need replacement.

---

## Chosen Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Extension Layer: /tf ui command (extensions/tf-ui.ts)          │
└────────────────────────────┬────────────────────────────────────┘
                             │ spawns
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Python Package (pi_tk_flow_ui/)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ TicketflowApp│  │TopicBrowser │  │ TicketBoard             │  │
│  │ (Textual App)│  │(Static)     │  │ (Static + filters)      │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                     │                 │
│         ▼                ▼                     ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │TopicScanner │  │YamlTicket   │  │ BoardClassifier         │  │
│  │ (new)       │  │Loader (new) │  │ (reuse from reference)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Data Sources: .tf/plans/*/tickets.yaml, topics/*.md, tk CLI    │
└─────────────────────────────────────────────────────────────────┘
```

**Technology**: Textual ^0.47.0, PyYAML ^6.0, Python ≥3.10

---

## Component Contracts

### C-1: Extension Command (`extensions/tf-ui.ts`)

```typescript
// Registers /tf ui [--web]
// Terminal: spawns `python -m pi_tk_flow_ui`
// Web: prints `textual serve "python -m pi_tk_flow_ui"`
```

### C-2: YamlTicketLoader

```python
@dataclass
class Ticket:
    id: str           # slices[].key
    title: str        # slices[].title
    body: str         # slices[].description (lazy load)
    status: str       # Queried from tk CLI
    deps: list[str]   # slices[].blocked_by
    tags: list[str]   # slices[].tags
    priority: int     # slices[].priority
    ticket_type: str  # slices[].type
    plan_name: str    # Derived from directory
    plan_dir: str     # Full path to plan

class YamlTicketLoader:
    def load_all() -> list[Ticket]      # All plans
    def refresh_status(id) -> str       # Query tk CLI
```

### C-3: BoardClassifier

```python
class BoardColumn(Enum):
    READY = "ready"           # status=open, no blockers
    BLOCKED = "blocked"       # has unclosed deps
    IN_PROGRESS = "in_progress"  # status=in_progress
    CLOSED = "closed"         # status=closed

class BoardClassifier:
    def classify(tickets) -> list[ClassifiedTicket]
```

### C-4: TopicScanner

```python
@dataclass
class Topic:
    path: Path
    title: str        # First # heading
    topic_type: str   # seed|plan|spike|baseline|other

class TopicScanner:
    def scan() -> list[Topic]
    def group_by_type() -> dict[str, list[Topic]]
```

### C-5: TicketflowApp

```python
class TicketflowApp(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("o", "open_primary_doc", "Open doc"),
        ("e", "open_in_editor", "Edit"),
        ("1-4", "open_doc_N", "Open PRD/Spec/Plan/Progress"),
    ]
```

---

## Key Flows

### Startup
```
/tf ui → python -m pi_tk_flow_ui → TicketflowApp.run()
    → TopicBrowser.on_mount() → TopicScanner.scan() → topics/*.md
    → TicketBoard.on_mount() → YamlTicketLoader.load_all()
        → Parse tickets.yaml → Query tk status → BoardClassifier
```

### Refresh (r key)
```
action_refresh() → YamlTicketLoader.refresh_status() per ticket
    → subprocess(["tk", "show", id, "--format", "json"])
    → BoardClassifier.classify() → Re-render
```

### Open Document (1-4 keys)
```
action_open_doc_N() → Resolve .tf/plans/NAME/0N-*.md path
    → app.suspend() → os.system($PAGER path) → Resume
```

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Textual API changes | Low | High | Pin version ^0.47.0 |
| tk CLI interface changes | Low | High | Document interface, add version check |
| Performance with many tickets | Medium | Medium | Lazy body loading, status caching |
| Dependency conflicts | Low | Medium | Optional `[ui]` extra |
| Web mode compatibility | Medium | Low | Test browsers, document limitations |

**Rollback**: Remove extension from `package.json`; core pi-tk-flow works without UI.

---

## Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| D-1 | Adapt reference code | 1000+ lines of working UI code; only data layer changes |
| D-2 | YAML ticket loader | pi-tk-flow uses `tickets.yaml`, not `.tickets/*.md` |
| D-3 | tk CLI as status source | Single source of truth; avoid cache drift |
| D-4 | Scan topics on-the-fly | No build step, no index.json to maintain |
| D-5 | Multi-plan aggregation | Show all tickets in one view; include plan name |
| D-6 | Optional [ui] extra | Core works without UI dependencies |

---

## File Manifest

**New**:
```
python/
├── pyproject.toml              # [ui] extra for textual, pyyaml
└── pi_tk_flow_ui/
    ├── __init__.py
    ├── __main__.py             # Entry point
    ├── app.py                  # TicketflowApp, TicketBoard, TopicBrowser
    ├── ticket_loader.py        # YamlTicketLoader
    ├── board_classifier.py     # BoardClassifier
    ├── topic_scanner.py        # TopicScanner
    └── styles.tcss             # CSS

extensions/tf-ui.ts              # /tf ui command
tests/fixtures/sample_project/   # Test data
tests/test_*.py                  # Unit tests
```

**Modified**:
- `package.json` — add extension to pi.extensions
- `README.md` — document UI installation and usage

---

## Success Criteria

1. `/tf ui` launches TUI showing Kanban board with tickets from all plans
2. Topic browser shows all knowledge topics grouped by type
3. Filters work (search, tag, assignee)
4. Key bindings work (1-4 docs, o primary, e editor, r refresh, q quit)
5. `/tf ui --web` prints correct `textual serve` command
6. Installation documented with optional `[ui]` extra
7. Unit test coverage ≥80% for data layer
