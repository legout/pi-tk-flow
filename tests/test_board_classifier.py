"""Tests for board_classifier module with markdown tickets."""

import pytest

from pi_tk_flow_ui.board_classifier import (
    BoardColumn,
    BoardClassifier,
    BoardView,
    ClassifiedTicket,
)
from pi_tk_flow_ui.ticket_loader import Ticket


class TestBoardClassifierWithFixtures:
    """Test BoardClassifier using markdown ticket fixtures."""

    def test_classify_fixture_tickets(self, sample_tickets_dir):
        """Test classification of tickets from fixtures."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader

        loader = YamlTicketLoader(sample_tickets_dir)
        tickets = loader.load_all()

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        classified_map = {ct.id: ct for ct in view.tickets}

        # t1-open: open, no deps -> READY
        assert classified_map["t1-open"].column == BoardColumn.READY

        # t2-blocked: open, depends on t1-open -> BLOCKED
        assert classified_map["t2-blocked"].column == BoardColumn.BLOCKED
        assert "t1-open" in classified_map["t2-blocked"].blocking_deps

        # t3-inprogress: in_progress, no deps -> IN_PROGRESS
        assert classified_map["t3-inprogress"].column == BoardColumn.IN_PROGRESS

        # t4-closed: closed -> CLOSED
        assert classified_map["t4-closed"].column == BoardColumn.CLOSED

    def test_counts_match_expected(self, sample_tickets_dir):
        """Test that column counts match expected values."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader

        loader = YamlTicketLoader(sample_tickets_dir)
        tickets = loader.load_all()

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        counts = view.counts

        assert counts["ready"] == 1      # t1-open
        assert counts["blocked"] == 1    # t2-blocked
        assert counts["in_progress"] == 1  # t3-inprogress
        assert counts["closed"] == 1     # t4-closed

    def test_get_by_column(self, sample_tickets_dir):
        """Test retrieving tickets by column."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader

        loader = YamlTicketLoader(sample_tickets_dir)
        tickets = loader.load_all()

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        ready = view.get_by_column(BoardColumn.READY)
        assert len(ready) == 1
        assert ready[0].id == "t1-open"

        blocked = view.get_by_column(BoardColumn.BLOCKED)
        assert len(blocked) == 1
        assert blocked[0].id == "t2-blocked"

    def test_closed_ticket_with_deps_stays_closed(self, sample_tickets_dir):
        """Test CLOSED precedence: even with open deps, closed tickets stay CLOSED."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader

        loader = YamlTicketLoader(sample_tickets_dir)
        tickets = loader.load_all()

        ticket_map = {t.id: t for t in tickets}

        # Modify t4-closed to depend on t1-open (which is open)
        ticket_map["t4-closed"].deps = ["t1-open"]

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        t4_classified = next(ct for ct in view.tickets if ct.id == "t4-closed")

        # CLOSED takes precedence over BLOCKED
        assert t4_classified.column == BoardColumn.CLOSED
        # Blocking deps should be empty for closed tickets
        assert t4_classified.blocking_deps == []

    def test_unknown_dependency_treated_as_blocker(self):
        """Test that unknown dependencies are treated as blockers."""
        tickets = [
            Ticket(
                id="test",
                status="open",
                title="Test",
                file_path=Path("/tmp/test.md"),
                deps=["NONEXISTENT"],
            )
        ]

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        classified = view.tickets[0]
        assert classified.column == BoardColumn.BLOCKED
        assert "NONEXISTENT" in classified.blocking_deps

    def test_in_progress_with_blocking_deps_is_blocked(self):
        """Test that in_progress tickets with blocking deps are shown as blocked."""
        tickets = [
            Ticket(
                id="dep",
                status="open",
                title="Dependency",
                file_path=Path("/tmp/dep.md"),
            ),
            Ticket(
                id="main",
                status="in_progress",
                title="Main Ticket",
                file_path=Path("/tmp/main.md"),
                deps=["dep"],
            ),
        ]

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        classified_map = {ct.id: ct for ct in view.tickets}

        # Even though main is "in_progress", it should be BLOCKED
        # because its dependency is not closed
        assert classified_map["main"].column == BoardColumn.BLOCKED


