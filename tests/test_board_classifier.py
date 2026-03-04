"""Tests for board_classifier module."""

import pytest

from pi_tk_flow_ui.board_classifier import (
    BoardColumn,
    BoardClassifier,
    BoardView,
    ClassifiedTicket,
)
from pi_tk_flow_ui.ticket_loader import Ticket


class TestBoardColumn:
    """Test BoardColumn enum."""
    
    def test_column_values(self):
        """Test column enum values."""
        assert BoardColumn.READY.value == "ready"
        assert BoardColumn.BLOCKED.value == "blocked"
        assert BoardColumn.IN_PROGRESS.value == "in_progress"
        assert BoardColumn.CLOSED.value == "closed"


class TestClassifiedTicket:
    """Test ClassifiedTicket dataclass."""
    
    def test_creation(self):
        """Test creating a classified ticket."""
        ticket = Ticket(id="T1", title="Test", body="", plan_name="p")
        ct = ClassifiedTicket(
            ticket=ticket,
            column=BoardColumn.READY,
            blocking_deps=[]
        )
        
        assert ct.id == "T1"
        assert ct.title == "Test"
        assert ct.column == BoardColumn.READY
        assert ct.blocking_deps == []


class TestBoardView:
    """Test BoardView dataclass."""
    
    def test_get_by_column(self):
        """Test filtering tickets by column."""
        t1 = Ticket(id="T1", title="Ready", body="", status="open", plan_name="p")
        t2 = Ticket(id="T2", title="Closed", body="", status="closed", plan_name="p")
        
        view = BoardView(tickets=[
            ClassifiedTicket(ticket=t1, column=BoardColumn.READY),
            ClassifiedTicket(ticket=t2, column=BoardColumn.CLOSED),
        ])
        
        ready_tickets = view.get_by_column(BoardColumn.READY)
        assert len(ready_tickets) == 1
        assert ready_tickets[0].id == "T1"
    
    def test_counts(self):
        """Test ticket count by column."""
        view = BoardView(tickets=[
            ClassifiedTicket(ticket=Ticket(id="T1", title="R1", body="", plan_name="p"), column=BoardColumn.READY),
            ClassifiedTicket(ticket=Ticket(id="T2", title="R2", body="", plan_name="p"), column=BoardColumn.READY),
            ClassifiedTicket(ticket=Ticket(id="T3", title="C1", body="", plan_name="p"), column=BoardColumn.CLOSED),
        ])
        
        counts = view.counts
        assert counts["ready"] == 2
        assert counts["closed"] == 1
        assert counts["blocked"] == 0
        assert counts["in_progress"] == 0


