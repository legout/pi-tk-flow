"""Textual TUI for pi-tk-flow.

Provides a Kanban-style interface for viewing tickets and browsing plans.
"""

from __future__ import annotations

import logging
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from pi_tk_flow_ui.board_classifier import BoardClassifier, BoardColumn, ClassifiedTicket, BoardView
from pi_tk_flow_ui.plan_scanner import Plan, PlanScanner

# Textual imports
from textual.app import App, ComposeResult
from textual.widgets import (
    Static, Header, Footer, ListView, ListItem, Label,
    TabbedContent, TabPane, Input, Button
)
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.binding import Binding

logger = logging.getLogger(__name__)

PLAN_DOC_OPEN_ORDER = (
    "03-implementation-plan.md",
    "01-prd.md",
    "02-spec.md",
    "04-ticket-breakdown.md",
    "03-plan.md",
    "04-progress.md",
)
TICKET_BREAKDOWN_FILES = ("04-ticket-breakdown.md", "04-progress.md")


def first_existing_file(dir_path: Path, candidates: tuple[str, ...]) -> Optional[Path]:
    """Return the first existing candidate file in a directory."""
    for filename in candidates:
        candidate = dir_path / filename
        if candidate.exists():
            return candidate
    return None


def open_file(widget: Static, file_path: Path) -> None:
    """Open a file using EDITOR/PAGER without invoking a shell."""
    if not file_path.exists():
        widget.notify(f"File not found: {file_path}", severity="error")
        return

    editor = os.environ.get("EDITOR", "").strip()
    pager = os.environ.get("PAGER", "").strip()

    cmd_parts = None
    for configured_cmd in (editor, pager):
        if not configured_cmd:
            continue
        try:
            cmd_parts = shlex.split(configured_cmd) + [str(file_path)]
        except ValueError:
            cmd_parts = [configured_cmd, str(file_path)]
        break

    if not cmd_parts:
        for fallback in ("less", "more", "cat"):
            if shutil.which(fallback):
                cmd_parts = [fallback, str(file_path)]
                break

    if not cmd_parts:
        widget.notify("No pager or editor found. Set $PAGER or $EDITOR.", severity="error")
        return

    try:
        with widget.app.suspend():
            result = subprocess.run(cmd_parts, check=False)
            exit_code = result.returncode
    except Exception as e:
        widget.notify(f"Failed to suspend terminal: {e}", severity="error")
        return

    if exit_code != 0:
        widget.notify(f"Command failed (exit code: {exit_code})", severity="error")


class DataListItem(ListItem):
    """ListItem that can store arbitrary data."""
    def __init__(self, *children, data=None, **kwargs):
        super().__init__(*children, **kwargs)
        self.data = data


