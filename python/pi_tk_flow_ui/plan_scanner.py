"""Plan scanning for browsing plan directories.

This module provides on-the-fly scanning of .tf/plans/<plan-dir>/ directories
with metadata extraction from plan documents.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .path_resolution import resolve_plans_dir

logger = logging.getLogger(__name__)


@dataclass
class Plan:
    """Represents a plan directory.
    
    Attributes:
        id: Plan identifier (directory name)
        title: Extracted title from PRD or directory name
        plan_date: Date from directory name (YYYY-MM-DD)
        plan_topic: Topic slug from directory name
        dir_path: Full path to the plan directory
        prd_path: Path to 01-prd.md if exists
        spec_path: Path to 02-spec.md if exists
        impl_plan_path: Path to 03-implementation-plan.md or 03-plan.md if exists
        ticket_breakdown_path: Path to 04-ticket-breakdown.md if exists
            (falls back to legacy 04-progress.md for older plans)
        status: Status from PRD frontmatter (Draft, Active, Complete, etc.)
    """
    id: str
    title: str
    plan_date: str
    plan_topic: str
    dir_path: Path
    prd_path: Optional[Path] = None
    spec_path: Optional[Path] = None
    impl_plan_path: Optional[Path] = None
    ticket_breakdown_path: Optional[Path] = None
    status: str = "Unknown"


class PlanScanner:
    """Scans plan directories from .tf/plans/.
    
    This scanner:
    1. Finds all subdirectories in .tf/plans/
    2. Extracts metadata from directory name (date-topic format)
    3. Locates key plan documents (prd, spec, implementation plan, ticket breakdown)
    4. Returns sorted plan metadata
    
    Directory name format: YYYY-MM-DD-<topic-slug>
    
    Example:
        >>> scanner = PlanScanner()
        >>> plans = scanner.scan()
        >>> for plan in plans:
        ...     print(f"{plan.plan_date}: {plan.title}")
    """
    
    def __init__(self, plans_dir: Optional[Path] = None):
        """Initialize the scanner.
        
        Args:
            plans_dir: Path to plans directory. If None, auto-discovers.
        """
        if plans_dir is None:
            plans_dir = self._find_plans_dir()
        
        self.plans_dir = Path(plans_dir)
    
    def _find_plans_dir(self) -> Path:
        """Find the current project's plans directory."""
        return resolve_plans_dir()
    
    def scan(self) -> list[Plan]:
        """Scan all plans from the plans directory.
        
        Returns:
            List of Plan objects sorted by date (newest first).
            Returns empty list if plans directory doesn't exist.
        """
        if not self.plans_dir.exists():
            logger.debug(f"Plans directory not found: {self.plans_dir}")
            return []
        
        plans: list[Plan] = []
        
        try:
            for entry in self.plans_dir.iterdir():
                if not entry.is_dir():
                    continue
                if entry.name.startswith("."):
                    continue
                
                try:
                    plan = self._parse_plan(entry)
                    if plan:
                        plans.append(plan)
                except Exception as e:
                    logger.warning(f"Failed to parse plan {entry.name}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error scanning plans directory: {e}")
            return []
        
        # Sort by date (newest first), then by topic name
        plans.sort(key=lambda p: (p.plan_date, p.plan_topic), reverse=True)
        
        return plans
    
    def _parse_plan(self, dir_path: Path) -> Optional[Plan]:
        """Parse a single plan directory.
        
        Args:
            dir_path: Path to the plan directory
            
        Returns:
            Plan object or None if invalid
        """
        dir_name = dir_path.name
        
        # Parse directory name: YYYY-MM-DD-<topic-slug>
        date_match = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)$", dir_name)
        if date_match:
            plan_date = date_match.group(1)
            plan_topic = date_match.group(2)
        else:
            # Fallback: use directory name as topic, no date
            plan_date = ""
            plan_topic = dir_name
        
        # Find key documents
        prd_path = dir_path / "01-prd.md"
        spec_path = dir_path / "02-spec.md"
        impl_plan_path = self._first_existing(
            dir_path,
            ["03-implementation-plan.md", "03-plan.md"],
        )
        ticket_breakdown_path = self._first_existing(
            dir_path,
            ["04-ticket-breakdown.md", "04-progress.md"],
        )
        
        # Extract title and status from PRD if available
        title = plan_topic.replace("-", " ").title()
        status = "Unknown"
        
        if prd_path.exists():
            try:
                content = prd_path.read_text(encoding="utf-8")
                extracted_title = self._extract_title(content)
                if extracted_title:
                    title = extracted_title
                extracted_status = self._extract_status(content)
                if extracted_status:
                    status = extracted_status
            except Exception as e:
                logger.debug(f"Error reading PRD {prd_path}: {e}")
        
        return Plan(
            id=dir_name,
            title=title,
            plan_date=plan_date,
            plan_topic=plan_topic,
            dir_path=dir_path,
            prd_path=prd_path if prd_path.exists() else None,
            spec_path=spec_path if spec_path.exists() else None,
            impl_plan_path=impl_plan_path,
            ticket_breakdown_path=ticket_breakdown_path,
            status=status
        )
    
    def _first_existing(self, dir_path: Path, filenames: list[str]) -> Optional[Path]:
        """Return the first existing file from a list of candidate names."""
        for name in filenames:
            candidate = dir_path / name
            if candidate.exists():
                return candidate
        return None

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from first # heading in markdown.
        
        Args:
            content: Markdown file content
            
        Returns:
            Title string or None if no heading found
        """
        # Look for first # heading (not ## or ###)
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# ") and not line.startswith("##"):
                # Extract title (remove # and whitespace)
                title = line[2:].strip()
                # Remove any formatting
                title = re.sub(r"\*\*|__|\*|_", "", title)
                # Remove "PRD:" or similar prefixes
                title = re.sub(r"^(PRD|SPEC|Plan):\s*", "", title, flags=re.IGNORECASE)
                return title
        
        return None
    
    def _extract_status(self, content: str) -> Optional[str]:
        """Extract status from PRD frontmatter.
        
        Args:
            content: Markdown file content
            
        Returns:
            Status string or None if not found
        """
        # Check for YAML frontmatter
        if not content.startswith("---"):
            # Try to find Status field inline
            status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
            if status_match:
                return status_match.group(1)
            return None
        
        try:
            # Find end of frontmatter
            end_match = re.search(r"\n---\s*\n", content[3:])
            if not end_match:
                return None
            
            frontmatter = content[3:3+end_match.start()]
            
            # Parse frontmatter as YAML for robust status extraction
            try:
                import yaml
                data = yaml.safe_load(frontmatter)
                if isinstance(data, dict):
                    if "status" in data:
                        return str(data["status"])
            except ImportError:
                pass
            
            # Fallback: Look for status field with regex
            status_match = re.search(r"^status:\s*(.+)$", frontmatter, re.MULTILINE | re.IGNORECASE)
            if status_match:
                return status_match.group(1).strip()
            
            # Also check for **Status**: inline format
            status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
            if status_match:
                return status_match.group(1)
            
        except Exception as e:
            logger.debug(f"Error extracting status: {e}")
        
        return None
    
    def get_by_id(self, plan_id: str) -> Optional[Plan]:
        """Get a plan by its ID.
        
        Args:
            plan_id: The plan ID to look up
            
        Returns:
            The plan if found, None otherwise
        """
        plans = self.scan()
        for plan in plans:
            if plan.id == plan_id:
                return plan
        return None
    
    def search(self, query: str) -> list[Plan]:
        """Search plans by query string.
        
        Searches in:
        - Plan ID
        - Title
        - Topic
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of matching plans
        """
        plans = self.scan()
        query_lower = query.lower()
        
        results = []
        for plan in plans:
            # Search in ID
            if query_lower in plan.id.lower():
                results.append(plan)
                continue
            # Search in title
            if query_lower in plan.title.lower():
                results.append(plan)
                continue
            # Search in topic
            if query_lower in plan.plan_topic.lower():
                results.append(plan)
                continue
            # Search in date
            if query_lower in plan.plan_date.lower():
                results.append(plan)
                continue
        
        return results