class TestClassifiedTicket:
    """Test ClassifiedTicket convenience methods."""

    def test_is_methods(self):
        """Test is_ready, is_blocked, is_in_progress, is_closed methods."""
        ticket = Ticket(
            id="test",
            status="open",
            title="Test",
            file_path=Path("/tmp/test.md"),
        )

        ready_ct = ClassifiedTicket(ticket, BoardColumn.READY)
        assert ready_ct.is_ready()
        assert not ready_ct.is_blocked()

        blocked_ct = ClassifiedTicket(ticket, BoardColumn.BLOCKED)
        assert blocked_ct.is_blocked()
        assert not blocked_ct.is_ready()

        in_progress_ct = ClassifiedTicket(ticket, BoardColumn.IN_PROGRESS)
        assert in_progress_ct.is_in_progress()

        closed_ct = ClassifiedTicket(ticket, BoardColumn.CLOSED)
        assert closed_ct.is_closed()

    def test_id_status_title_properties(self):
        """Test convenience properties delegate to ticket."""
        ticket = Ticket(
            id="TEST-123",
            status="open",
            title="Test Title",
            file_path=Path("/tmp/test.md"),
        )

        ct = ClassifiedTicket(ticket, BoardColumn.READY)

        assert ct.id == "TEST-123"
        assert ct.status == "open"
        assert ct.title == "Test Title"


class TestBoardView:
    """Test BoardView methods."""

    def test_empty_board(self):
        """Test empty board view."""
        view = BoardView([])

        assert view.counts == {
            "ready": 0,
            "blocked": 0,
            "in_progress": 0,
            "closed": 0,
        }

    def test_total_count(self):
        """Test total ticket count."""
        tickets = [
            Ticket(id="t1", status="open", title="T1", file_path=Path("/tmp/t1.md")),
            Ticket(id="t2", status="closed", title="T2", file_path=Path("/tmp/t2.md")),
        ]

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        assert len(view.tickets) == 2


class TestBoardClassifierEdgeCases:
    """Test edge cases in board classification."""

    def test_empty_ticket_list(self):
        """Test classifying empty ticket list."""
        classifier = BoardClassifier([])
        view = classifier.classify()

        assert view.tickets == []
        assert view.counts["ready"] == 0

    def test_unknown_status_treated_as_ready(self):
        """Test that unknown status is treated as ready (no deps)."""
        tickets = [
            Ticket(
                id="test",
                status="unknown_status",
                title="Test",
                file_path=Path("/tmp/test.md"),
            ),
        ]

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        assert view.tickets[0].column == BoardColumn.READY

    def test_multiple_deps_all_closed(self):
        """Test ticket with multiple deps all closed."""
        tickets = [
            Ticket(
                id="dep1",
                status="closed",
                title="Dep1",
                file_path=Path("/tmp/d1.md"),
            ),
            Ticket(
                id="dep2",
                status="closed",
                title="Dep2",
                file_path=Path("/tmp/d2.md"),
            ),
            Ticket(
                id="main",
                status="open",
                title="Main",
                file_path=Path("/tmp/main.md"),
                deps=["dep1", "dep2"],
            ),
        ]

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        classified_map = {ct.id: ct for ct in view.tickets}
        assert classified_map["main"].column == BoardColumn.READY

    def test_multiple_deps_some_open(self):
        """Test ticket with mix of closed and open deps."""
        tickets = [
            Ticket(
                id="dep1",
                status="closed",
                title="Dep1",
                file_path=Path("/tmp/d1.md"),
            ),
            Ticket(
                id="dep2",
                status="open",
                title="Dep2",
                file_path=Path("/tmp/d2.md"),
            ),
            Ticket(
                id="main",
                status="open",
                title="Main",
                file_path=Path("/tmp/main.md"),
                deps=["dep1", "dep2"],
            ),
        ]

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        classified_map = {ct.id: ct for ct in view.tickets}
        assert classified_map["main"].column == BoardColumn.BLOCKED
        # Should only list the open dep as blocking
        assert "dep2" in classified_map["main"].blocking_deps
        assert "dep1" not in classified_map["main"].blocking_deps

    def test_circular_deps(self):
        """Test circular dependencies don't cause infinite loops."""
        tickets = [
            Ticket(
                id="a",
                status="open",
                title="A",
                file_path=Path("/tmp/a.md"),
                deps=["b"],
            ),
            Ticket(
                id="b",
                status="open",
                title="B",
                file_path=Path("/tmp/b.md"),
                deps=["a"],
            ),
        ]

        classifier = BoardClassifier(tickets)
        view = classifier.classify()

        # Both should be blocked by each other
        classified_map = {ct.id: ct for ct in view.tickets}
        assert classified_map["a"].column == BoardColumn.BLOCKED
        assert classified_map["b"].column == BoardColumn.BLOCKED


# Import Path for tests that need it
from pathlib import Path