class PlanBrowser(Static):
    """Widget for browsing plan directories."""
    
    plans: reactive[list[Plan]] = reactive([])
    selected_plan: reactive[Optional[Plan]] = reactive(None)
    
    def compose(self) -> ComposeResult:
        """Compose the plan browser layout."""
        with Horizontal():
            # Left sidebar: plan list
            with Vertical(id="plan-sidebar"):
                yield Input(placeholder="Search plans...", id="plan-search")
                yield ListView(id="plan-list")
            
            # Right panel: plan details
            with Vertical(id="plan-detail"):
                yield Static("Select a plan to view details", id="plan-detail-content")
    
    def on_mount(self) -> None:
        """Load plans when mounted."""
        self.load_plans()
    
    def load_plans(self) -> None:
        """Load plans from .tf/plans/."""
        try:
            scanner = PlanScanner()
            self.plans = scanner.scan()
            self.update_plan_list()
        except Exception as e:
            self.query_one("#plan-list", ListView).clear()
            self.query_one("#plan-detail-content", Static).update(
                f"[red]Error loading plans:[/red]\n{e}"
            )
    
    def update_plan_list(self) -> None:
        """Update the plan list display."""
        list_view = self.query_one("#plan-list", ListView)
        list_view.clear()
        
        if not self.plans:
            list_view.append(ListItem(
                Label("[dim]No plans found in .tf/plans/[/dim]"),
                disabled=True
            ))
            return
        
        # Group by year/month from date
        by_period: dict[str, list[Plan]] = {}
        for plan in self.plans:
            if plan.plan_date:
                period = plan.plan_date[:7]  # YYYY-MM
            else:
                period = "Unknown"
            by_period.setdefault(period, []).append(plan)
        
        # Add items grouped by period (sorted newest first)
        for period in sorted(by_period.keys(), reverse=True):
            plans_in_period = by_period[period]
            # Add period header
            display_period = period if period != "Unknown" else "No Date"
            list_view.append(ListItem(
                Label(f"[b]{display_period}[/b]"),
                disabled=True
            ))
            # Add plans
            for plan in plans_in_period:
                display_title = plan.title[:40] + "..." if len(plan.title) > 40 else plan.title
                status_indicator = f"[{plan.status}] " if plan.status != "Unknown" else ""
                list_view.append(DataListItem(
                    Label(f"  {status_indicator}{display_title}"),
                    data=plan
                ))
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle plan selection."""
        item = event.item
        if hasattr(item, "data") and item.data:
            self.selected_plan = item.data
            self.update_detail_view()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input."""
        if not event.value:
            self.update_plan_list()
            return
        
        try:
            query = event.value.lower()
            results = [
                p for p in self.plans
                if query in p.title.lower()
                or query in p.plan_topic.lower()
                or query in p.id.lower()
                or query in p.plan_date.lower()
            ]
            
            list_view = self.query_one("#plan-list", ListView)
            list_view.clear()
            
            if not results:
                list_view.append(ListItem(
                    Label("[dim]No matching plans[/dim]"),
                    disabled=True
                ))
                return
            
            for plan in sorted(results, key=lambda p: (p.plan_date, p.plan_topic), reverse=True):
                display_title = plan.title[:40] + "..." if len(plan.title) > 40 else plan.title
                status_indicator = f"[{plan.status}] " if plan.status != "Unknown" else ""
                list_view.append(DataListItem(
                    Label(f"{status_indicator}{display_title}"),
                    data=plan
                ))
        except Exception:
            pass  # Ignore search errors
    
    def update_detail_view(self) -> None:
        """Update the detail view for selected plan."""
        if not self.selected_plan:
            return
        
        plan = self.selected_plan
        content = self.query_one("#plan-detail-content", Static)
        
        # Build detail text
        lines = [
            f"[b]{plan.title}[/b]",
            f"",
            f"ID: {plan.id}",
            f"Date: {plan.plan_date or 'N/A'}",
            f"Topic: {plan.plan_topic}",
            f"Status: {plan.status}",
            "",
            "[b]Documents:[/b]",
        ]
        
        if plan.prd_path:
            lines.append(f"  [green]✓[/green] PRD (01-prd.md)")
        else:
            lines.append(f"  [dim]✗ PRD[/dim]")
        
        if plan.spec_path:
            lines.append(f"  [green]✓[/green] Spec (02-spec.md)")
        else:
            lines.append(f"  [dim]✗ Spec[/dim]")
        
        if plan.impl_plan_path:
            lines.append(f"  [green]✓[/green] Implementation Plan ({plan.impl_plan_path.name})")
        else:
            lines.append(f"  [dim]✗ Implementation Plan[/dim]")
        
        if plan.ticket_breakdown_path:
            label = "Ticket Breakdown" if plan.ticket_breakdown_path.name == "04-ticket-breakdown.md" else "Legacy Progress"
            lines.append(f"  [green]✓[/green] {label} ({plan.ticket_breakdown_path.name})")
        else:
            lines.append(f"  [dim]✗ Ticket Breakdown[/dim]")
        
        lines.append("")
        lines.append(f"Path: {plan.dir_path}")
        
        content.update("\n".join(lines))
    
    def action_open_doc(self) -> None:
        """Open the selected plan's PRD in pager/editor."""
        if not self.selected_plan:
            self.notify("No plan selected", severity="warning")
            return
        
        plan = self.selected_plan
        # Open PRD first, or implementation plan as fallback
        file_to_open = plan.prd_path or plan.impl_plan_path or plan.spec_path
        
        if not file_to_open:
            self.notify("No documents found for this plan", severity="warning")
            return
        
        self._open_file(file_to_open)
    
    def action_open_doc_1(self) -> None:
        """Open PRD document (01-prd.md) for selected plan."""
        if not self.selected_plan:
            self.notify("No plan selected", severity="warning")
            return
        
        if not self.selected_plan.prd_path:
            self.notify("PRD not found for this plan", severity="warning")
            return
        
        self._open_file(self.selected_plan.prd_path)
    
    def action_open_doc_2(self) -> None:
        """Open Spec document (02-spec.md) for selected plan."""
        if not self.selected_plan:
            self.notify("No plan selected", severity="warning")
            return
        
        if not self.selected_plan.spec_path:
            self.notify("Spec not found for this plan", severity="warning")
            return
        
        self._open_file(self.selected_plan.spec_path)
    
    def action_open_doc_3(self) -> None:
        """Open Implementation Plan document for selected plan."""
        if not self.selected_plan:
            self.notify("No plan selected", severity="warning")
            return
        
        if not self.selected_plan.impl_plan_path:
            self.notify("Implementation Plan not found for this plan", severity="warning")
            return
        
        self._open_file(self.selected_plan.impl_plan_path)
    
    def action_open_doc_4(self) -> None:
        """Open ticket breakdown document for selected plan."""
        if not self.selected_plan:
            self.notify("No plan selected", severity="warning")
            return
        
        if not self.selected_plan.ticket_breakdown_path:
            self.notify("Ticket breakdown not found for this plan", severity="warning")
            return
        
        self._open_file(self.selected_plan.ticket_breakdown_path)
    
    def _open_file(self, file_path: Path) -> None:
        """Open a file using EDITOR/PAGER."""
        open_file(self, file_path)


