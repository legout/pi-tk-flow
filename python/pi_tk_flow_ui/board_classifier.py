"""Board classification logic for tickets.

This module provides Kanban column classification based on ticket status
and dependency resolution.
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
    """A ticket with board column classification.
    
    Attributes:
        ticket: The underlying Ticket object
        column: The Kanban column this ticket belongs in
        blocking_deps: List of dependency IDs that are blocking this ticket
    """
    ticket: "Ticket"
    column: BoardColumn
    blocking_deps: list[str] = field(default_factory=list)
    
    @property
    def id(self) -> str:
        """Ticket ID (convenience accessor)."""
        return self.ticket.id
    
    @property
    def title(self) -> str:
        """Ticket title (convenience accessor)."""
        return self.ticket.title


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
    
    Classification rules (in order of precedence):
    1. CLOSED: If ticket status is "closed"
    2. BLOCKED: If any dependency is not closed
    3. IN_PROGRESS: If ticket status is "in_progress"
    4. READY: All other tickets (open, no blockers)
    
    Example:
        >>> from pi_tk_flow_ui.ticket_loader import YamlTicketLoader
        >>> loader = YamlTicketLoader()
        >>> tickets = loader.load_all()
        >>> classifier = BoardClassifier(tickets)
        >>> view = classifier.classify()
        >>> print(f"Ready: {view.counts['ready']}")
        >>> print(f"Blocked: {view.counts['blocked']}")
    """
    
    def __init__(self, tickets: list["Ticket"] | None = None):
        """Initialize classifier.
        
        Args:
            tickets: Optional list of tickets. If None, loads all tickets.
        """
        self.tickets = tickets or []
        self._ticket_map: dict[str, "Ticket"] = {}
    
    def classify(self, tickets: list["Ticket"] | None = None) -> BoardView:
        """Classify tickets into board columns.
        
        Args:
            tickets: Optional list to classify. Uses self.tickets if not provided.
            
        Returns:
            BoardView with all classified tickets.
        """
        tickets_to_classify = tickets if tickets is not None else self.tickets
        
        # Build ticket lookup map for dependency resolution
        self._ticket_map = {t.id: t for t in tickets_to_classify}
        
        classified: list[ClassifiedTicket] = []
        for ticket in tickets_to_classify:
            column, blocking = self._classify_one(ticket)
            classified.append(ClassifiedTicket(
                ticket=ticket,
                column=column,
                blocking_deps=blocking
            ))
        
        return BoardView(tickets=classified)
    
    def classify_all(self) -> BoardView:
        """Load and classify all tickets from all plans.
        
        Convenience method that loads tickets and classifies them.
        
        Returns:
            BoardView with all classified tickets.
        """
        if not self.tickets:
            from .ticket_loader import YamlTicketLoader
            loader = YamlTicketLoader()
            self.tickets = loader.load_all()
        
        return self.classify(self.tickets)
    
    def _classify_one(self, ticket: "Ticket") -> tuple[BoardColumn, list[str]]:
        """Classify a single ticket.
        
        Args:
            ticket: The ticket to classify
            
        Returns:
            Tuple of (column, blocking_dependencies)
        """
        # Rule 1: Closed tickets go to CLOSED column
        if ticket.status == "closed":
            return BoardColumn.CLOSED, []
        
        # Rule 2: Check for blocking dependencies
        blocking = self._get_blocking_deps(ticket)
        if blocking:
            return BoardColumn.BLOCKED, blocking
        
        # Rule 3: In-progress tickets
        if ticket.status == "in_progress":
            return BoardColumn.IN_PROGRESS, []
        
        # Rule 4: Everything else is READY
        return BoardColumn.READY, []
    
    def _get_blocking_deps(self, ticket: "Ticket") -> list[str]:
        """Get list of unresolved (blocking) dependencies.
        
        A dependency is blocking if:
        - It exists in our ticket map AND its status is not "closed"
        - It doesn't exist in our ticket map (unknown dependency = treat as blocker)
        
        Args:
            ticket: The ticket to check dependencies for
            
        Returns:
            List of blocking dependency IDs
        """
        blocking: list[str] = []
        
        for dep_id in ticket.deps:
            dep = self._ticket_map.get(dep_id)
            if dep is None:
                # Unknown dependency - treat as blocking for safety
                blocking.append(dep_id)
            elif dep.status != "closed":
                # Known dependency not yet closed
                blocking.append(dep_id)
        
        return blocking
    
    def is_blocked(self, ticket: "Ticket") -> bool:
        """Check if a ticket is blocked by dependencies.
        
        Args:
            ticket: The ticket to check
            
        Returns:
            True if ticket has unresolved dependencies
        """
        blocking = self._get_blocking_deps(ticket)
        return len(blocking) > 0
    
    def get_ready_tickets(self) -> list["Ticket"]:
        """Get all tickets that are ready to work on.
        
        Returns:
            List of tickets that are open (not in_progress or closed)
            and have no blocking dependencies.
        """
        ready: list["Ticket"] = []
        for ticket in self.tickets:
            if ticket.status not in ("closed", "in_progress"):
                if not self.is_blocked(ticket):
                    ready.append(ticket)
        return ready
