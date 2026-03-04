"""Ticket loading from YAML files and tk CLI status queries.

This module provides ticket loading from .tf/plans/*/tickets.yaml files
with live status refresh from the tk CLI.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Ticket:
    """Represents a ticket parsed from tickets.yaml.
    
    Attributes:
        id: Unique ticket identifier (e.g., "S1", "my-ticket")
        title: Short ticket title
        body: Full description/body text
        status: Current status (open, in_progress, closed)
        deps: List of blocking dependency ticket IDs
        tags: List of tags/labels
        assignee: Optional assignee identifier
        priority: Optional priority number (lower = higher priority)
        ticket_type: Type of ticket (feature, bug, chore, epic, etc.)
        plan_name: Name of the plan directory
        plan_dir: Full path to the plan directory
        external_ref: Optional external reference (e.g., GitHub issue)
    """
    id: str
    title: str
    body: str
    status: str = "open"
    deps: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    assignee: Optional[str] = None
    priority: Optional[int] = None
    ticket_type: str = "feature"
    plan_name: str = ""
    plan_dir: str = ""
    external_ref: Optional[str] = None


class TicketLoadError(Exception):
    """Raised when ticket loading fails."""
    pass


class YamlTicketLoader:
    """Loads tickets from .tf/plans/*/tickets.yaml files.
    
    This loader:
    1. Scans .tf/plans/ for all subdirectories containing tickets.yaml
    2. Parses each YAML file and extracts slice/epic definitions
    3. Maps YAML fields to Ticket objects
    4. Queries tk CLI for current status
    
    Example:
        >>> loader = YamlTicketLoader(Path(".tf"))
        >>> tickets = loader.load_all()
        >>> for ticket in tickets:
        ...     print(f"{ticket.id}: {ticket.title} ({ticket.status})")
    """
    
    def __init__(self, tf_dir: Optional[Path] = None):
        """Initialize the loader.
        
        Args:
            tf_dir: Path to .tf directory. If None, auto-discovers from cwd.
        """
        if tf_dir is None:
            tf_dir = self._find_tf_dir()
        
        self.tf_dir = Path(tf_dir)
        self.plans_dir = self.tf_dir / "plans"
        self._status_cache: dict[str, str] = {}
    
    def _find_tf_dir(self) -> Path:
        """Find the .tf directory by walking up from cwd."""
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            tf_dir = parent / ".tf"
            if tf_dir.is_dir():
                return tf_dir
        # Fallback to cwd/.tf
        return cwd / ".tf"
    
    def load_all(self, refresh: bool = False) -> list[Ticket]:
        """Load tickets from all plan directories.
        
        Args:
            refresh: If True, clear status cache to re-query tk CLI.
        
        Returns:
            List of all tickets from all plans.
            
        Raises:
            TicketLoadError: If the plans directory doesn't exist.
        """
        # Clear status cache if refresh requested
        if refresh:
            self._status_cache.clear()
        
        if not self.plans_dir.exists():
            logger.warning(f"Plans directory not found: {self.plans_dir}")
            return []
        
        all_tickets: list[Ticket] = []
        
        for plan_dir in self.plans_dir.iterdir():
            if not plan_dir.is_dir():
                continue
            
            tickets_file = plan_dir / "tickets.yaml"
            if not tickets_file.exists():
                continue
            
            try:
                plan_tickets = self.load_plan(plan_dir)
                all_tickets.extend(plan_tickets)
            except Exception as e:
                logger.warning(f"Failed to load tickets from {plan_dir}: {e}")
                continue
        
        return all_tickets
    
    def load_plan(self, plan_dir: Path) -> list[Ticket]:
        """Load tickets from a single plan directory.
        
        Args:
            plan_dir: Path to the plan directory containing tickets.yaml
            
        Returns:
            List of tickets from this plan.
            
        Raises:
            TicketLoadError: If tickets.yaml cannot be read or parsed.
        """
        tickets_file = plan_dir / "tickets.yaml"
        
        if not tickets_file.exists():
            return []
        
        try:
            with open(tickets_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise TicketLoadError(f"Invalid YAML in {tickets_file}: {e}")
        except IOError as e:
            raise TicketLoadError(f"Cannot read {tickets_file}: {e}")
        
        if not isinstance(data, dict):
            raise TicketLoadError(f"Invalid tickets.yaml format: expected dict, got {type(data).__name__}")
        
        plan_name = plan_dir.name
        tickets: list[Ticket] = []
        
        # Parse slices
        slices_data = data.get("slices", [])
        if isinstance(slices_data, list):
            for slice_data in slices_data:
                try:
                    ticket = self._parse_slice(slice_data, plan_name, plan_dir)
                    if ticket:
                        tickets.append(ticket)
                except Exception as e:
                    slice_key = slice_data.get("key", "unknown") if isinstance(slice_data, dict) else "unknown"
                    logger.warning(f"Failed to parse slice {slice_key} in {plan_name}: {e}")
        
        # Parse epic if present
        epic_data = data.get("epic")
        if isinstance(epic_data, dict):
            try:
                epic_ticket = self._parse_epic(epic_data, plan_name, plan_dir)
                if epic_ticket:
                    tickets.append(epic_ticket)
            except Exception as e:
                logger.warning(f"Failed to parse epic in {plan_name}: {e}")
        
        return tickets
    
    def _parse_slice(self, data: dict, plan_name: str, plan_dir: Path) -> Optional[Ticket]:
        """Parse a slice definition into a Ticket.
        
        Args:
            data: Raw slice data from YAML
            plan_name: Name of the plan directory
            plan_dir: Full path to plan directory
            
        Returns:
            Ticket object or None if invalid.
        """
        if not isinstance(data, dict):
            return None
        
        key = data.get("key")
        if not key:
            return None
        
        # Get description
        description = data.get("description", "")
        if isinstance(description, list):
            description = "\n".join(str(line) for line in description)
        
        # Build ticket
        # Normalize assignee to string or None
        raw_assignee = data.get("assignee")
        assignee = str(raw_assignee) if raw_assignee is not None else None
        
        ticket = Ticket(
            id=str(key),
            title=str(data.get("title", "Untitled")),
            body=str(description) if description else "",
            deps=self._parse_deps(data.get("blocked_by")),
            tags=self._parse_tags(data.get("tags")),
            assignee=assignee,
            priority=data.get("priority"),
            ticket_type=data.get("type", "feature"),
            plan_name=plan_name,
            plan_dir=str(plan_dir),
            external_ref=data.get("external_ref"),
        )
        
        # Refresh status from tk CLI
        ticket.status = self.refresh_status(ticket.id)
        
        return ticket
    
    def _parse_epic(self, data: dict, plan_name: str, plan_dir: Path) -> Optional[Ticket]:
        """Parse an epic definition into a Ticket.
        
        Args:
            data: Raw epic data from YAML
            plan_name: Name of the plan directory
            plan_dir: Full path to plan directory
            
        Returns:
            Ticket object or None if invalid.
        """
        if not isinstance(data, dict):
            return None
        
        title = data.get("title")
        if not title:
            return None
        
        # Get description
        description = data.get("description", "")
        if isinstance(description, list):
            description = "\n".join(str(line) for line in description)
        
        # Use plan name as epic ID
        epic_id = f"epic-{plan_name}"
        
        # Normalize assignee to string or None
        raw_assignee = data.get("assignee")
        assignee = str(raw_assignee) if raw_assignee is not None else None
        
        ticket = Ticket(
            id=epic_id,
            title=str(title),
            body=str(description) if description else "",
            deps=self._parse_deps(data.get("blocked_by")),
            tags=self._parse_tags(data.get("tags")),
            assignee=assignee,
            priority=data.get("priority"),
            ticket_type="epic",
            plan_name=plan_name,
            plan_dir=str(plan_dir),
            external_ref=data.get("external_ref"),
        )
        
        # Refresh status from tk CLI
        ticket.status = self.refresh_status(ticket.id)
        
        return ticket
    
    def _parse_deps(self, blocked_by: Optional[list | str]) -> list[str]:
        """Parse blocked_by field into list of dependency IDs."""
        if blocked_by is None:
            return []
        if isinstance(blocked_by, str):
            return [blocked_by] if blocked_by else []
        if isinstance(blocked_by, list):
            return [str(d) for d in blocked_by if d]
        return []
    
    def _parse_tags(self, tags: Optional[list | str]) -> list[str]:
        """Parse tags field into list of tag strings."""
        if tags is None:
            return []
        if isinstance(tags, str):
            return [tags] if tags else []
        if isinstance(tags, list):
            return [str(t) for t in tags if t]
        return []
    
    def refresh_status(self, ticket_id: str) -> str:
        """Query tk CLI for current ticket status.
        
        Uses caching to avoid repeated queries for the same ticket
        in a single load operation.
        
        Args:
            ticket_id: The ticket ID to query
            
        Returns:
            Status string ("open", "in_progress", "closed", etc.)
            Returns "open" if the query fails.
        """
        if ticket_id in self._status_cache:
            return self._status_cache[ticket_id]
        
        status = self._query_tk_status(ticket_id)
        self._status_cache[ticket_id] = status
        return status
    
    def _query_tk_status(self, ticket_id: str) -> str:
        """Execute tk CLI to get ticket status.
        
        Args:
            ticket_id: The ticket ID to query
            
        Returns:
            Status string, defaults to "open" on any failure.
        """
        try:
            result = subprocess.run(
                ["tk", "show", ticket_id, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode != 0:
                logger.debug(f"tk show failed for {ticket_id}: {result.stderr}")
                return "open"
            
            data = json.loads(result.stdout)
            
            # Handle different JSON structures
            # Try "status" field directly, or nested in "ticket" or "data"
            status = data.get("status")
            if status is None and "ticket" in data:
                status = data["ticket"].get("status")
            if status is None and "data" in data:
                status = data["data"].get("status")
            
            return str(status) if status else "open"
            
        except subprocess.TimeoutExpired:
            logger.warning(f"tk show timed out for {ticket_id}")
            return "open"
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from tk show {ticket_id}: {e}")
            return "open"
        except FileNotFoundError:
            # tk CLI not installed
            logger.debug("tk CLI not found, defaulting all statuses to 'open'")
            return "open"
        except Exception as e:
            logger.debug(f"Error querying tk for {ticket_id}: {e}")
            return "open"
