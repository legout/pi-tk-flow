"""Textual TUI for Ticketflow.

Provides a Kanban-style interface for viewing tickets and browsing knowledge topics.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Import ticket loading and board classification
from tf.ticket_loader import TicketLoader, Ticket
from tf.board_classifier import BoardClassifier, BoardColumn, ClassifiedTicket, BoardView


def resolve_knowledge_dir() -> Path:
    """Resolve the knowledge directory from config or default.
    
    Resolution order:
    1. TF_KNOWLEDGE_DIR environment variable
    2. workflow.knowledgeDir from .tf/config/settings.json
    3. Default: .tf/knowledge (relative to repo root or cwd)
    
    Returns:
        Resolved Path to the knowledge directory
    """
    # 1. Environment variable
    env_dir = os.environ.get("TF_KNOWLEDGE_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    
    # 2. Find repo root and check config
    repo_root = _find_repo_root()
    if repo_root:
        local_config = repo_root / ".tf" / "config" / "settings.json"
        if local_config.is_file():
            try:
                with open(local_config, "r", encoding="utf-8") as f:
                    config = json.load(f)
                knowledge_dir = config.get("workflow", {}).get("knowledgeDir")
                if knowledge_dir:
                    path = Path(knowledge_dir).expanduser()
                    if path.is_absolute():
                        return path.resolve()
                    return (repo_root / path).resolve()
            except (json.JSONDecodeError, IOError):
                pass
        return (repo_root / ".tf" / "knowledge").resolve()
    
    # 3. Fallback to cwd
    return (Path.cwd() / ".tf" / "knowledge").resolve()


def _find_repo_root() -> Optional[Path]:
    """Find the repository root by looking for .tf directory."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        tf_dir = parent / ".tf"
        if tf_dir.is_dir():
            has_tickets = (tf_dir / "tickets").is_dir()
            has_ralph = (tf_dir / "ralph").is_dir()
            has_agents = (parent / "AGENTS.md").is_file()
            if has_tickets or has_ralph or has_agents:
                return parent
    return None


def get_topic_type(topic_id: str) -> str:
    """Derive topic type from topic ID prefix.
    
    Args:
        topic_id: The topic ID (e.g., "seed-add-versioning")
        
    Returns:
        The topic type: "seed", "plan", "spike", "baseline", or "unknown"
    """
    if topic_id.startswith("seed-"):
        return "seed"
    elif topic_id.startswith("plan-"):
        return "plan"
    elif topic_id.startswith("spike-"):
        return "spike"
    elif topic_id.startswith("baseline-"):
        return "baseline"
    else:
        return "unknown"


@dataclass
class TopicDoc:
    """Represents a topic document with path and existence info."""
    path: str
    exists: bool


@dataclass
class Topic:
    """Represents a knowledge topic with resolved documentation paths."""
    id: str
    title: str
    keywords: list[str] = field(default_factory=list)
    topic_type: str = "unknown"
    overview: Optional[TopicDoc] = None
    sources: Optional[TopicDoc] = None
    plan: Optional[TopicDoc] = None
    backlog: Optional[TopicDoc] = None
    
    @property
    def available_docs(self) -> dict[str, TopicDoc]:
        """Return mapping of doc types to docs that exist."""
        docs = {}
        for doc_type in ["overview", "sources", "plan", "backlog"]:
            doc = getattr(self, doc_type)
            if doc and doc.exists:
                docs[doc_type] = doc
        return docs


class TopicIndexLoadError(Exception):
    """Raised when topic index cannot be loaded."""
    pass


