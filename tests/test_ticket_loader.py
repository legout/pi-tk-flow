"""Tests for ticket_loader module with markdown frontmatter parsing."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from pi_tk_flow_ui.ticket_loader import (
    Ticket,
    TicketLoadError,
    YamlTicketLoader,
)


@pytest.fixture
def sample_tickets_dir(sample_project_fixture_dir: Path) -> Path:
    """Return the path to the sample tickets directory."""
    return sample_project_fixture_dir / ".tickets"


@pytest.fixture
def tmp_tickets_dir(tmp_path: Path) -> Path:
    """Create a temporary tickets directory."""
    tickets_dir = tmp_path / ".tickets"
    tickets_dir.mkdir()
    return tickets_dir


class TestTicket:
    """Test Ticket dataclass."""
    
    def test_ticket_creation(self):
        """Test basic ticket creation."""
        ticket = Ticket(
            id="TEST-1",
            status="open",
            title="Test Ticket",
            file_path=Path("/tmp/test.md"),
        )
        
        assert ticket.id == "TEST-1"
        assert ticket.title == "Test Ticket"
        assert ticket.status == "open"
        assert ticket.deps == []
        assert ticket.tags == []
    
    def test_ticket_lazy_body_loading(self, tmp_tickets_dir: Path):
        """Test that body is loaded lazily from file."""
        ticket_file = tmp_tickets_dir / "test.md"
        ticket_file.write_text("""---
id: test-ticket
status: open
---
# Test Title

Body content here.
""")
        
        ticket = Ticket(
            id="test-ticket",
            status="open",
            title="Test Title",
            file_path=ticket_file,
        )
        
        # Body should be empty before access
        assert ticket._body is None
        assert not ticket._body_loaded
        
        # Access body
        body = ticket.body
        assert "Body content here." in body
        assert ticket._body_loaded


class TestYamlTicketLoader:
    """Test YamlTicketLoader with markdown ticket files."""
    
    def test_load_all_tickets(self, sample_tickets_dir: Path):
        """Test loading all tickets from the sample fixture."""
        loader = YamlTicketLoader(sample_tickets_dir)
        tickets = loader.load_all()
        
        # Should have 4 tickets from sample fixtures
        assert len(tickets) == 4
        
        # Build ticket lookup
        ticket_map = {t.id: t for t in tickets}
        
        # Verify all expected tickets loaded
        assert "t1-open" in ticket_map
        assert "t2-blocked" in ticket_map
        assert "t3-inprogress" in ticket_map
        assert "t4-closed" in ticket_map
    
    def test_ticket_field_mapping(self, sample_tickets_dir: Path):
        """Test that all YAML frontmatter fields are mapped correctly."""
        loader = YamlTicketLoader(sample_tickets_dir)
        tickets = loader.load_all()
        
        ticket_map = {t.id: t for t in tickets}
        
        # Check open ticket
        t1 = ticket_map["t1-open"]
        assert t1.status == "open"
        assert t1.title == "Open ticket ready to work"
        assert t1.priority == 1
        assert t1.assignee == "tester"
        assert t1.ticket_type == "feature"
        assert t1.tags == ["ready", "feature"]
        assert t1.deps == []
        
        # Check blocked ticket
        t2 = ticket_map["t2-blocked"]
        assert t2.status == "open"
        assert t2.deps == ["t1-open"]
        assert t2.priority == 2
        
        # Check in-progress ticket
        t3 = ticket_map["t3-inprogress"]
        assert t3.status == "in_progress"
        
        # Check closed ticket
        t4 = ticket_map["t4-closed"]
        assert t4.status == "closed"
    
    def test_missing_tickets_directory_raises_error(self, tmp_path: Path):
        """Missing .tickets directory should raise TicketLoadError."""
        loader = YamlTicketLoader(tmp_path / ".tickets")
        
        with pytest.raises(TicketLoadError) as exc_info:
            loader.load_all()
        
        assert "Tickets directory not found" in str(exc_info.value)
    
    def test_empty_tickets_directory(self, tmp_tickets_dir: Path):
        """Empty tickets directory returns empty list."""
        loader = YamlTicketLoader(tmp_tickets_dir)
        tickets = loader.load_all()
        
        assert tickets == []
    
    def test_malformed_ticket_skipped_with_warning(self, tmp_tickets_dir: Path):
        """Malformed tickets are skipped with a warning."""
        # Create a valid ticket
        (tmp_tickets_dir / "valid.md").write_text("""---
id: valid
status: open
---
# Valid Ticket
""")
        
        # Create a malformed ticket (no frontmatter)
        (tmp_tickets_dir / "invalid.md").write_text("""# No Frontmatter

