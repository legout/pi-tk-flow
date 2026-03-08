"""Board classification logic for Kanban-style ticket board.

Provides Ready/Blocked/In Progress/Closed classification based on ticket
status and dependencies, computed locally without subprocess calls.

Classification Rules:
- Closed: status == "closed" (regardless of dependencies)
- In Progress: status == "in_progress"
- Blocked: status in {open, in_progress} and any dependency is not closed
- Ready: status == "open" and all dependencies are closed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ticket_loader import Ticket


class BoardColumn(Enum):
    """Kanban board columns."""
    READY = "ready"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


@dataclass
class ClassifiedTicket:
    """A ticket with its board column classification.

    Attributes:
        ticket: The underlying Ticket object
        column: The board column this ticket belongs to
        blocking_deps: List of dependency IDs that are blocking this ticket
                      (only populated for BLOCKED tickets)
    """
    ticket: "Ticket"
    column: BoardColumn
    blocking_deps: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        """Get ticket ID."""
        return self.ticket.id

    @property
    def status(self) -> str:
        """Get ticket status."""
        return self.ticket.status

    @property
    def title(self) -> str:
        """Get ticket title."""
        return self.ticket.title

    def is_ready(self) -> bool:
        """Check if ticket is in Ready column."""
        return self.column == BoardColumn.READY

    def is_blocked(self) -> bool:
        """Check if ticket is in Blocked column."""
        return self.column == BoardColumn.BLOCKED

    def is_in_progress(self) -> bool:
        """Check if ticket is in In Progress column."""
        return self.column == BoardColumn.IN_PROGRESS

    def is_closed(self) -> bool:
        """Check if ticket is in Closed column."""
        return self.column == BoardColumn.CLOSED


@dataclass
class BoardView:
    """Complete board view with classified tickets."""
    tickets: list[ClassifiedTicket] = field(default_factory=list)

    def get_by_column(self, column: BoardColumn) -> list[ClassifiedTicket]:
        """Get all tickets in a specific column."""
        return [t for t in self.tickets if t.column == column]

    @property
    def counts(self) -> dict[str, int]:
        """Get ticket counts by column."""
        return {
            "ready": len(self.get_by_column(BoardColumn.READY)),
            "blocked": len(self.get_by_column(BoardColumn.BLOCKED)),
            "in_progress": len(self.get_by_column(BoardColumn.IN_PROGRESS)),
            "closed": len(self.get_by_column(BoardColumn.CLOSED)),
        }


class BoardClassifier:
    """Classifies tickets into Kanban board columns.

    This classifier implements the MVP rule for mapping tickets into
    Ready/Blocked/In Progress/Closed columns based on status and dependencies.

    The classification is performed locally without spawning subprocesses
    (no `tk ready` calls), making it suitable for UI rendering.

    Classification Rules:
    - Closed: status == "closed"
    - In Progress: status == "in_progress"
    - Blocked: status in {open, in_progress} and any dependency is not closed
    - Ready: status == "open" and all dependencies are closed
    """

    def __init__(self, tickets: list["Ticket"] | None = None):
        """Initialize classifier.

        Args:
            tickets: Optional list of tickets. If None, loads all tickets.
        """
        self.tickets = tickets or []
        self._classified: list[ClassifiedTicket] = []
        self._by_column: dict[BoardColumn, list[ClassifiedTicket]] = {
            col: [] for col in BoardColumn
        }
        self._by_id: dict[str, ClassifiedTicket] = {}

    def classify(self, tickets: list["Ticket"] | None = None) -> BoardView:
        """Classify tickets into board columns.

        Args:
            tickets: Optional list to classify. Uses self.tickets if not provided.

        Returns:
            BoardView with all classified tickets.
        """
        tickets_to_classify = tickets if tickets is not None else self.tickets
        return self._classify_tickets(tickets_to_classify)

    def classify_all(self) -> BoardView:
        """Load and classify all tickets from .tickets/ directory.

        Convenience method that loads tickets and classifies them.

        Returns:
            BoardView with all classified tickets.
        """
        if not self.tickets:
            from .ticket_loader import YamlTicketLoader
            loader = YamlTicketLoader()
            self.tickets = loader.load_all()

        return self.classify(self.tickets)

    def _classify_tickets(self, tickets: list["Ticket"]) -> BoardView:
        """Classify a list of tickets.

        Args:
            tickets: List of tickets to classify

        Returns:
            BoardView containing classified tickets
        """
        # Build status lookup for dependency checking
        status_by_id: dict[str, str] = {t.id: t.status for t in tickets}

        self._classified = []
        self._by_column = {col: [] for col in BoardColumn}
        self._by_id = {}

        for ticket in tickets:
            classified = self._classify_single(ticket, status_by_id)
            self._classified.append(classified)
            self._by_column[classified.column].append(classified)
            self._by_id[classified.id] = classified

        # Sort each column by priority (if available) then ID
        for column in BoardColumn:
            self._by_column[column].sort(
                key=lambda ct: (-(ct.ticket.priority or 0), ct.id)
            )

        return BoardView(self._classified)

    def _classify_single(self, ticket: "Ticket", status_by_id: dict[str, str]) -> ClassifiedTicket:
        """Classify a single ticket.

        Args:
            ticket: The ticket to classify
            status_by_id: Lookup dict mapping ticket IDs to their status

        Returns:
            ClassifiedTicket with column assignment
        """
        status = (ticket.status or "").lower()

        # Rule 1: Closed tickets go to Closed column (regardless of deps)
        if status == "closed":
            return ClassifiedTicket(ticket, BoardColumn.CLOSED)

        # For open/in_progress tickets, check dependencies first
        # (blocked check applies to both open and in_progress statuses)
        blocking_deps = self._find_blocking_deps(ticket, status_by_id)

        # Rule 2: If any dependency is not closed, ticket is Blocked
        if blocking_deps:
            return ClassifiedTicket(ticket, BoardColumn.BLOCKED, blocking_deps)

        # Rule 3: In Progress status (and no blocking deps) goes to In Progress column
        if status == "in_progress":
            return ClassifiedTicket(ticket, BoardColumn.IN_PROGRESS)

        # Rule 4: Open status (and no blocking deps) goes to Ready column
        if status == "open":
            return ClassifiedTicket(ticket, BoardColumn.READY)

        # Unknown status - treat as Ready (no blocking deps)
        return ClassifiedTicket(ticket, BoardColumn.READY)

    def _find_blocking_deps(self, ticket: "Ticket", status_by_id: dict[str, str]) -> list[str]:
        """Find dependencies that are blocking this ticket.

        A dependency is blocking if it's not in "closed" status.

        Args:
            ticket: The ticket to check
            status_by_id: Lookup dict mapping ticket IDs to their status

        Returns:
            List of blocking dependency IDs
        """
        blocking = []
        for dep_id in ticket.deps:
            dep_status = status_by_id.get(dep_id, "unknown").lower()
            if dep_status != "closed":
                blocking.append(dep_id)
        return blocking

    def is_blocked(self, ticket: "Ticket") -> bool:
        """Check if a ticket is blocked by dependencies.

        Args:
            ticket: The ticket to check

        Returns:
            True if ticket has unresolved dependencies
        """
        # Build status lookup if not already built
        if not hasattr(self, '_status_by_id') or not self._status_by_id:
            if not self.tickets:
                from .ticket_loader import YamlTicketLoader
                loader = YamlTicketLoader()
                self.tickets = loader.load_all()
            self._status_by_id = {t.id: t.status for t in self.tickets}

        blocking = self._find_blocking_deps(ticket, self._status_by_id)
        return len(blocking) > 0

    def get_ready_tickets(self) -> list["Ticket"]:
        """Get all tickets that are ready to work on.

        Returns:
            List of tickets that are open (not in_progress or closed)
            and have no blocking dependencies.
        """
        if not self.tickets:
            from .ticket_loader import YamlTicketLoader
            loader = YamlTicketLoader()
            self.tickets = loader.load_all()

        view = self.classify(self.tickets)
        return [ct.ticket for ct in view.get_by_column(BoardColumn.READY)]