class TopicIndexLoader:
    """Loads and provides access to knowledge topics from index.json.
    
    This class handles:
    - Loading .tf/knowledge/index.json
    - Grouping topics by type (seed/spike/plan/baseline)
    - Resolving documentation paths for each topic
    - Providing filtered access to topics
    
    Example:
        >>> loader = TopicIndexLoader()
        >>> topics = loader.load()
        >>> seed_topics = loader.get_by_type("seed")
        >>> for topic in seed_topics:
        ...     print(f"{topic.id}: {topic.title}")
        ...     print(f"  Available docs: {list(topic.available_docs.keys())}")
    """
    
    def __init__(self, knowledge_dir: Optional[Path] = None):
        """Initialize the loader.
        
        Args:
            knowledge_dir: Optional path to knowledge directory.
                          If not provided, resolves automatically.
        """
        self.knowledge_dir = knowledge_dir or resolve_knowledge_dir()
        self._topics: list[Topic] = []
        self._by_type: dict[str, list[Topic]] = {}
        self._by_id: dict[str, Topic] = {}
        self._loaded = False
    
    def load(self) -> list[Topic]:
        """Load topics from index.json.
        
        Returns:
            List of all topics.
            
        Raises:
            TopicIndexLoadError: If index.json cannot be read or is invalid.
        """
        index_path = self.knowledge_dir / "index.json"
        
        if not index_path.exists():
            raise TopicIndexLoadError(
                f"Knowledge index not found: {index_path}\n"
                "Run 'tf kb rebuild-index' to create it."
            )
        
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise TopicIndexLoadError(
                f"Invalid JSON in {index_path}: {e}\n"
                "Run 'tf kb rebuild-index' to fix it."
            )
        except IOError as e:
            raise TopicIndexLoadError(f"Cannot read {index_path}: {e}")
        
        # Handle both dict with 'topics' key and legacy list format
        if isinstance(data, dict):
            topics_data = data.get("topics", [])
        elif isinstance(data, list):
            topics_data = data
        else:
            raise TopicIndexLoadError(
                f"Invalid index format: expected dict or list, got {type(data).__name__}\n"
                "Run 'tf kb rebuild-index' to fix it."
            )
        
        self._topics = []
        self._by_type = {"seed": [], "plan": [], "spike": [], "baseline": [], "unknown": []}
        self._by_id = {}
        
        for topic_data in topics_data:
            topic = self._parse_topic(topic_data)
            self._topics.append(topic)
            self._by_type[topic.topic_type].append(topic)
            self._by_id[topic.id] = topic
        
        self._loaded = True
        return self._topics
    
    def _parse_topic(self, data: dict) -> Topic:
        """Parse a topic from index.json data.
        
        Args:
            data: Raw topic data from index.json
            
        Returns:
            Parsed Topic with resolved doc paths
        """
        topic_id = data.get("id", "")
        topic_type = get_topic_type(topic_id)
        
        # Resolve doc paths
        def resolve_doc(doc_path: Optional[str]) -> Optional[TopicDoc]:
            if not doc_path:
                return None
            full_path = self.knowledge_dir / doc_path
            return TopicDoc(
                path=doc_path,
                exists=full_path.exists()
            )
        
        return Topic(
            id=topic_id,
            title=data.get("title", ""),
            keywords=data.get("keywords", []),
            topic_type=topic_type,
            overview=resolve_doc(data.get("overview")),
            sources=resolve_doc(data.get("sources")),
            plan=resolve_doc(data.get("plan")),
            backlog=resolve_doc(data.get("backlog")),
        )
    
    def get_all(self) -> list[Topic]:
        """Get all topics.
        
        Returns:
            List of all loaded topics.
            
        Raises:
            TopicIndexLoadError: If topics haven't been loaded.
        """
        if not self._loaded:
            raise TopicIndexLoadError("Topics not loaded. Call load() first.")
        return self._topics.copy()
    
    def get_by_type(self, topic_type: str) -> list[Topic]:
        """Get topics filtered by type.
        
        Args:
            topic_type: One of "seed", "plan", "spike", "baseline", "unknown"
            
        Returns:
            List of topics of the specified type.
            
        Raises:
            TopicIndexLoadError: If topics haven't been loaded.
        """
        if not self._loaded:
            raise TopicIndexLoadError("Topics not loaded. Call load() first.")
        return self._by_type.get(topic_type, []).copy()
    
    def get_by_id(self, topic_id: str) -> Optional[Topic]:
        """Get a topic by its ID.
        
        Args:
            topic_id: The topic ID to look up
            
        Returns:
            The topic if found, None otherwise.
            
        Raises:
            TopicIndexLoadError: If topics haven't been loaded.
        """
        if not self._loaded:
            raise TopicIndexLoadError("Topics not loaded. Call load() first.")
        return self._by_id.get(topic_id)
    
    def search(self, query: str) -> list[Topic]:
        """Search topics by keyword in title or keywords.
        
        Args:
            query: Search string (case-insensitive substring match)
            
        Returns:
            List of matching topics.
            
        Raises:
            TopicIndexLoadError: If topics haven't been loaded.
        """
        if not self._loaded:
            raise TopicIndexLoadError("Topics not loaded. Call load() first.")
        
        query_lower = query.lower()
        results = []
        
        for topic in self._topics:
            # Search in title
            if query_lower in topic.title.lower():
                results.append(topic)
                continue
            # Search in keywords
            if any(query_lower in kw.lower() for kw in topic.keywords):
                results.append(topic)
                continue
            # Search in ID
            if query_lower in topic.id.lower():
                results.append(topic)
        
        return results
    
    @property
    def topic_types(self) -> list[str]:
        """Get list of available topic types that have topics."""
        if not self._loaded:
            return []
        return [t for t in ["seed", "plan", "spike", "baseline"] if self._by_type[t]]
    
    @property
    def count_by_type(self) -> dict[str, int]:
        """Get count of topics by type."""
        if not self._loaded:
            return {}
        return {
            "seed": len(self._by_type["seed"]),
            "plan": len(self._by_type["plan"]),
            "spike": len(self._by_type["spike"]),
            "baseline": len(self._by_type["baseline"]),
            "unknown": len(self._by_type["unknown"]),
        }


def format_topic_list(topics: list[Topic], show_docs: bool = False) -> str:
    """Format a list of topics for display.
    
    Args:
        topics: List of topics to format
        show_docs: Whether to show available docs for each topic
        
    Returns:
        Formatted string suitable for display
    """
    if not topics:
        return "No topics found."
    
    lines = []
    for topic in topics:
        doc_indicator = ""
        if show_docs and topic.available_docs:
            doc_indicator = f" [{', '.join(topic.available_docs.keys())}]"
        lines.append(f"  {topic.id}: {topic.title}{doc_indicator}")
    
    return "\n".join(lines)


