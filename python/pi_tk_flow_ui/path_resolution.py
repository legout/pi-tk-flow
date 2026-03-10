"""Helpers for resolving project-relative pi-tk-flow paths.

These helpers keep discovery anchored to the current project so a global
`~/.tf` directory does not accidentally hijack path resolution for unrelated
repositories.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_BOUNDARY_MARKERS = (".git", "PROJECT.md", "AGENTS.md")


@dataclass(frozen=True)
class SearchScope:
    """Bounded ancestor search configuration.

    Attributes:
        ancestors: Ordered ancestor list from cwd outward.
        fallback_base: Base directory to use when no workflow artifacts exist yet.
    """

    ancestors: tuple[Path, ...]
    fallback_base: Path


def _has_project_boundary(path: Path) -> bool:
    """Return True when the path looks like a project root/boundary."""
    return any((path / marker).exists() for marker in PROJECT_BOUNDARY_MARKERS)


def build_search_scope(start: Path | None = None) -> SearchScope:
    """Build a bounded ancestor search scope from the current directory.

    Resolution prefers staying inside the current repository/project boundary.
    If no explicit project boundary is found, searches do not climb into the
    user's home directory when started from a child directory, which avoids
    accidentally picking up an unrelated global `~/.tf` workspace.
    """

    cwd = (start or Path.cwd()).resolve()
    ancestors = [cwd, *cwd.parents]

    for index, parent in enumerate(ancestors):
        if _has_project_boundary(parent):
            return SearchScope(tuple(ancestors[: index + 1]), parent)

    home = Path.home().resolve()
    if cwd != home and home in ancestors:
        home_index = ancestors.index(home)
        bounded_ancestors = tuple(ancestors[:home_index])
        if bounded_ancestors:
            return SearchScope(bounded_ancestors, cwd)

    return SearchScope(tuple(ancestors), cwd)


def resolve_tickets_dir(start: Path | None = None) -> Path:
    """Resolve the `.tickets` directory for the current project."""

    scope = build_search_scope(start)

    for parent in scope.ancestors:
        candidate = parent / ".tickets"
        if candidate.is_dir():
            return candidate

    for parent in scope.ancestors:
        if (parent / ".tf").is_dir():
            return parent / ".tickets"

    return scope.fallback_base / ".tickets"


def resolve_plans_dir(start: Path | None = None) -> Path:
    """Resolve the `.tf/plans` directory for the current project."""

    scope = build_search_scope(start)

    for parent in scope.ancestors:
        candidate = parent / ".tf" / "plans"
        if candidate.is_dir():
            return candidate

    return scope.fallback_base / ".tf" / "plans"
