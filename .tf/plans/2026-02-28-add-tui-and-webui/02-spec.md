# Technical Spec: Add TUI and Optional Web UI

**Date**: 2026-02-28
**Status**: Draft
**Parent PRD**: `01-prd.md`

---

## Architecture

### Overview

The TUI adapts the reference Textual implementation from pi-tk-workflow with a new data layer for pi-tk-flow's YAML-based ticket storage. The architecture follows a clean separation between data loading, business logic, and presentation.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Extension Layer                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  extensions/tf-ui.ts                                         │    │
│  │  - Registers /tf ui command                                  │    │
│  │  - Spawns Python process (terminal or web mode)              │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Python Package                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  pi_tk_flow_ui/app.py (TicketflowApp)                        │    │
│  │  - Textual application root                                  │    │
│  │  - TabbedContent: TopicBrowser | TicketBoard                 │    │
│  │  - CSS styling, key bindings                                 │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│              ┌───────────────┴───────────────┐                       │
│              ▼                               ▼                       │
│  ┌─────────────────────┐         ┌─────────────────────┐            │
│  │  TopicBrowser       │         │  TicketBoard        │            │
│  │  - Sidebar list     │         │  - 4-column Kanban  │            │
│  │  - Detail panel     │         │  - Detail panel     │            │
│  │  - Group by type    │         │  - Filter controls  │            │
│  └─────────────────────┘         └─────────────────────┘            │
│              │                               │                       │
│              ▼                               ▼                       │
│  ┌─────────────────────┐         ┌─────────────────────┐            │
│  │  TopicScanner       │         │  YamlTicketLoader   │            │
│  │  - Scan topics/*.md │         │  - Parse YAML       │            │
│  │  - Extract metadata │         │  - Query tk CLI     │            │
│  └─────────────────────┘         └─────────────────────┘            │
│                                          │                          │
│                                          ▼                          │
│                              ┌─────────────────────┐                │
│                              │  BoardClassifier    │                │
│                              │  - Classify tickets │                │
│                              │  - Handle deps      │                │
│                              └─────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Sources                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │  tickets.yaml   │  │  topics/*.md    │  │  tk CLI         │      │
│  │  (per plan)     │  │  (knowledge)    │  │  (status)       │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Code Reuse** | Adapt reference TUI | 1423-line reference is well-designed; UI layer reusable |
| **Data Layer** | New loaders for YAML | pi-tk-flow uses `tickets.yaml`, not `.tickets/*.md` |
| **Status Source** | Query `tk` CLI | Single source of truth, avoids cache drift |
| **Topic Index** | Scan on-the-fly | No build step, simpler maintenance |
| **Web UI** | `textual serve` | Free with Textual framework |

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Extension | TypeScript (pi SDK) | Current |
| TUI Framework | Textual | ^0.47.0 |
| YAML Parsing | PyYAML | ^6.0 |
| CLI Integration | subprocess | stdlib |
| Python | CPython | ≥3.10 |

---

## Components

### C-1: Extension Command (`extensions/tf-ui.ts`)

**Purpose**: Registers `/tf ui` command with pi extension API.

**Interface**:
```typescript
interface TfUiCommand {
  description: string;
  handler: (args: string[], ctx: ExtensionContext) => Promise<void>;
}
```

**Behavior**:
- Parses `--web` flag from args
- Constructs Python command:
  - Terminal: `python -m pi_tk_flow_ui`
  - Web: `textual serve "python -m pi_tk_flow_ui"`
- Spawns process with inherited stdio (terminal) or prints command (web)
- Handles process lifecycle (cleanup on exit)

**Error Handling**:
- Missing Python: Display installation instructions
- Missing `pi_tk_flow_ui`: Suggest `pip install -e ./python[ui]`
- Process failure: Log error, display user-friendly message

### C-2: TicketflowApp (`python/pi_tk_flow_ui/app.py`)

**Purpose**: Main Textual application root.

**Responsibilities**:
- Define application structure (Header, TabbedContent, Footer)
- Register key bindings (`q`, `r`, `o`, `e`, `1-4`)
- Load CSS styling
- Coordinate child widgets

**Key Bindings**:

| Key | Action | Description |
|-----|--------|-------------|
| `q` | `app.quit` | Exit application |
| `r` | `app.refresh` | Reload all data |
| `o` | `app.open_primary_doc` | Open primary documentation |
| `e` | `app.open_in_editor` | Open current item in `$EDITOR` |
| `1` | `app.open_doc_1` | Open PRD |
| `2` | `app.open_doc_2` | Open Spec |
| `3` | `app.open_doc_3` | Open Plan |
| `4` | `app.open_doc_4` | Open Progress |

**State**:
```python
class TicketflowApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [...]
    
    # Reactive state
    current_plan_dir: reactive[str] = reactive("")
    selected_ticket_id: reactive[str | None] = reactive(None)
    selected_topic_path: reactive[str | None] = reactive(None)
```

### C-3: TicketBoard (`python/pi_tk_flow_ui/app.py`)

**Purpose**: Kanban board widget displaying classified tickets.

**Responsibilities**:
- Display tickets in 4 columns (Ready, Blocked, In Progress, Closed)
- Handle ticket selection
- Apply filters (search, tag, assignee)
- Show ticket details in side panel

**Props/State**:
```python
class TicketBoard(Static):
    # Filter state
    search_query: reactive[str] = reactive("")
    selected_tag: reactive[str | None] = reactive(None)
    selected_assignee: reactive[str | None] = reactive(None)
    
    # Data
    tickets: list[ClassifiedTicket] = []
```

**Rendering**:
```
┌────────────────────────────────────────────────────────────────────┐
│ [Search: _______] [Tag: All ▼] [Assignee: All ▼]                  │
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│   READY (3)  │  BLOCKED (1) │ IN PROGRESS  │      CLOSED (5)      │
├──────────────┼──────────────┼──────────────┼──────────────────────┤
│ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │ ┌──────────────────┐ │
│ │ S1: Add  │ │ │ S3: Auth │ │ │ S2: API  │ │ │ E1: Setup proj   │ │
│ │ filters  │ │ │ (→S2)    │ │ │ endpoint │ │ │                  │ │
│ └──────────┘ │ └──────────┘ │ └──────────┘ │ └──────────────────┘ │
│ ┌──────────┐ │              │              │ ┌──────────────────┐ │
│ │ S4: Test │ │              │              │ │ S0: Initial work │ │
│ │ suite    │ │              │              │ └──────────────────┘ │
│ └──────────┘ │              │              │                      │
└──────────────┴──────────────┴──────────────┴──────────────────────┘
```

### C-4: TopicBrowser (`python/pi_tk_flow_ui/app.py`)

**Purpose**: Knowledge base topic browser.

**Responsibilities**:
- Display topics grouped by type prefix
- Show topic content in detail panel
- Handle topic selection and navigation

**Topic Grouping**:
- `seed-*` → Seeds (project scaffolding)
- `plan-*` → Planning guides
- `spike-*` → Spike solutions
- `baseline-*` → Baseline patterns
- Other → Miscellaneous

**Rendering**:
```
┌────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────┐ ┌────────────────────────────────────────┐ │
│ │ TOPICS              │ │ TOPIC DETAIL                          │ │
│ │                     │ │                                        │ │
│ │ ▼ Seeds             │ │ # plan-implementation-workflow         │ │
│ │   seed-project      │ │                                        │ │
│ │   seed-python       │ │ This topic describes the standard      │ │
│ │                     │ │ implementation workflow for tk-driven  │ │
│ │ ▼ Planning          │ │ development...                         │ │
│ │   plan-impl-workflow│ │                                        │ │
│ │   plan-review-cycle │ │ ## Key Steps                           │ │
│ │                     │ │ 1. Run `/tk-plan` to generate plan     │ │
│ │ ▼ Spikes            │ │ 2. Run `/tk-ticketize` to create tickets│ │
│ │   spike-auth-flow   │ │ 3. Run `/tk-implement <id>` to execute  │ │
│ └─────────────────────┘ └────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### C-5: YamlTicketLoader (`python/pi_tk_flow_ui/ticket_loader.py`)

**Purpose**: Parse `tickets.yaml` files and produce `Ticket` objects.

**Interface**:
```python
@dataclass
class Ticket:
    id: str
    title: str
    body: str
    status: str  # open, in_progress, closed
    deps: list[str]
    tags: list[str]
    assignee: str | None
    priority: int
    ticket_type: str  # feature, bug, chore, epic
    plan_name: str
    plan_dir: str
    
    _body_path: str | None = field(default=None, repr=False)
    
    def load_body(self) -> str:
        """Lazily load body content."""
        ...

class YamlTicketLoader:
    def __init__(self, tf_dir: Path):
        self.tf_dir = tf_dir
        self._status_cache: dict[str, str] = {}
    
    def load_all(self) -> list[Ticket]:
        """Load tickets from all plan directories."""
        ...
    
    def load_plan(self, plan_dir: Path) -> list[Ticket]:
        """Load tickets from a single plan directory."""
        ...
    
    def refresh_status(self, ticket_id: str) -> str:
        """Query tk CLI for current status."""
        ...
```

**YAML Mapping**:
```yaml
# Input (tickets.yaml)
slices:
  - key: S1
    title: "Add filters"
    description: |
      Implement search and tag filters
    blocked_by: [S3]
    tags: [feature, ui]
    priority: 2
    type: feature

# Output (Ticket)
Ticket(
    id="S1",
    title="Add filters",
    body="Implement search and tag filters\n",
    status="open",  # Queried from tk CLI
    deps=["S3"],
    tags=["feature", "ui"],
    priority=2,
    ticket_type="feature"
)
```

**Status Query**:
```python
def _query_status(self, ticket_id: str) -> str:
    """Query tk CLI for ticket status."""
    result = subprocess.run(
        ["tk", "show", ticket_id, "--format", "json"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return data.get("status", "open")
    return "open"  # Default fallback
```

### C-6: BoardClassifier (`python/pi_tk_flow_ui/board_classifier.py`)

**Purpose**: Classify tickets into Kanban columns.

**Interface**:
```python
class BoardColumn(Enum):
    READY = "ready"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

@dataclass
class ClassifiedTicket:
    ticket: Ticket
    column: BoardColumn

class BoardClassifier:
    def __init__(self, tickets: list[Ticket]):
        self.tickets = tickets
        self._ticket_map = {t.id: t for t in tickets}
    
    def classify(self) -> list[ClassifiedTicket]:
        """Classify all tickets into columns."""
        ...
    
    def classify_one(self, ticket: Ticket) -> BoardColumn:
        """Classify a single ticket."""
        ...
    
    def get_blocking_deps(self, ticket: Ticket) -> list[str]:
        """Get unresolved dependencies for a ticket."""
        ...
```

**Classification Logic**:
```python
def classify_one(self, ticket: Ticket) -> BoardColumn:
    if ticket.status == "closed":
        return BoardColumn.CLOSED
    
    blocking = self.get_blocking_deps(ticket)
    if blocking:
        return BoardColumn.BLOCKED
    
    if ticket.status == "in_progress":
        return BoardColumn.IN_PROGRESS
    
    return BoardColumn.READY

def get_blocking_deps(self, ticket: Ticket) -> list[str]:
    unresolved = []
    for dep_id in ticket.deps:
        dep = self._ticket_map.get(dep_id)
        if dep and dep.status != "closed":
            unresolved.append(dep_id)
    return unresolved
```

### C-7: TopicScanner (`python/pi_tk_flow_ui/topic_scanner.py`)

**Purpose**: Scan knowledge base topics on-the-fly.

**Interface**:
```python
@dataclass
class Topic:
    path: Path
    title: str
    topic_type: str  # seed, plan, spike, baseline, other
    relative_path: str

class TopicScanner:
    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
    
    def scan(self) -> list[Topic]:
        """Scan all topic files."""
        ...
    
    def group_by_type(self, topics: list[Topic]) -> dict[str, list[Topic]]:
        """Group topics by type prefix."""
        ...
    
    def _extract_title(self, path: Path) -> str:
        """Extract title from first # heading."""
        ...
    
    def _classify_type(self, filename: str) -> str:
        """Determine topic type from filename prefix."""
        ...
```

**Type Classification**:
```python
def _classify_type(self, filename: str) -> str:
    prefix = filename.split("-")[0]
    type_map = {
        "seed": "seed",
        "plan": "plan",
        "spike": "spike",
        "baseline": "baseline",
    }
    return type_map.get(prefix, "other")
```

### C-8: Package Configuration (`python/pyproject.toml`)

**Purpose**: Define Python package with optional UI dependencies.

```toml
[project]
name = "pi-tk-flow-ui"
version = "0.1.0"
description = "TUI for pi-tk-flow ticket management"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
ui = [
    "textual>=0.47.0",
    "pyyaml>=6.0",
]

[project.scripts]
tf-ui = "pi_tk_flow_ui:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Data Flow

### D-1: Application Startup

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  /tf ui      │────▶│  __main__.py │────▶│ TicketflowApp│
│  (pi ext)    │     │  (entry pt)  │     │  .run()      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                    ┌─────────────────────────────┘
                    ▼
           ┌──────────────────┐
           │ app.on_mount()   │
           └────────┬─────────┘
                    │
    ┌───────────────┴───────────────┐
    ▼                               ▼
┌─────────────┐            ┌─────────────────┐
│ TopicBrowser│            │   TicketBoard   │
│ .on_mount() │            │   .on_mount()   │
└──────┬──────┘            └────────┬────────┘
       │                            │
       ▼                            ▼
┌─────────────┐            ┌─────────────────┐
│TopicScanner │            │YamlTicketLoader │
│ .scan()     │            │ .load_all()     │
└──────┬──────┘            └────────┬────────┘
       │                            │
       ▼                            ▼
┌─────────────┐            ┌─────────────────┐
│topics/*.md  │            │ tickets.yaml    │
│ (scan FS)   │            │ + tk CLI status │
└─────────────┘            └─────────────────┘
```

### D-2: Ticket Refresh Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User presses│────▶│  app.action_ │────▶│ Emit refresh │
│  'r'         │     │  refresh()   │     │ message      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                    ┌─────────────────────────────┘
                    ▼
           ┌──────────────────┐
           │ TicketBoard      │
           │ .on_refresh()    │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ YamlTicketLoader │
           │ .refresh_status()│
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐     ┌──────────────┐
           │ tk show <id>     │────▶│ Parse JSON   │
           │ (subprocess)     │     │ response     │
           └──────────────────┘     └──────────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ Update ticket    │
           │ status in memory │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ BoardClassifier  │
           │ .classify()      │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ Re-render board  │
           │ columns          │
           └──────────────────┘
```

### D-3: Filter Application Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ User types   │────▶│ SearchInput  │────▶│ Update       │
│ in search    │     │ .on_change() │     │ search_query │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                    ┌─────────────────────────────┘
                    ▼
           ┌──────────────────┐
           │ _apply_filters() │
           └────────┬─────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌─────────┐  ┌───────────┐  ┌─────────────┐
│ Search  │  │ Tag filter│  │Assignee     │
│ match   │  │ match     │  │filter match │
└────┬────┘  └─────┬─────┘  └──────┬──────┘
     │             │               │
     └─────────────┴───────────────┘
                   │
                   ▼
          ┌────────────────┐
          │ Filtered ticket│
          │ list           │
          └───────┬────────┘
                  │
                  ▼
          ┌────────────────┐
          │ Re-render      │
          │ columns        │
          └────────────────┘
```

### D-4: Document Open Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ User presses │────▶│ app.action_  │────▶│ Resolve doc  │
│ '1' (PRD)    │     │ open_doc_1() │     │ path         │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                    ┌─────────────────────────────┘
                    ▼
           ┌──────────────────┐
           │ Find plan dir    │
           │ from selected    │
           │ ticket           │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ Resolve path:    │
           │ .tf/plans/NAME/  │
           │ 01-prd.md        │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐     ┌──────────────┐
           │ app.suspend()    │────▶│ os.system(   │
           │ (pause TUI)      │     │  $PAGER path)│
           └──────────────────┘     └──────────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ Resume TUI       │
           │ on exit          │
           └──────────────────┘
```

---

## Error Handling

### E-1: Missing Python Installation

**Detection**: Extension spawns `python --version` check on first run.

**User Message**:
```
Error: Python 3.10+ is required for the TUI.
Install Python: https://www.python.org/downloads/
```

**Recovery**: User must install Python manually; command exits gracefully.

### E-2: Missing UI Dependencies

**Detection**: Import error when loading `pi_tk_flow_ui`.

**User Message**:
```
Error: UI dependencies not installed.
Run: pip install -e ./python[ui]
Or: uv pip install -e ./python[ui]
```

**Recovery**: User installs dependencies; command works on next run.

### E-3: Missing tickets.yaml

**Detection**: `YamlTicketLoader` finds no `tickets.yaml` files.

**Behavior**:
- Display empty board with message: "No tickets found. Create a plan with `/tk-plan` first."
- Do not crash; allow topic browsing to continue

### E-4: Corrupt YAML

**Detection**: `yaml.safe_load()` raises exception.

**User Message**:
```
Warning: Could not parse .tf/plans/my-plan/tickets.yaml
Error: [YAML error details]
Some tickets may not appear in the board.
```

**Recovery**:
- Log warning, skip corrupt file
- Continue loading other plans

### E-5: tk CLI Failure

**Detection**: `subprocess.run(["tk", ...])` returns non-zero exit code.

**Behavior**:
- Default to `status="open"` for affected ticket
- Log warning: "Could not query status for S1, defaulting to open"
- Continue operation

### E-6: Missing Knowledge Directory

**Detection**: `TopicScanner` finds no `.tf/knowledge/topics/` directory.

**Behavior**:
- Display empty topic list with message: "No knowledge topics found."
- Do not crash; allow ticket browsing to continue

### E-7: External Editor Failure

**Detection**: `os.system($EDITOR)` fails or editor not set.

**User Message**:
```
Error: Could not open editor.
Set $EDITOR environment variable or use 'o' to open in pager.
```

**Recovery**: User fixes environment; command available on next attempt.

### Error Handling Summary

| Error Code | Condition | User Message | Recovery |
|------------|-----------|--------------|----------|
| E-1 | No Python | Install instructions | Manual install |
| E-2 | No UI deps | pip install command | Manual install |
| E-3 | No tickets | Empty board message | Create plan |
| E-4 | Corrupt YAML | Warning + skip | Fix YAML |
| E-5 | tk CLI fail | Default to open | Fix tk CLI |
| E-6 | No knowledge | Empty topics message | N/A |
| E-7 | No editor | Set $EDITOR | Manual fix |

---

## Observability

### O-1: Logging

**Framework**: Python `logging` module

**Log Levels**:
- `DEBUG`: Data loading details, filter operations
- `INFO`: Application lifecycle events
- `WARNING`: Recoverable errors (missing files, CLI failures)
- `ERROR`: Unrecoverable errors (import failures)

**Log Format**:
```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

**Log Output**:
- Terminal UI: Suppress logs (would interfere with display)
- Web UI: Log to file `~/.pi-tk-flow-ui.log`
- Debug mode: `TF_UI_DEBUG=1` enables console logging

### O-2: Performance Metrics

**Tracked Metrics**:
| Metric | Description | Target |
|--------|-------------|--------|
| `startup_time_ms` | Time from launch to first render | <500ms |
| `ticket_load_time_ms` | Time to load all tickets | <200ms |
| `status_query_time_ms` | Time per tk CLI query | <100ms |
| `topic_scan_time_ms` | Time to scan knowledge base | <100ms |
| `refresh_time_ms` | Time for full refresh | <500ms |

**Collection**: Simple timing via `time.perf_counter()`; logged at DEBUG level.

### O-3: Crash Reporting

**Approach**: Textual's built-in exception handling

**Behavior**:
- Unhandled exceptions display in TUI error screen
- Error includes stack trace and suggestion to report
- No automatic telemetry (privacy)

### O-4: Debug Mode

**Activation**: `TF_UI_DEBUG=1 /tf ui`

**Additional Features**:
- Console logging enabled
- Performance metrics logged
- Verbose data loading output
- Textual debug console (Ctrl+D)

---

## Testing Strategy

### T-1: Unit Tests (Data Layer)

**Scope**: `YamlTicketLoader`, `TopicScanner`, `BoardClassifier`

**Framework**: pytest

**Test Cases**:

```python
# test_ticket_loader.py
def test_load_empty_plan(tmp_path):
    """Loading an empty plan returns no tickets."""
    ...
    
def test_load_sample_plan(sample_plan_dir):
    """Loading a sample plan parses all slices correctly."""
    ...
    
def test_yaml_mapping(sample_yaml):
    """YAML fields map correctly to Ticket attributes."""
    ...

def test_status_query(mocker):
    """Status is queried from tk CLI correctly."""
    ...

# test_topic_scanner.py
def test_scan_empty_directory(tmp_path):
    """Scanning empty directory returns no topics."""
    ...

def test_extract_title(sample_topic):
    """Title extracted from first # heading."""
    ...

def test_classify_type():
    """Filename prefix determines topic type."""
    ...

# test_board_classifier.py
def test_classify_closed_ticket():
    """Closed tickets go to CLOSED column."""
    ...

def test_classify_blocked_ticket():
    """Tickets with unclosed deps go to BLOCKED."""
    ...

def test_classify_ready_ticket():
    """Open tickets without blockers go to READY."""
    ...
```

**Coverage Target**: ≥80% for data layer modules

### T-2: Integration Tests

**Scope**: Full data loading pipeline

**Test Cases**:

```python
# test_integration.py
def test_full_load(sample_project):
    """Load all tickets from sample project."""
    loader = YamlTicketLoader(sample_project / ".tf")
    tickets = loader.load_all()
    assert len(tickets) > 0
    
def test_classifier_integration(sample_tickets):
    """Classifier works with loaded tickets."""
    classifier = BoardClassifier(sample_tickets)
    classified = classifier.classify()
    assert all(c.column in BoardColumn for c in classified)

def test_topic_browser_loads(sample_knowledge):
    """Topic browser loads all topics."""
    scanner = TopicScanner(sample_knowledge)
    topics = scanner.scan()
    assert len(topics) > 0
```

### T-3: Manual UI Tests

**Scope**: Visual and interactive verification

**Test Checklist**:

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|-----------------|
| M-1 | Launch TUI | `/tf ui` | Board displays with tickets |
| M-2 | Refresh tickets | Press `r` | Status reloaded from tk CLI |
| M-3 | Search filter | Type in search box | Tickets filtered |
| M-4 | Tag filter | Select tag from dropdown | Tickets filtered |
| M-5 | Select ticket | Click ticket in board | Details shown in panel |
| M-6 | Open doc | Press `1` | PRD opens in pager |
| M-7 | Open editor | Press `e` | Ticket opens in editor |
| M-8 | Browse topics | Click Topics tab | Topic list displayed |
| M-9 | Select topic | Click topic | Content shown in panel |
| M-10 | Quit | Press `q` | Application exits |
| M-11 | Web mode | `/tf ui --web` | Command printed |

### T-4: Sample Project

**Purpose**: Provide known-good data for testing

**Structure**:
```
tests/fixtures/sample_project/
├── .tf/
│   ├── plans/
│   │   └── sample-plan/
│   │       ├── 01-prd.md
│   │       ├── 02-spec.md
│   │       ├── 03-plan.md
│   │       ├── 04-progress.md
│   │       └── tickets.yaml
│   └── knowledge/
│       └── topics/
│           ├── seed-project.md
│           ├── plan-impl-workflow.md
│           └── spike-auth.md
```

**tickets.yaml**:
```yaml
epic:
  title: "Sample Epic"
  type: epic
  description: "A sample epic for testing"
  tags: [testing]

slices:
  - key: S1
    title: "First slice"
    type: feature
    priority: 1
    tags: [feature, core]
    description: "First implementation slice"
    blocked_by: []
    
  - key: S2
    title: "Second slice"
    type: feature
    priority: 2
    tags: [feature, deps]
    description: "Depends on S1"
    blocked_by: [S1]
```

---

## Rollout & Risks

### R-1: Phased Rollout

**Phase 1: Core Package (Week 1)**
- Create Python package structure
- Implement `YamlTicketLoader`, `TopicScanner`, `BoardClassifier`
- Add unit tests for data layer
- Manual testing with sample project

**Phase 2: UI Integration (Week 2)**
- Port `TicketflowApp` from reference
- Implement `TicketBoard` and `TopicBrowser`
- Add CSS styling
- Manual UI testing

**Phase 3: Extension Integration (Week 3)**
- Create `extensions/tf-ui.ts`
- Register `/tf ui` command
- Test with pi runtime
- Documentation

**Phase 4: Polish & Release (Week 4)**
- Performance optimization
- Error message refinement
- Final documentation
- Release notes

### R-2: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Textual API changes | Low | High | Pin version, test on upgrade |
| tk CLI interface changes | Low | High | Document expected interface, add version check |
| Performance with many tickets | Medium | Medium | Lazy loading, pagination if needed |
| Web mode compatibility issues | Medium | Low | Test in common browsers, document limitations |
| User confusion about status source | Medium | Low | Clear documentation, in-app help |
| Dependency conflicts | Low | Medium | Use optional `[ui]` extra |
| Reference code license issues | Very Low | High | Verify license compatibility before porting |

### R-3: Rollback Plan

**If Critical Bug Found**:
1. Remove extension from `package.json` `pi.extensions` array
2. Users can still use pi-tk-flow core without UI
3. Fix bug in Python package
4. Re-enable extension after fix

**If Performance Unacceptable**:
1. Profile slow operations
2. Implement caching or lazy loading
3. If still slow, consider pagination or virtualization

### R-4: Success Criteria

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Launch success | `/tf ui` starts without error | 100% |
| Load time | Time to first render | <1s |
| Refresh time | Time for `r` key refresh | <500ms |
| Test coverage | Unit test coverage | ≥80% (data layer) |
| Documentation | README explains installation | Complete |
| User acceptance | Manual test checklist passes | 100% |

### R-5: Post-Launch Monitoring

**Week 1-2 After Launch**:
- Monitor for user-reported issues
- Collect feedback on performance
- Document common questions

**Ongoing**:
- Track Textual version updates
- Monitor tk CLI for interface changes
- Collect enhancement requests

---

## File Manifest

### New Files

| Path | Description |
|------|-------------|
| `python/pyproject.toml` | Package configuration with [ui] extra |
| `python/pi_tk_flow_ui/__init__.py` | Package init, version |
| `python/pi_tk_flow_ui/__main__.py` | Entry point for `python -m` |
| `python/pi_tk_flow_ui/app.py` | TicketflowApp, TicketBoard, TopicBrowser |
| `python/pi_tk_flow_ui/ticket_loader.py` | YamlTicketLoader, Ticket dataclass |
| `python/pi_tk_flow_ui/board_classifier.py` | BoardClassifier, BoardColumn |
| `python/pi_tk_flow_ui/topic_scanner.py` | TopicScanner, Topic dataclass |
| `python/pi_tk_flow_ui/styles.tcss` | Textual CSS styling |
| `extensions/tf-ui.ts` | Extension command registration |
| `tests/fixtures/sample_project/` | Test data |
| `tests/test_ticket_loader.py` | Unit tests for loader |
| `tests/test_topic_scanner.py` | Unit tests for scanner |
| `tests/test_board_classifier.py` | Unit tests for classifier |

### Modified Files

| Path | Changes |
|------|---------|
| `package.json` | Add `tf-ui` to `pi.extensions` array |
| `README.md` | Add UI installation and usage section |

---

## Appendix: Reference Code Mapping

| Reference Component | New Component | Changes Required |
|---------------------|---------------|------------------|
| `TicketLoader` | `YamlTicketLoader` | Parse YAML instead of markdown |
| `Ticket` dataclass | `Ticket` dataclass | Add `plan_name`, `plan_dir` fields |
| `TopicIndexLoader` | `TopicScanner` | Scan files instead of reading JSON |
| `BoardClassifier` | `BoardClassifier` | Reuse unchanged |
| `TicketflowApp` | `TicketflowApp` | Minor adaptation for new loaders |
| `TicketBoard` | `TicketBoard` | Add plan name display |
| `TopicBrowser` | `TopicBrowser` | Minor adaptation for new scanner |
| CSS styles | `styles.tcss` | Extract to separate file |
| `main()` | `__main__.py` | Adapt for extension spawning |