def open_topic_doc(topic: Topic, doc_type: str) -> bool:
    """Open a topic document in $PAGER or $EDITOR.
    
    Args:
        topic: The topic containing the document
        doc_type: Type of document to open (overview, sources, plan, backlog)
        
    Returns:
        True if document was opened, False otherwise
    """
    doc = getattr(topic, doc_type, None)
    if not doc or not doc.exists:
        return False
    
    doc_path = Path(topic.id).parent / doc.path
    full_path = resolve_knowledge_dir() / doc.path
    
    # Try $PAGER first, then $EDITOR, then fallback
    pager = os.environ.get("PAGER", "")
    editor = os.environ.get("EDITOR", "")
    
    if pager:
        cmd = f'{pager} "{full_path}"'
    elif editor:
        cmd = f'{editor} "{full_path}"'
    else:
        # Fallback to common pagers
        for fallback in ["less", "more", "cat"]:
            if os.system(f"which {fallback} > /dev/null 2>&1") == 0:
                cmd = f'{fallback} "{full_path}"'
                break
        else:
            return False
    
    os.system(cmd)
    return True


def main(argv: Optional[list[str]] = None) -> int:
    """Launch the Ticketflow TUI or web UI.
    
    Args:
        argv: Command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse command-line arguments
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="tf ui",
        description="Launch the Ticketflow UI (terminal or web)"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Print the textual serve command for running the UI in a browser"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind web server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for web server (default: 8000)"
    )

    # Parse only known args to allow backward compatibility
    args, _ = parser.parse_known_args(argv or sys.argv[1:])

    # If --web flag is set, print the textual serve command
    if args.web:
        print("\n🌐 To serve the Ticketflow UI in a web browser, run:")
        print("")
        print(f"   textual serve \"tf ui\" --host {args.host} --port {args.port}")
        print("")
        print("⚠️  WARNING: Security considerations for web serving:")
        print("   • The default host (127.0.0.1) only allows local access")
        print("   • Use --host 0.0.0.0 to bind to all interfaces (allows external access)")
        print("   • Binding to 0.0.0.0 exposes the UI on your network - ensure proper firewall rules")
        print("   • No authentication is provided - anyone with access can view tickets")
        print("")
        return 0
    
    # Check if we're running in a TTY
    # For web serving via textual serve, stdin/stdout are not TTYs
    # We allow non-TTY execution as the App will handle it
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        sys.stderr.write("Warning: Running in non-TTY environment (web server mode)\n")
    
    try:
        from textual.app import App, ComposeResult
        from textual.widgets import (
            Static, Header, Footer, ListView, ListItem, Label,
            TabbedContent, TabPane, Input, Markdown, Button
        )
        from textual.containers import Horizontal, Vertical, VerticalScroll
        from textual.reactive import reactive
        from textual.binding import Binding
    except ImportError:
        print("Error: Textual is not installed.", file=sys.stderr)
        print("Install with: uv pip install textual", file=sys.stderr)
        print("Or run with uv: uv run tf ui", file=sys.stderr)
        return 1

    class DataListItem(ListItem):
        """ListItem that can store arbitrary data."""
        def __init__(self, *children, data=None, **kwargs):
            super().__init__(*children, **kwargs)
            self.data = data

    class TopicBrowser(Static):
        """Widget for browsing knowledge topics."""
        
        topics: reactive[list[Topic]] = reactive([])
        selected_topic: reactive[Optional[Topic]] = reactive(None)
        
        def compose(self) -> ComposeResult:
            """Compose the topic browser layout."""
            with Horizontal():
                # Left sidebar: topic list
                with Vertical(id="topic-sidebar"):
                    yield Input(placeholder="Search topics...", id="topic-search")
                    yield ListView(id="topic-list")
                
                # Right panel: topic details
                with Vertical(id="topic-detail"):
                    yield Static("Select a topic to view details", id="topic-detail-content")
        
        def on_mount(self) -> None:
            """Load topics when mounted."""
            self.load_topics()
        
        def load_topics(self) -> None:
            """Load topics from index."""
            try:
                loader = TopicIndexLoader()
                self.topics = loader.load()
                self.update_topic_list()
            except TopicIndexLoadError as e:
                self.query_one("#topic-list", ListView).clear()
                self.query_one("#topic-detail-content", Static).update(
                    f"[red]Error loading topics:[/red]\n{e}"
                )
        
        def update_topic_list(self) -> None:
            """Update the topic list display."""
            list_view = self.query_one("#topic-list", ListView)
            list_view.clear()
            
            # Group by type
            by_type: dict[str, list[Topic]] = {}
            for topic in self.topics:
                by_type.setdefault(topic.topic_type, []).append(topic)
            
            # Add items grouped by type
            for type_name in ["plan", "spike", "seed", "baseline", "unknown"]:
                if type_name in by_type:
                    # Add type header
                    list_view.append(ListItem(
                        Label(f"[b]{type_name.upper()}[/b]"),
                        disabled=True
                    ))
                    # Add topics
                    for topic in sorted(by_type[type_name], key=lambda t: t.title):
                        list_view.append(DataListItem(
                            Label(f"  {topic.title}"),
                            data=topic
                        ))
        
        def on_list_view_selected(self, event: ListView.Selected) -> None:
            """Handle topic selection."""
            item = event.item
            if hasattr(item, "data") and item.data:
                self.selected_topic = item.data
                self.update_detail_view()
        
        def update_detail_view(self) -> None:
            """Update the detail view for selected topic."""
            if not self.selected_topic:
                return
            
            topic = self.selected_topic
            content = self.query_one("#topic-detail-content", Static)
            
            # Build detail text
            lines = [
                f"[b]{topic.title}[/b]",
                f"",
                f"ID: {topic.id}",
                f"Type: {topic.topic_type}",
            ]
            
            if topic.keywords:
                lines.append(f"Keywords: {', '.join(topic.keywords)}")
            
            lines.append("")
            lines.append("[b]Available Documents:[/b]")
            
            # Map doc types to key bindings
            key_map = {
                "overview": "[1]",
                "sources": "[2]",
                "plan": "[3]",
                "backlog": "[4]",
            }
            
            for doc_type, doc in topic.available_docs.items():
                key_hint = key_map.get(doc_type, "")
                lines.append(f"  {key_hint} {doc_type}: {doc.path}")
            
            if not topic.available_docs:
                lines.append("  [dim](no documents available)[/dim]")
            else:
                lines.append("")
                lines.append("[dim]Press [1-4] to open, 'o' for first available[/dim]")
            
            content.update("\n".join(lines))
        
        def action_open_doc(self) -> None:
            """Open the first available document (default action)."""
            if not self.selected_topic:
                self.notify("No topic selected", severity="warning")
                return
            
            topic = self.selected_topic
            if not topic.available_docs:
                self.notify(f"No documents available for {topic.id}", severity="warning")
                return
            
            # Open the first available doc
            doc_type = list(topic.available_docs.keys())[0]
            self._open_doc(topic, doc_type)
        
        def action_open_overview(self) -> None:
            """Open overview document."""
            self._open_doc_by_type("overview")
        
        def action_open_sources(self) -> None:
            """Open sources document."""
            self._open_doc_by_type("sources")
        
        def action_open_plan(self) -> None:
            """Open plan document."""
            self._open_doc_by_type("plan")
        
        def action_open_backlog(self) -> None:
            """Open backlog document."""
            self._open_doc_by_type("backlog")
        
        def _open_doc_by_type(self, doc_type: str) -> None:
            """Open a document by type with error handling."""
            if not self.selected_topic:
                self.notify("No topic selected", severity="warning")
                return
            
            self._open_doc(self.selected_topic, doc_type)
        
        def _open_doc(self, topic: Topic, doc_type: str) -> None:
            """Open a topic document using $PAGER or $EDITOR.
            
            Args:
                topic: The topic containing the document
                doc_type: Type of document to open
            """
            doc = getattr(topic, doc_type, None)
            
            if not doc:
                self.notify(f"{topic.id} has no {doc_type} document", severity="warning")
                return
            
            if not doc.exists:
                self.notify(f"{doc_type} document not found: {doc.path}", severity="error")
                return
            
            # Resolve full path
            knowledge_dir = resolve_knowledge_dir()
            full_path = knowledge_dir / doc.path
            
            # Determine command to use
            pager = os.environ.get("PAGER", "").strip()
            editor = os.environ.get("EDITOR", "").strip()
            
            cmd = None
            if pager:
                cmd = f'{pager} "{full_path}"'
            elif editor:
                cmd = f'{editor} "{full_path}"'
            else:
                # Fallback to common pagers
                for fallback in ["less", "more", "cat"]:
                    result = os.system(f"which {fallback} > /dev/null 2>&1")
                    if result == 0:
                        cmd = f'{fallback} "{full_path}"'
                        break
            
            if not cmd:
                self.notify("No pager or editor found. Set $PAGER or $EDITOR.", severity="error")
                return
            
            # Run the command with terminal suspend for external pagers/editors
            try:
                with self.app.suspend():
                    exit_code = os.system(cmd)
            except Exception as e:
                self.notify(f"Failed to suspend terminal: {e}", severity="error")
                return
            
            if exit_code != 0:
                self.notify(f"Failed to open document (exit code: {exit_code})", severity="error")
            else:
                self.notify(f"Opened {doc_type}: {doc.path}")
        
        def on_input_changed(self, event: Input.Changed) -> None:
            """Handle search input."""
            if not event.value:
                self.update_topic_list()
                return
            
            try:
                loader = TopicIndexLoader()
                loader._topics = self.topics  # Use already loaded topics
                loader._loaded = True
                results = loader.search(event.value)
                
                list_view = self.query_one("#topic-list", ListView)
                list_view.clear()

                for topic in sorted(results, key=lambda t: t.title):
                    list_view.append(DataListItem(
                        Label(f"[{topic.topic_type}] {topic.title}"),
                        data=topic
                    ))
            except Exception:
                pass  # Ignore search errors
    
    class TicketBoard(Static):
        """Widget for displaying Kanban-style ticket board."""
        
        board_view: reactive[Optional[BoardView]] = reactive(None)
        selected_ticket: reactive[Optional[ClassifiedTicket]] = reactive(None)
        
        # Filter state
        search_query: reactive[str] = reactive("")
        status_filter: reactive[str] = reactive("")
        tag_filter: reactive[str] = reactive("")
        assignee_filter: reactive[str] = reactive("")
        external_ref_filter: reactive[str] = reactive("")
        
        # Description display state
        show_full_description: reactive[bool] = reactive(False)
        DESCRIPTION_LIMIT: int = 2500
        
        # Implementation docs state
        implementation_docs: reactive[dict[str, Path]] = reactive({})
        
        def compose(self) -> ComposeResult:
            """Compose the ticket board layout."""
            with Horizontal():
                # Left side: Board columns
                with Vertical(id="board-container"):
                    yield Static("[b]Ticket Board[/b]", id="board-header")
                    
                    # Filter bar
                    with Horizontal(id="filter-bar"):
                        yield Input(placeholder="Search title/body...", id="search-input")
                        yield Input(placeholder="Status...", id="status-filter")
                        yield Input(placeholder="Tag...", id="tag-filter")
                        yield Input(placeholder="Assignee...", id="assignee-filter")
                        yield Input(placeholder="External ref...", id="external-ref-filter")
                        yield Button("Clear", id="clear-filters", variant="primary")
                    
                    with Horizontal(id="board-columns"):
                        # Four columns: Ready, Blocked, In Progress, Closed
                        with VerticalScroll(id="col-ready", classes="board-column"):
                            yield Static("[green]READY[/green]", classes="column-header")
                            yield ListView(id="list-ready")
                        
                        with VerticalScroll(id="col-blocked", classes="board-column"):
                            yield Static("[red]BLOCKED[/red]", classes="column-header")
                            yield ListView(id="list-blocked")
                        
                        with VerticalScroll(id="col-in-progress", classes="board-column"):
                            yield Static("[yellow]IN PROGRESS[/yellow]", classes="column-header")
                            yield ListView(id="list-in-progress")
                        
                        with VerticalScroll(id="col-closed", classes="board-column"):
                            yield Static("[dim]CLOSED[/dim]", classes="column-header")
                            yield ListView(id="list-closed")
                
                # Right side: Ticket detail panel
                with Vertical(id="ticket-detail-panel"):
                    yield Static("[b]Ticket Detail[/b]", id="detail-header")
                    yield VerticalScroll(Static("Select a ticket to view details", id="ticket-detail-content"), id="detail-scroll")
        
        def on_mount(self) -> None:
            """Load tickets when mounted."""
            self.load_tickets()
        
        def load_tickets(self) -> None:
            """Load and classify tickets from disk."""
            try:
                classifier = BoardClassifier()
                self.board_view = classifier.classify_all()
                self.update_board()
                self.update_detail_counts()
            except Exception as e:
                self._show_error(f"Error loading tickets: {e}")
        
        def load_implementation_docs(self, ticket_id: str) -> dict[str, Path]:
            """Load implementation docs for a ticket from .tf/knowledge/tickets/.
            
            Args:
                ticket_id: The ticket ID to load docs for
                
            Returns:
                Dict mapping doc type to Path of the doc file
            """
            # Find repo root
            repo_root = _find_repo_root()
            if not repo_root:
                return {}
            
            knowledge_tickets_dir = repo_root / ".tf" / "knowledge" / "tickets" / ticket_id
            
            if not knowledge_tickets_dir.is_dir():
                return {}
            
            # Map of doc types to filenames
            doc_types = {
                "implementation": "implementation.md",
                "research": "research.md",
                "review": "review.md",
                "fixes": "fixes.md",
                "close-summary": "close-summary.md",
                "chain-summary": "chain-summary.md",
                "post-fix-verification": "post-fix-verification.md",
            }
            
            docs = {}
            for doc_type, filename in doc_types.items():
                doc_path = knowledge_tickets_dir / filename
                if doc_path.exists():
                    docs[doc_type] = doc_path
            
            return docs
        
        def _show_error(self, message: str) -> None:
            """Display an error message in all columns."""
            for col_id in ["list-ready", "list-blocked", "list-in-progress", "list-closed"]:
                list_view = self.query_one(f"#{col_id}", ListView)
                list_view.clear()
            self.query_one("#ticket-detail-content", Static).update(f"[red]{message}[/red]")
        
        def on_input_changed(self, event: Input.Changed) -> None:
            """Handle filter input changes."""
            input_id = event.input.id
            if input_id == "search-input":
                self.search_query = event.value
            elif input_id == "status-filter":
                self.status_filter = event.value.lower()
            elif input_id == "tag-filter":
                self.tag_filter = event.value.lower()
            elif input_id == "assignee-filter":
                self.assignee_filter = event.value.lower()
            elif input_id == "external-ref-filter":
                self.external_ref_filter = event.value.lower()
            self.update_board()
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses."""
            if event.button.id == "clear-filters":
                self._clear_filters()
        
        def _clear_filters(self) -> None:
            """Clear all filter inputs and restore full ticket set."""
            # Reset reactive filter state
            self.search_query = ""
            self.status_filter = ""
            self.tag_filter = ""
            self.assignee_filter = ""
            self.external_ref_filter = ""
            
            # Clear input widgets
            self.query_one("#search-input", Input).value = ""
            self.query_one("#status-filter", Input).value = ""
            self.query_one("#tag-filter", Input).value = ""
            self.query_one("#assignee-filter", Input).value = ""
            self.query_one("#external-ref-filter", Input).value = ""
            
            self.notify("Filters cleared")
        
        def _apply_filters(self, tickets: list[ClassifiedTicket]) -> list[ClassifiedTicket]:
            """Apply all active filters to the ticket list.
            
            Args:
                tickets: List of classified tickets to filter
                
            Returns:
                Filtered list of tickets matching all criteria
            """
            filtered = tickets
            
            # Search query (title, body, or ID)
            if self.search_query:
                query = self.search_query.lower()
                filtered = [
                    ct for ct in filtered
                    if query in ct.id.lower()
                    or query in ct.ticket.title.lower()
                    or query in ct.ticket.body.lower()
                ]
            
            # Status filter
            if self.status_filter:
                filtered = [
                    ct for ct in filtered
                    if self.status_filter in ct.ticket.status.lower()
                ]
            
            # Tag filter (substring match on any tag)
            if self.tag_filter:
                filtered = [
                    ct for ct in filtered
                    if any(self.tag_filter in tag.lower() for tag in ct.ticket.tags)
                ]
            
            # Assignee filter
            if self.assignee_filter:
                filtered = [
                    ct for ct in filtered
                    if ct.ticket.assignee and self.assignee_filter in ct.ticket.assignee.lower()
                ]
            
            # External ref filter
            if self.external_ref_filter:
                filtered = [
                    ct for ct in filtered
                    if ct.ticket.external_ref and self.external_ref_filter in ct.ticket.external_ref.lower()
                ]
            
            return filtered
        
        def update_detail_counts(self) -> None:
            """Update the board header with ticket counts."""
            if not self.board_view:
                return
            counts = self.board_view.counts
            header = self.query_one("#board-header", Static)
            header.update(
                f"[b]Ticket Board[/b] | "
                f"[green]Ready: {counts['ready']}[/green] | "
                f"[red]Blocked: {counts['blocked']}[/red] | "
                f"[yellow]In Progress: {counts['in_progress']}[/yellow] | "
                f"[dim]Closed: {counts['closed']}[/dim]"
            )
        
        def update_board(self) -> None:
            """Update all board columns with tickets."""
            if not self.board_view:
                return
            
            # Update each column
            column_map = {
                BoardColumn.READY: "list-ready",
                BoardColumn.BLOCKED: "list-blocked",
                BoardColumn.IN_PROGRESS: "list-in-progress",
                BoardColumn.CLOSED: "list-closed",
            }
            
            for column, list_id in column_map.items():
                list_view = self.query_one(f"#{list_id}", ListView)
                list_view.clear()
                
                tickets = self.board_view.get_by_column(column)
                # Apply filters
                tickets = self._apply_filters(tickets)
                
                for ct in tickets:
                    # Format: ID - Title (truncated if needed)
                    title = ct.title[:35] + "..." if len(ct.title) > 35 else ct.title
                    priority_indicator = f"[P{ct.ticket.priority}] " if ct.ticket.priority is not None else ""
                    label_text = f"{priority_indicator}{ct.id}: {title}"

                    list_view.append(DataListItem(
                        Label(label_text),
                        data=ct
                    ))
        
        def on_list_view_selected(self, event: ListView.Selected) -> None:
            """Handle ticket selection from any column."""
            item = event.item
            if hasattr(item, "data") and item.data:
                self.selected_ticket = item.data
                self.update_detail_view()
        
        def update_detail_view(self) -> None:
            """Update the detail view for selected ticket."""
            if not self.selected_ticket:
                return
            
            ct = self.selected_ticket
            ticket = ct.ticket
            content = self.query_one("#ticket-detail-content", Static)
            
            # Build detail text
            status_color = {
                BoardColumn.READY: "green",
                BoardColumn.BLOCKED: "red",
                BoardColumn.IN_PROGRESS: "yellow",
                BoardColumn.CLOSED: "dim",
            }.get(ct.column, "white")
            
            lines = [
                f"[b]{ticket.title}[/b]",
                "",
                f"ID: {ticket.id}",
                f"Status: {ticket.status}",
                f"Column: [{status_color}]{ct.column.value.upper()}[/{status_color}]",
            ]
            
            if ticket.ticket_type:
                lines.append(f"Type: {ticket.ticket_type}")
            if ticket.priority is not None:
                lines.append(f"Priority: {ticket.priority}")
            if ticket.assignee:
                lines.append(f"Assignee: @{ticket.assignee}")
            if ticket.external_ref:
                lines.append(f"External Ref: {ticket.external_ref}")
            
            if ticket.tags:
                lines.append(f"Tags: {', '.join(ticket.tags)}")
            
            if ticket.deps:
                lines.append("")
                lines.append("[b]Dependencies:[/b]")
                for dep in ticket.deps:
                    # Check if this dep is blocking
                    is_blocking = dep in ct.blocking_deps
                    color = "red" if is_blocking else "dim"
                    status_indicator = " [BLOCKING]" if is_blocking else ""
                    lines.append(f"  • [{color}]{dep}[/{color}]{status_indicator}")
            
            if ticket.links:
                lines.append("")
                lines.append("[b]Linked Tickets:[/b]")
                for link in ticket.links:
                    lines.append(f"  • {link}")
            
            lines.append("")
            lines.append("[b]Description:[/b] [dim](Press 'e' to expand/collapse)[/dim]")
            
            # Load and display body (with configurable limit)
            if self.show_full_description:
                body = ticket.body if ticket.body else "(no description)"
            else:
                limit = self.DESCRIPTION_LIMIT
                body = ticket.body[:limit] if ticket.body else "(no description)"
                if len(ticket.body) > limit:
                    body += "\n\n[i](truncated... press 'e' to expand)[/i]"
            lines.append(body)
            
            # Load and display implementation docs
            impl_docs = self.load_implementation_docs(ticket.id)
            if impl_docs:
                lines.append("")
                lines.append("[b]Implementation Docs:[/b] [dim](Press key to open)[/dim]")
                
                # Map doc types to key bindings
                key_map = {
                    "implementation": "[1]",
                    "research": "[2]",
                    "review": "[3]",
                    "fixes": "[4]",
                    "close-summary": "[5]",
                    "chain-summary": "[6]",
                    "post-fix-verification": "[7]",
                }
                
                for doc_type, doc_path in impl_docs.items():
                    key_hint = key_map.get(doc_type, "")
                    lines.append(f"  {key_hint} {doc_type}: {doc_path.name}")
            else:
                lines.append("")
                lines.append("[dim]No implementation docs found (run IRF workflow to generate)[/dim]")
            
            content.update("\n".join(lines))
        
        def action_toggle_description(self) -> None:
            """Toggle between truncated and full description view."""
            self.show_full_description = not self.show_full_description
            self.update_detail_view()
        
        def _open_implementation_doc(self, doc_type: str) -> None:
            """Open an implementation doc by type.
            
            Args:
                doc_type: Type of doc to open (implementation, research, review, etc.)
            """
            if not self.selected_ticket:
                self.notify("No ticket selected", severity="warning")
                return
            
            ticket_id = self.selected_ticket.ticket.id
            docs = self.load_implementation_docs(ticket_id)
            
            if doc_type not in docs:
                self.notify(f"No {doc_type} doc found for {ticket_id}", severity="warning")
                return
            
            doc_path = docs[doc_type]
            
            # Determine command to use
            pager = os.environ.get("PAGER", "").strip()
            editor = os.environ.get("EDITOR", "").strip()
            
            cmd = None
            if pager:
                cmd = f'{pager} "{doc_path}"'
            elif editor:
                cmd = f'{editor} "{doc_path}"'
            else:
                # Fallback to common pagers
                for fallback in ["less", "more", "cat"]:
                    result = os.system(f"which {fallback} > /dev/null 2>&1")
                    if result == 0:
                        cmd = f'{fallback} "{doc_path}"'
                        break
            
            if not cmd:
                self.notify("No pager or editor found. Set $PAGER or $EDITOR.", severity="error")
                return
            
            # Run the command with terminal suspend for external pagers/editors
            try:
                with self.app.suspend():
                    exit_code = os.system(cmd)
            except Exception as e:
                self.notify(f"Failed to suspend terminal: {e}", severity="error")
                return
            
            if exit_code != 0:
                self.notify(f"Failed to open document (exit code: {exit_code})", severity="error")
            else:
                self.notify(f"Opened {doc_type}: {doc_path.name}")
        
        def action_open_implementation(self) -> None:
            """Open implementation doc."""
            self._open_implementation_doc("implementation")
        
        def action_open_research(self) -> None:
            """Open research doc."""
            self._open_implementation_doc("research")
        
        def action_open_review(self) -> None:
            """Open review doc."""
            self._open_implementation_doc("review")
        
        def action_open_fixes(self) -> None:
            """Open fixes doc."""
            self._open_implementation_doc("fixes")
        
        def action_open_close_summary(self) -> None:
            """Open close-summary doc."""
            self._open_implementation_doc("close-summary")
        
        def action_open_chain_summary(self) -> None:
            """Open chain-summary doc."""
            self._open_implementation_doc("chain-summary")
        
        def action_open_post_fix_verification(self) -> None:
            """Open post-fix-verification doc."""
            self._open_implementation_doc("post-fix-verification")
    
    class TicketflowApp(App):
        """Textual app for Ticketflow."""
        
        CSS = """
        Screen {
            align: center middle;
        }
        
        #placeholder {
            width: 60;
            height: auto;
            border: solid green;
            padding: 1 2;
            text-align: center;
        }
        
        #topic-sidebar {
            width: 40%;
            border: solid $primary;
            padding: 1;
        }
        
        #topic-detail {
            width: 60%;
            border: solid $primary;
            padding: 1;
        }
        
        #topic-list {
            height: 1fr;
            border: solid $primary-darken-2;
        }
        
        #topic-search {
            margin-bottom: 1;
        }
        
        #topic-detail-content {
            height: 1fr;
        }
        
        /* Ticket Board Styles */
        #board-container {
            width: 65%;
            border: solid $primary;
            padding: 1;
        }
        
        #board-header {
            height: auto;
            padding-bottom: 1;
            border-bottom: solid $primary-darken-2;
            margin-bottom: 1;
        }
        
        #filter-bar {
            height: auto;
            padding-bottom: 1;
            margin-bottom: 1;
        }
        
        #filter-bar Input {
            width: 1fr;
            margin-right: 1;
        }
        
        #filter-bar Input:last-child {
            margin-right: 0;
        }
        
        #board-columns {
            height: 1fr;
        }
        
        .board-column {
            width: 1fr;
            border: solid $primary-darken-2;
            margin: 0 1;
            padding: 1;
        }
        
        .board-column:first-child {
            margin-left: 0;
        }
        
        .board-column:last-child {
            margin-right: 0;
        }
        
        .column-header {
            text-align: center;
            border-bottom: solid $primary-darken-2;
            padding-bottom: 1;
            margin-bottom: 1;
        }
        
        #list-ready, #list-blocked, #list-in-progress, #list-closed {
            height: 1fr;
            border: none;
        }
        
        #ticket-detail-panel {
            width: 35%;
            border: solid $primary;
            padding: 1;
        }
        
        #detail-header {
            height: auto;
            padding-bottom: 1;
            border-bottom: solid $primary-darken-2;
            margin-bottom: 1;
        }
        
        #detail-scroll {
            height: 1fr;
        }
        
        #ticket-detail-content {
            height: auto;
        }
        
        ListView > ListItem.--highlight {
            background: $primary-darken-2;
        }
        
        ListView:focus > ListItem.--highlight {
            background: $primary;
        }
        """
        
        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("r", "refresh", "Refresh"),
            Binding("o", "open_doc", "Open Doc"),
            Binding("e", "expand_desc", "Expand Desc"),
            Binding("1", "open_overview", "Overview/Impl"),
            Binding("2", "open_sources", "Sources/Research"),
            Binding("3", "open_plan", "Plan/Review"),
            Binding("4", "open_backlog", "Backlog/Fixes"),
            # Additional ticket doc bindings (only for Tickets tab)
            Binding("5", "ticket_close", "Close Summary"),
            Binding("6", "ticket_chain", "Chain Summary"),
            Binding("7", "ticket_pfv", "Post-Fix Verif"),
        ]
        
        def compose(self) -> ComposeResult:
            """Compose the app layout."""
            yield Header()
            
            with TabbedContent():
                with TabPane("Topics", id="tab-topics"):
                    yield TopicBrowser()
                
                with TabPane("Tickets", id="tab-tickets"):
                    yield TicketBoard()
            
            yield Footer()
        
        def action_refresh(self) -> None:
            """Refresh the current view."""
            # Get the active tab
            tabbed = self.query_one(TabbedContent)
            active_pane = tabbed.active_pane
            
            if active_pane and active_pane.id == "tab-topics":
                topic_browser = self.query_one(TopicBrowser)
                topic_browser.load_topics()
            elif active_pane and active_pane.id == "tab-tickets":
                ticket_board = self.query_one(TicketBoard)
                ticket_board.load_tickets()
        
        def action_open_doc(self) -> None:
            """Open the first available document (delegates to appropriate widget)."""
            tabbed = self.query_one(TabbedContent)
            active_pane = tabbed.active_pane
            
            if active_pane and active_pane.id == "tab-topics":
                topic_browser = self.query_one(TopicBrowser)
                topic_browser.action_open_doc()
            elif active_pane and active_pane.id == "tab-tickets":
                ticket_board = self.query_one(TicketBoard)
                ticket_board.action_open_implementation()
        
        def action_open_overview(self) -> None:
            """Open overview document (Topics tab) or implementation doc (Tickets tab)."""
            tabbed = self.query_one(TabbedContent)
            active_pane = tabbed.active_pane
            
            if active_pane and active_pane.id == "tab-topics":
                topic_browser = self.query_one(TopicBrowser)
                topic_browser.action_open_overview()
            elif active_pane and active_pane.id == "tab-tickets":
                ticket_board = self.query_one(TicketBoard)
                ticket_board.action_open_implementation()
        
        def action_open_sources(self) -> None:
            """Open sources document (Topics tab) or research doc (Tickets tab)."""
            tabbed = self.query_one(TabbedContent)
            active_pane = tabbed.active_pane
            
            if active_pane and active_pane.id == "tab-topics":
                topic_browser = self.query_one(TopicBrowser)
                topic_browser.action_open_sources()
            elif active_pane and active_pane.id == "tab-tickets":
                ticket_board = self.query_one(TicketBoard)
                ticket_board.action_open_research()
        
        def action_open_plan(self) -> None:
            """Open plan document (Topics tab) or review doc (Tickets tab)."""
            tabbed = self.query_one(TabbedContent)
            active_pane = tabbed.active_pane
            
            if active_pane and active_pane.id == "tab-topics":
                topic_browser = self.query_one(TopicBrowser)
                topic_browser.action_open_plan()
            elif active_pane and active_pane.id == "tab-tickets":
                ticket_board = self.query_one(TicketBoard)
                ticket_board.action_open_review()
        
        def action_open_backlog(self) -> None:
            """Open backlog document (Topics tab) or fixes doc (Tickets tab)."""
            tabbed = self.query_one(TabbedContent)
            active_pane = tabbed.active_pane
            
            if active_pane and active_pane.id == "tab-topics":
                topic_browser = self.query_one(TopicBrowser)
                topic_browser.action_open_backlog()
            elif active_pane and active_pane.id == "tab-tickets":
                ticket_board = self.query_one(TicketBoard)
                ticket_board.action_open_fixes()
        
        def action_expand_desc(self) -> None:
            """Toggle full description view (delegates to TicketBoard)."""
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_toggle_description()
        
        def action_ticket_impl(self) -> None:
            """Open implementation doc (delegates to TicketBoard)."""
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_open_implementation()
        
        def action_ticket_research(self) -> None:
            """Open research doc (delegates to TicketBoard)."""
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_open_research()
        
        def action_ticket_review(self) -> None:
            """Open review doc (delegates to TicketBoard)."""
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_open_review()
        
        def action_ticket_fixes(self) -> None:
            """Open fixes doc (delegates to TicketBoard)."""
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_open_fixes()
        
        def action_ticket_close(self) -> None:
            """Open close-summary doc (delegates to TicketBoard)."""
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_open_close_summary()
        
        def action_ticket_chain(self) -> None:
            """Open chain-summary doc (delegates to TicketBoard)."""
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_open_chain_summary()
        
        def action_ticket_pfv(self) -> None:
            """Open post-fix-verification doc (delegates to TicketBoard)."""
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_open_post_fix_verification()
    
    app = TicketflowApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