class TestBoardClassifier:
    """Test BoardClassifier functionality."""
    
    def test_classify_closed_ticket(self):
        """Test that closed tickets go to CLOSED column."""
        ticket = Ticket(id="T1", title="Done", body="", status="closed", plan_name="p")
        classifier = BoardClassifier([ticket])
        
        result = classifier.classify()
        
        assert len(result.tickets) == 1
        assert result.tickets[0].column == BoardColumn.CLOSED
        assert result.tickets[0].blocking_deps == []
    
    def test_classify_ready_ticket(self):
        """Test that open tickets without blockers go to READY column."""
        ticket = Ticket(id="T1", title="Ready", body="", status="open", deps=[], plan_name="p")
        classifier = BoardClassifier([ticket])
        
        result = classifier.classify()
        
        assert result.tickets[0].column == BoardColumn.READY
    
    def test_classify_blocked_by_open_dep(self):
        """Test that tickets with open dependencies are BLOCKED."""
        # T1 is open, T2 depends on T1
        t1 = Ticket(id="T1", title="Dep", body="", status="open", plan_name="p")
        t2 = Ticket(id="T2", title="Blocked", body="", status="open", deps=["T1"], plan_name="p")
        
        classifier = BoardClassifier([t1, t2])
        result = classifier.classify()
        
        t1_classified = next(ct for ct in result.tickets if ct.id == "T1")
        t2_classified = next(ct for ct in result.tickets if ct.id == "T2")
        
        assert t1_classified.column == BoardColumn.READY
        assert t2_classified.column == BoardColumn.BLOCKED
        assert "T1" in t2_classified.blocking_deps
    
    def test_classify_not_blocked_by_closed_dep(self):
        """Test that tickets with closed dependencies are not blocked."""
        # T1 is closed, T2 depends on T1
        t1 = Ticket(id="T1", title="Done", body="", status="closed", plan_name="p")
        t2 = Ticket(id="T2", title="Unblocked", body="", status="open", deps=["T1"], plan_name="p")
        
        classifier = BoardClassifier([t1, t2])
        result = classifier.classify()
        
        t2_classified = next(ct for ct in result.tickets if ct.id == "T2")
        
        assert t2_classified.column == BoardColumn.READY
        assert t2_classified.blocking_deps == []
    
    def test_classify_blocked_by_unknown_dep(self):
        """Test that unknown dependencies are treated as blockers."""
        ticket = Ticket(
            id="T1",
            title="Unknown dep",
            body="",
            status="open",
            deps=["UNKNOWN"],
            plan_name="p"
        )
        
        classifier = BoardClassifier([ticket])
        result = classifier.classify()
        
        assert result.tickets[0].column == BoardColumn.BLOCKED
        assert "UNKNOWN" in result.tickets[0].blocking_deps
    
    def test_classify_in_progress(self):
        """Test that in_progress tickets go to IN_PROGRESS column."""
        ticket = Ticket(id="T1", title="WIP", body="", status="in_progress", deps=[], plan_name="p")
        classifier = BoardClassifier([ticket])
        
        result = classifier.classify()
        
        assert result.tickets[0].column == BoardColumn.IN_PROGRESS
    
    def test_classify_in_progress_with_blocker(self):
        """Test that in_progress tickets with blockers still go to BLOCKED."""
        t1 = Ticket(id="T1", title="Dep", body="", status="open", plan_name="p")
        t2 = Ticket(
            id="T2",
            title="WIP but blocked",
            body="",
            status="in_progress",
            deps=["T1"],
            plan_name="p"
        )
        
        classifier = BoardClassifier([t1, t2])
        result = classifier.classify()
        
        t2_classified = next(ct for ct in result.tickets if ct.id == "T2")
        
        # Blocked takes precedence over in_progress
        assert t2_classified.column == BoardColumn.BLOCKED
    
    def test_multiple_blocking_deps(self):
        """Test tracking multiple blocking dependencies."""
        t1 = Ticket(id="T1", title="Open1", body="", status="open", plan_name="p")
        t2 = Ticket(id="T2", title="Open2", body="", status="open", plan_name="p")
        t3 = Ticket(id="T3", title="Done", body="", status="closed", plan_name="p")
        t4 = Ticket(
            id="T4",
            title="Blocked",
            body="",
            status="open",
            deps=["T1", "T2", "T3"],
            plan_name="p"
        )
        
        classifier = BoardClassifier([t1, t2, t3, t4])
        result = classifier.classify()
        
        t4_classified = next(ct for ct in result.tickets if ct.id == "T4")
        
        assert t4_classified.column == BoardColumn.BLOCKED
        assert "T1" in t4_classified.blocking_deps
        assert "T2" in t4_classified.blocking_deps
        # T3 is closed, so not blocking
        assert "T3" not in t4_classified.blocking_deps
    
    def test_is_blocked_method(self):
        """Test the is_blocked helper method."""
        t1 = Ticket(id="T1", title="Dep", body="", status="open", plan_name="p")
        t2 = Ticket(id="T2", title="Blocked", body="", status="open", deps=["T1"], plan_name="p")
        
        classifier = BoardClassifier([t1, t2])
        classifier._ticket_map = {"T1": t1, "T2": t2}
        
        assert classifier.is_blocked(t2) is True
        assert classifier.is_blocked(t1) is False
    
    def test_get_ready_tickets(self):
        """Test get_ready_tickets helper method."""
        t1 = Ticket(id="T1", title="Ready", body="", status="open", deps=[], plan_name="p")
        t2 = Ticket(id="T2", title="Blocked", body="", status="open", deps=["T1"], plan_name="p")
        t3 = Ticket(id="T3", title="In Progress", body="", status="in_progress", deps=[], plan_name="p")
        t4 = Ticket(id="T4", title="Closed", body="", status="closed", plan_name="p")
        
        classifier = BoardClassifier([t1, t2, t3, t4])
        ready = classifier.get_ready_tickets()
        
        # Only t1 is ready (open, no blockers, not in_progress)
        assert len(ready) == 1
        assert ready[0].id == "T1"
    
    def test_empty_ticket_list(self):
        """Test classification with empty ticket list."""
        classifier = BoardClassifier([])
        result = classifier.classify()
        
        assert result.tickets == []
        assert result.counts == {
            "ready": 0,
            "blocked": 0,
            "in_progress": 0,
            "closed": 0,
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
