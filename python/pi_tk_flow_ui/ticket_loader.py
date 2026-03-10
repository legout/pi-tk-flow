"""Ticket loading from .tickets/*.md files with frontmatter parsing.

This module provides efficient loading of ticket metadata from `.tickets/*.md` files,
with support for lazy loading of full ticket body content.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from .path_resolution import resolve_tickets_dir

logger = logging.getLogger(__name__)

# Regex pattern for YAML frontmatter (supports both Unix \n and Windows \r\n line endings)
FRONTMATTER_PATTERN = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", re.DOTALL)

# Regex pattern for markdown title (first # heading)
TITLE_PATTERN = re.compile(r"^#\s*(.+)$", re.MULTILINE)


@dataclass
class Ticket:
    """Represents a ticket with metadata and lazy body loading.

    Attributes:
        id: Ticket ID (e.g., "ptf-102j")
        status: Ticket status (e.g., "open", "closed", "in_progress")
        title: Ticket title from markdown heading
        file_path: Path to the ticket markdown file
        deps: List of ticket dependencies
        tags: List of tags
        assignee: Optional assignee username
        external_ref: Optional external reference
        priority: Optional priority level
        ticket_type: Optional ticket type
        created: Optional creation timestamp
        links: List of linked tickets
        plan_name: Deprecated, kept for compatibility
        plan_dir: Deprecated, kept for compatibility
        _body: Cached body content (None until loaded)
        _body_loaded: Whether body has been loaded
    """
    id: str
    status: str
    title: str
    file_path: Path
    deps: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    assignee: Optional[str] = None
    external_ref: Optional[str] = None
    priority: Optional[int] = None
    ticket_type: Optional[str] = None
    created: Optional[str] = None
    links: list[str] = field(default_factory=list)
    plan_name: str = ""  # Deprecated, kept for compatibility
    plan_dir: str = ""  # Deprecated, kept for compatibility
    _body: Optional[str] = field(default=None, repr=False)
    _body_loaded: bool = field(default=False, repr=False)

    @property
    def body(self) -> str:
        """Get the full ticket body, loading lazily if needed.

        Returns:
            The markdown body content (excluding frontmatter and title).
        """
        if not self._body_loaded:
            self._load_body()
        return self._body or ""

    def _load_body(self) -> None:
        """Load the body content from disk."""
        try:
            content = self.file_path.read_text(encoding="utf-8")
            # Extract body after frontmatter
            match = FRONTMATTER_PATTERN.match(content)
            if match:
                body_content = match.group(2)
            else:
                body_content = content

            # Remove title line if present
            lines = body_content.split("\n")
            if lines and lines[0].startswith("# "):
                body_content = "\n".join(lines[1:]).lstrip("\n")

            self._body = body_content
        except (IOError, OSError) as e:
            logger.warning(f"Failed to load body for ticket {self.id}: {e}")
            self._body = ""
        self._body_loaded = True


class TicketLoadError(Exception):
    """Raised when a ticket cannot be loaded."""
    pass


class YamlTicketLoader:
    """Loads tickets from `.tickets/*.md` files.

    This loader provides:
    - Efficient loading of frontmatter + title only (fast for many tickets)
    - Lazy loading of full body content (on demand)
    - Graceful handling of malformed tickets (warnings, no crashes)

    Example:
        >>> loader = YamlTicketLoader()
        >>> tickets = loader.load_all()
        >>> for ticket in tickets:
        ...     print(f"{ticket.id}: {ticket.title}")
        ...     # Body is only loaded when accessed:
        ...     print(ticket.body[:100])
    """

    def __init__(self, tickets_dir: Optional[Path] = None):
        """Initialize the loader.

        Args:
            tickets_dir: Optional path to tickets directory.
                        If not provided, resolves to the current project's
                        `.tickets` directory.
        """
        self.tickets_dir = tickets_dir or self._resolve_tickets_dir()
        self._tickets: list[Ticket] = []
        self._by_id: dict[str, Ticket] = {}
        self._loaded = False

    def _resolve_tickets_dir(self) -> Path:
        """Resolve the current project's tickets directory.

        Returns:
            Resolved Path to the tickets directory
        """
        return resolve_tickets_dir()

    def load_all(self, refresh: bool = False) -> list[Ticket]:
        """Load all tickets from the tickets directory.

        Args:
            refresh: If True, reload tickets even if already loaded.

        Returns:
            List of all loaded tickets (metadata only, bodies are lazy-loaded).

        Raises:
            TicketLoadError: If tickets directory cannot be found.
        """
        if self._loaded and not refresh:
            return self._tickets.copy()

        if not self.tickets_dir.exists():
            raise TicketLoadError(
                f"Tickets directory not found: {self.tickets_dir}\n"
                "Run 'tk init' to create it."
            )

        self._tickets = []
        self._by_id = {}

        # Find all .md files in tickets directory
        ticket_files = sorted(self.tickets_dir.glob("*.md"))

        for file_path in ticket_files:
            try:
                ticket = self._parse_ticket(file_path)
                if ticket:
                    self._tickets.append(ticket)
                    self._by_id[ticket.id] = ticket
            except Exception as e:
                logger.warning(f"Skipping malformed ticket {file_path.name}: {e}")
                continue

        self._loaded = True
        return self._tickets.copy()

    def _parse_ticket(self, file_path: Path) -> Optional[Ticket]:
        """Parse a single ticket file.

        Args:
            file_path: Path to the ticket markdown file

        Returns:
            Parsed Ticket or None if parsing fails
        """
        content = file_path.read_text(encoding="utf-8")

        # Parse frontmatter
        frontmatter = self._parse_frontmatter(content)
        if frontmatter is None:
            logger.warning(f"No frontmatter found in {file_path.name}")
            return None

        # Extract title from markdown body
        title = self._extract_title(content)

        # Build ticket object
        ticket = Ticket(
            id=frontmatter.get("id", file_path.stem),
            status=frontmatter.get("status", "open"),
            title=title,
            file_path=file_path,
            deps=frontmatter.get("deps", []),
            tags=frontmatter.get("tags", []),
            assignee=frontmatter.get("assignee"),
            external_ref=frontmatter.get("external-ref") or frontmatter.get("external_ref"),
            priority=frontmatter.get("priority"),
            ticket_type=frontmatter.get("type"),
            created=frontmatter.get("created"),
            links=frontmatter.get("links", []),
            # For backward compatibility
            plan_name="",
            plan_dir=str(file_path.parent),
        )

        return ticket

    def _parse_frontmatter(self, content: str) -> Optional[dict]:
        """Parse YAML frontmatter from content.

        Args:
            content: The markdown file content

        Returns:
            Dictionary of frontmatter fields or None if no frontmatter
        """
        match = FRONTMATTER_PATTERN.match(content)
        if not match:
            return None

        frontmatter_text = match.group(1)

        try:
            return yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as e:
            logger.warning(f"YAML parsing failed: {e}")
            return None

    def _extract_title(self, content: str) -> str:
        """Extract the title from markdown content.

        Args:
            content: The markdown file content

        Returns:
            The title (first # heading) or empty string if not found
        """
        # Remove frontmatter first
        match = FRONTMATTER_PATTERN.match(content)
        if match:
            body = match.group(2)
        else:
            body = content

        # Find first # heading
        title_match = TITLE_PATTERN.search(body)
        if title_match:
            return title_match.group(1).strip()

        return ""

    def get_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by its ID.

        Args:
            ticket_id: The ticket ID to look up

        Returns:
            The ticket if found, None otherwise

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")
        return self._by_id.get(ticket_id)

    def get_by_status(self, status: str) -> list[Ticket]:
        """Get tickets filtered by status.

        Args:
            status: Status to filter by (e.g., "open", "closed")

        Returns:
            List of tickets with matching status

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")
        return [t for t in self._tickets if t.status == status]

    def search(self, query: str) -> list[Ticket]:
        """Search tickets by query string in title, id, or tags.

        Args:
            query: Search string (case-insensitive substring match)

        Returns:
            List of matching tickets

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")

        query_lower = query.lower()
        results = []

        for ticket in self._tickets:
            # Search in ID
            if query_lower in ticket.id.lower():
                results.append(ticket)
                continue
            # Search in title
            if query_lower in ticket.title.lower():
                results.append(ticket)
                continue
            # Search in tags
            if any(query_lower in tag.lower() for tag in ticket.tags):
                results.append(ticket)
                continue

        return results

    @property
    def count_by_status(self) -> dict[str, int]:
        """Get count of tickets by status.

        Returns:
            Dictionary mapping status to count
        """
        if not self._loaded:
            return {}

        counts: dict[str, int] = {}
        for ticket in self._tickets:
            counts[ticket.status] = counts.get(ticket.status, 0) + 1
        return counts