This ticket has no YAML frontmatter.
""")
        
        loader = YamlTicketLoader(tmp_tickets_dir)
        tickets = loader.load_all()
        
        # Should only have the valid ticket
        assert len(tickets) == 1
        assert tickets[0].id == "valid"
    
    def test_get_by_id(self, sample_tickets_dir: Path):
        """Test retrieving a ticket by ID."""
        loader = YamlTicketLoader(sample_tickets_dir)
        loader.load_all()
        
        ticket = loader.get_by_id("t1-open")
        assert ticket is not None
        assert ticket.title == "Open ticket ready to work"
        
        # Non-existent ticket
        assert loader.get_by_id("nonexistent") is None
    
    def test_get_by_status(self, sample_tickets_dir: Path):
        """Test filtering tickets by status."""
        loader = YamlTicketLoader(sample_tickets_dir)
        loader.load_all()
        
        open_tickets = loader.get_by_status("open")
        assert len(open_tickets) == 2  # t1-open, t2-blocked
        
        closed_tickets = loader.get_by_status("closed")
        assert len(closed_tickets) == 1  # t4-closed
    
    def test_search_by_title(self, sample_tickets_dir: Path):
        """Test searching tickets by title."""
        loader = YamlTicketLoader(sample_tickets_dir)
        loader.load_all()
        
        results = loader.search("ready")
        assert len(results) == 1
        assert results[0].id == "t1-open"
    
    def test_search_by_id(self, sample_tickets_dir: Path):
        """Test searching tickets by ID."""
        loader = YamlTicketLoader(sample_tickets_dir)
        loader.load_all()
        
        results = loader.search("blocked")
        assert len(results) == 1
        assert results[0].id == "t2-blocked"
    
    def test_search_by_tag(self, sample_tickets_dir: Path):
        """Test searching tickets by tag."""
        loader = YamlTicketLoader(sample_tickets_dir)
        loader.load_all()
        
        results = loader.search("feature")
        assert len(results) == 2  # t1-open, t2-blocked
    
    def test_search_case_insensitive(self, sample_tickets_dir: Path):
        """Search should be case-insensitive."""
        loader = YamlTicketLoader(sample_tickets_dir)
        loader.load_all()
        
        results_lower = loader.search("open")
        results_upper = loader.search("OPEN")
        
        assert len(results_lower) == len(results_upper)
    
    def test_count_by_status(self, sample_tickets_dir: Path):
        """Test status counting."""
        loader = YamlTicketLoader(sample_tickets_dir)
        loader.load_all()
        
        counts = loader.count_by_status
        
        assert counts["open"] == 2
        assert counts["in_progress"] == 1
        assert counts["closed"] == 1
    
    def test_refresh_reloads_tickets(self, tmp_tickets_dir: Path):
        """Test refresh=True reloads tickets."""
        # Create initial ticket
        (tmp_tickets_dir / "ticket.md").write_text("""---
id: ticket-1
status: open
---
# Ticket 1
""")
        
        loader = YamlTicketLoader(tmp_tickets_dir)
        tickets = loader.load_all()
        assert len(tickets) == 1
        
        # Add another ticket
        (tmp_tickets_dir / "ticket2.md").write_text("""---
id: ticket-2
status: open
---
# Ticket 2
""")
        
        # Without refresh, still get 1
        tickets = loader.load_all()
        assert len(tickets) == 1
        
        # With refresh, get 2
        tickets = loader.load_all(refresh=True)
        assert len(tickets) == 2
    
    def test_no_load_before_get_by_id_raises(self, sample_tickets_dir: Path):
        """Calling get_by_id before load_all should raise error."""
        loader = YamlTicketLoader(sample_tickets_dir)
        
        with pytest.raises(TicketLoadError):
            loader.get_by_id("any-id")


class TestTicketLoaderPaths:
    """Test path resolution for tickets directory."""

    def test_resolve_tickets_dir_finds_tf_parent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Loader should find .tickets next to a project-local .tf directory."""
        (tmp_path / ".tf").mkdir()
        (tmp_path / ".tickets").mkdir()

        (tmp_path / ".tickets" / "test.md").write_text("""---
id: test
status: open
---
# Test
""")

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        loader = YamlTicketLoader()

        assert loader.tickets_dir == tmp_path / ".tickets"
        assert [ticket.id for ticket in loader.load_all()] == ["test"]

    def test_prefers_repo_tickets_over_unrelated_ancestor_tf(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Repo-local .tickets should win over an unrelated ancestor .tf directory."""
        outer = tmp_path / "outer"
        project = outer / "coding" / "example-project"
        subdir = project / "src"

        (outer / ".tf").mkdir(parents=True)
        (project / ".git").mkdir(parents=True)
        (project / ".tickets").mkdir(parents=True)
        subdir.mkdir(parents=True)

        (project / ".tickets" / "local.md").write_text("""---
id: local-ticket
status: open
---
# Local Ticket
""", encoding="utf-8")

        monkeypatch.chdir(subdir)

        loader = YamlTicketLoader()

        assert loader.tickets_dir == project / ".tickets"
        assert [ticket.id for ticket in loader.load_all()] == ["local-ticket"]