class TicketBoard(Static):
    """Widget for displaying Kanban-style ticket board."""
    
    board_view: reactive[Optional[BoardView]] = reactive(None)
    selected_ticket: reactive[Optional[ClassifiedTicket]] = reactive(None)
    
    # Filter state
    search_query: reactive[str] = reactive("")
    tag_filter: reactive[str] = reactive("")
    assignee_filter: reactive[str] = reactive("")
    
    # Description display state
    show_full_description: reactive[bool] = reactive(False)
    DESCRIPTION_LIMIT: int = 2500
    
    def compose(self) -> ComposeResult:
        """Compose the ticket board layout."""
        with Horizontal():
            # Left side: Board columns
            with Vertical(id="board-container"):
                yield Static("[b]Ticket Board[/b]", id="board-header")
                
                # Filter bar
                with Horizontal(id="filter-bar"):
                    yield Input(placeholder="Search title/body...", id="search-input")
                    yield Input(placeholder="Tag...", id="tag-filter")
                    yield Input(placeholder="Assignee...", id="assignee-filter")
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
    
    def _show_error(self, message: str) -> None:
        """Display an error message."""
        for col_id in ["list-ready", "list-blocked", "list-in-progress", "list-closed"]:
            list_view = self.query_one(f"#{col_id}", ListView)
            list_view.clear()
        self.query_one("#ticket-detail-content", Static).update(f"[red]{message}[/red]")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes."""
        input_id = event.input.id
        if input_id == "search-input":
            self.search_query = event.value
        elif input_id == "tag-filter":
            self.tag_filter = event.value.lower()
        elif input_id == "assignee-filter":
            self.assignee_filter = event.value.lower()
        self.update_board()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "clear-filters":
            self._clear_filters()
    
    def _clear_filters(self) -> None:
        """Clear all filter inputs."""
        self.search_query = ""
        self.tag_filter = ""
        self.assignee_filter = ""
        
        self.query_one("#search-input", Input).value = ""
        self.query_one("#tag-filter", Input).value = ""
        self.query_one("#assignee-filter", Input).value = ""
        
        self.notify("Filters cleared")
        self.update_board()
    
    def _apply_filters(self, tickets: list[ClassifiedTicket]) -> list[ClassifiedTicket]:
        """Apply all active filters to the ticket list."""
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
        
        # Tag filter
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
            tickets = self._apply_filters(tickets)

            # Show empty state if no tickets after filtering
            if not tickets:
                list_view.append(ListItem(
                    Label("[dim]No tickets[/dim]"),
                    disabled=True
                ))
                continue

            for ct in tickets:
                title = ct.title[:35] + "..." if len(ct.title) > 35 else ct.title
                priority_indicator = f"[P{ct.ticket.priority}] " if ct.ticket.priority else ""
                plan_indicator = f"[{ct.ticket.plan_name[:15]}] " if ct.ticket.plan_name else ""
                label_text = f"{plan_indicator}{priority_indicator}{ct.id}: {title}"
                
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
        if ticket.priority:
            lines.append(f"Priority: {ticket.priority}")
        if ticket.assignee:
            lines.append(f"Assignee: @{ticket.assignee}")
        if ticket.external_ref:
            lines.append(f"External: {ticket.external_ref}")
        
        if ticket.tags:
            lines.append(f"Tags: {', '.join(ticket.tags)}")
        
        lines.append("")
        lines.append(f"Plan: {ticket.plan_name}")
        
        if ticket.deps:
            lines.append("")
            lines.append("[b]Dependencies:[/b]")
            for dep in ticket.deps:
                is_blocking = dep in ct.blocking_deps
                color = "red" if is_blocking else "dim"
                status_indicator = " [BLOCKING]" if is_blocking else ""
                lines.append(f"  • [{color}]{dep}[/{color}]{status_indicator}")
        
        lines.append("")
        lines.append("[b]Description:[/b] [dim](Press 'e' to expand/collapse)[/dim]")
        
        if self.show_full_description:
            body = ticket.body if ticket.body else "(no description)"
        else:
            limit = self.DESCRIPTION_LIMIT
            body = ticket.body[:limit] if ticket.body else "(no description)"
            if len(ticket.body) > limit:
                body += "\n\n[i](truncated... press 'e' to expand)[/i]"
        lines.append(body)
        
        content.update("\n".join(lines))
    
    def action_toggle_description(self) -> None:
        """Toggle between truncated and full description view."""
        self.show_full_description = not self.show_full_description
        self.update_detail_view()
    
    def action_open_in_editor(self) -> None:
        """Open selected ticket's plan directory in editor."""
        if not self.selected_ticket:
            self.notify("No ticket selected", severity="warning")
            return
        
        plan_dir = Path(self.selected_ticket.ticket.plan_dir)
        if not plan_dir.exists():
            self.notify(f"Plan directory not found: {plan_dir}", severity="error")
            return
        
        plan_file = first_existing_file(plan_dir, PLAN_DOC_OPEN_ORDER)
        
        if plan_file is None:
            self.notify(f"No plan documents found in {plan_dir}", severity="warning")
            return
        
        self._open_file(plan_file)
    
    def _open_file(self, file_path: Path) -> None:
        """Open a file using EDITOR/PAGER."""
        open_file(self, file_path)


class TicketflowApp(App):
    """Textual app for Ticketflow."""
    
    CSS_PATH = "styles.tcss"
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("o", "open_doc", "Open Doc"),
        Binding("e", "expand_desc", "Expand Desc"),
        Binding("1", "open_doc_1", "Open PRD"),
        Binding("2", "open_doc_2", "Open Spec"),
        Binding("3", "open_doc_3", "Open Plan"),
        Binding("4", "open_doc_4", "Open Breakdown"),
        Binding("?", "help", "Help"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        
        with TabbedContent():
            with TabPane("Tickets", id="tab-tickets"):
                yield TicketBoard()
            
            with TabPane("Plans", id="tab-plans"):
                yield PlanBrowser()
        
        yield Footer()
    
    def action_refresh(self) -> None:
        """Refresh the current view."""
        tabbed = self.query_one(TabbedContent)
        active = tabbed.active
        
        if active == "tab-tickets":
            ticket_board = self.query_one(TicketBoard)
            ticket_board.load_tickets()
            self.notify("Tickets refreshed")
        elif active == "tab-plans":
            plan_browser = self.query_one(PlanBrowser)
            plan_browser.load_plans()
            self.notify("Plans refreshed")
    
    def action_open_doc(self) -> None:
        """Open the selected item (delegates to active widget)."""
        tabbed = self.query_one(TabbedContent)
        active = tabbed.active
        
        if active == "tab-tickets":
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_open_in_editor()
        elif active == "tab-plans":
            plan_browser = self.query_one(PlanBrowser)
            plan_browser.action_open_doc()
    
    def action_expand_desc(self) -> None:
        """Toggle description expand (tickets only)."""
        tabbed = self.query_one(TabbedContent)
        active = tabbed.active
        
        if active == "tab-tickets":
            ticket_board = self.query_one(TicketBoard)
            ticket_board.action_toggle_description()
    
    def action_open_doc_1(self) -> None:
        """Open PRD document (01-prd.md)."""
        tabbed = self.query_one(TabbedContent)
        active = tabbed.active
        
        if active == "tab-plans":
            plan_browser = self.query_one(PlanBrowser)
            plan_browser.action_open_doc_1()
        else:
            self._open_plan_doc_for_ticket("01-prd.md")
    
    def action_open_doc_2(self) -> None:
        """Open Spec document (02-spec.md)."""
        tabbed = self.query_one(TabbedContent)
        active = tabbed.active
        
        if active == "tab-plans":
            plan_browser = self.query_one(PlanBrowser)
            plan_browser.action_open_doc_2()
        else:
            self._open_plan_doc_for_ticket("02-spec.md")
    
    def action_open_doc_3(self) -> None:
        """Open Plan document (03-implementation-plan.md)."""
        tabbed = self.query_one(TabbedContent)
        active = tabbed.active
        
        if active == "tab-plans":
            plan_browser = self.query_one(PlanBrowser)
            plan_browser.action_open_doc_3()
        else:
            # Try 03-implementation-plan.md first, then 03-plan.md
            if not self._open_plan_doc_for_ticket("03-implementation-plan.md"):
                self._open_plan_doc_for_ticket("03-plan.md")
    
    def action_open_doc_4(self) -> None:
        """Open ticket breakdown document."""
        tabbed = self.query_one(TabbedContent)
        active = tabbed.active
        
        if active == "tab-plans":
            plan_browser = self.query_one(PlanBrowser)
            plan_browser.action_open_doc_4()
        else:
            for filename in TICKET_BREAKDOWN_FILES:
                if self._open_plan_doc_for_ticket(filename):
                    break
    
    def _open_plan_doc_for_ticket(self, filename: str) -> bool:
        """Open a plan document by filename.
        
        Returns True if document was found and opened, False otherwise.
        """
        ticket_board = self.query_one(TicketBoard)
        if not ticket_board.selected_ticket:
            self.notify("No ticket selected", severity="warning")
            return False
        
        plan_dir = Path(ticket_board.selected_ticket.ticket.plan_dir)
        doc_path = plan_dir / filename
        
        if not doc_path.exists():
            self.notify(f"Document not found: {filename}", severity="warning")
            return False
        
        ticket_board._open_file(doc_path)
        return True
    
    def action_help(self) -> None:
        """Show help dialog."""
        help_text = """[b]Keyboard Shortcuts[/b]

[b]Global[/b]
  q        Quit
  r        Refresh current tab
  ?        Show this help

[b]Tickets Tab[/b]
  o        Open plan document
  e        Expand/collapse description
  1        Open PRD (01-prd.md)
  2        Open Spec (02-spec.md)
  3        Open Plan (03-implementation-plan.md)
  4        Open Ticket Breakdown (04-ticket-breakdown.md)

[b]Plans Tab[/b]
  o        Open PRD (or first available doc)
  1        Open PRD (01-prd.md)
  2        Open Spec (02-spec.md)
  3        Open Implementation Plan
  4        Open Ticket Breakdown (04-ticket-breakdown.md)

[b]Navigation[/b]
  Tab      Move focus
  ↑/↓      Navigate lists
  Enter    Select item
"""
        self.notify(help_text, timeout=10)


def main() -> int:
    """Main entry point for the app."""
    app = TicketflowApp()
    app.run()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
