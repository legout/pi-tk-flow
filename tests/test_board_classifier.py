"""Tests for board_classifier module."""

import pytest

from pi_tk_flow_ui.board_classifier import (
    BoardColumn,
    BoardClassifier,
    BoardView,
    ClassifiedTicket,
)
from pi_tk_flow_ui.ticket_loader import Ticket


class TestBoardClassifierWithFixtures:
    """Test BoardClassifier using deterministic sample fixtures."""
    
    def test_classify_fixture_tickets_precedence_rules(self, sample_project_tf_dir):
        """Test precedence rules: CLOSED > BLOCKED > IN_PROGRESS > READY.
        
        Uses real tickets loaded from fixtures to verify classification.
        """
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader
        
        loader = YamlTicketLoader(sample_project_tf_dir)
        tickets = loader.load_all()
        
        # Manually set statuses for deterministic testing
        ticket_map = {t.id: t for t in tickets}
        
        # S1: open, no deps -> READY
        if "S1" in ticket_map:
            ticket_map["S1"].status = "open"
            ticket_map["S1"].deps = []
        
        # S2: open, depends on S1 -> BLOCKED (S1 is open)
        if "S2" in ticket_map:
            ticket_map["S2"].status = "open"
            ticket_map["S2"].deps = ["S1"]
        
        # S3: in_progress, no deps -> IN_PROGRESS
        if "S3" in ticket_map:
            ticket_map["S3"].status = "in_progress"
            ticket_map["S3"].deps = []
        
        # S4: closed -> CLOSED (takes precedence over everything)
        if "S4" in ticket_map:
            ticket_map["S4"].status = "closed"
            ticket_map["S4"].deps = []
        
        # S5: open, depends on S1 and S2 -> BLOCKED (both open deps)
        if "S5" in ticket_map:
            ticket_map["S5"].status = "open"
            ticket_map["S5"].deps = ["S1", "S2"]
        
        classifier = BoardClassifier(tickets)
        view = classifier.classify()
        
        classified_map = {ct.id: ct for ct in view.tickets}
        
        # Verify precedence rules
        if "S1" in classified_map:
            assert classified_map["S1"].column == BoardColumn.READY, \
                "S1 should be READY (open, no deps)"
        
        if "S2" in classified_map:
            assert classified_map["S2"].column == BoardColumn.BLOCKED, \
                "S2 should be BLOCKED (depends on open S1)"
            assert "S1" in classified_map["S2"].blocking_deps
        
        if "S3" in classified_map:
            assert classified_map["S3"].column == BoardColumn.IN_PROGRESS, \
                "S3 should be IN_PROGRESS (in_progress, no deps)"
        
        if "S4" in classified_map:
            assert classified_map["S4"].column == BoardColumn.CLOSED, \
                "S4 should be CLOSED (closed status)"
        
        if "S5" in classified_map:
            assert classified_map["S5"].column == BoardColumn.BLOCKED, \
                "S5 should be BLOCKED (depends on S1 and S2)"
            assert "S1" in classified_map["S5"].blocking_deps
            assert "S2" in classified_map["S5"].blocking_deps
    
    def test_fixture_closed_ticket_with_deps_stays_closed(self, sample_project_tf_dir):
        """Test CLOSED precedence: even with open deps, closed tickets stay CLOSED."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader
        
        loader = YamlTicketLoader(sample_project_tf_dir)
        tickets = loader.load_all()
        
        ticket_map = {t.id: t for t in tickets}
        
        # Create scenario: S4 is closed but depends on S1 which is open
        if "S4" in ticket_map and "S1" in ticket_map:
            ticket_map["S4"].status = "closed"
            ticket_map["S4"].deps = ["S1"]
            ticket_map["S1"].status = "open"
            
            classifier = BoardClassifier(tickets)
            view = classifier.classify()
            
            s4_classified = next(ct for ct in view.tickets if ct.id == "S4")
            
            # CLOSED takes precedence over BLOCKED
            assert s4_classified.column == BoardColumn.CLOSED
            assert s4_classified.blocking_deps == []  # No blockers needed for closed
    
    def test_fixture_unknown_dependency_treated_as_blocker(self, sample_project_tf_dir):
        """Test that unknown dependencies are treated as blockers."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader
        
        loader = YamlTicketLoader(sample_project_tf_dir)
        tickets = loader.load_all()
        
        # Add a dependency on a non-existent ticket
        ticket_map = {t.id: t for t in tickets}
        if "S1" in ticket_map:
            ticket_map["S1"].status = "open"
            ticket_map["S1"].deps = ["NONEXISTENT-TICKET"]
            
            classifier = BoardClassifier(tickets)
            view = classifier.classify()
            
            s1_classified = next(ct for ct in view.tickets if ct.id == "S1")
            
            assert s1_classified.column == BoardColumn.BLOCKED
            assert "NONEXISTENT-TICKET" in s1_classified.blocking_deps
    
    def test_fixture_mixed_deps_some_blocking(self, sample_project_tf_dir):
        """Test with mix of blocking (open) and non-blocking (closed) deps."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader
        
        loader = YamlTicketLoader(sample_project_tf_dir)
        tickets = loader.load_all()
        
        ticket_map = {t.id: t for t in tickets}
        
        # Set up: S1 closed, S2 open
        if "S1" in ticket_map:
            ticket_map["S1"].status = "closed"
        if "S2" in ticket_map:
            ticket_map["S2"].status = "open"
        
        # Create ticket depending on both S1 (closed) and S2 (open)
        if "S1" in ticket_map and "S2" in ticket_map:
            # Use S3 as the test ticket
            ticket_map["S3"].status = "open"
            ticket_map["S3"].deps = ["S1", "S2"]
            
            classifier = BoardClassifier(tickets)
            view = classifier.classify()
            
            s3_classified = next(ct for ct in view.tickets if ct.id == "S3")
            
            assert s3_classified.column == BoardColumn.BLOCKED
            assert "S2" in s3_classified.blocking_deps  # S2 is open, blocks
            assert "S1" not in s3_classified.blocking_deps  # S1 is closed, doesn't block
    
    def test_fixture_in_progress_with_blocker(self, sample_project_tf_dir):
        """Test that in_progress tickets with blockers go to BLOCKED."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader
        
        loader = YamlTicketLoader(sample_project_tf_dir)
        tickets = loader.load_all()
        
        ticket_map = {t.id: t for t in tickets}
        
        # Set up: S1 open, S2 in_progress but depends on S1
        if "S1" in ticket_map and "S2" in ticket_map:
            ticket_map["S1"].status = "open"
            ticket_map["S2"].status = "in_progress"
            ticket_map["S2"].deps = ["S1"]
            
            classifier = BoardClassifier(tickets)
            view = classifier.classify()
            
            s2_classified = next(ct for ct in view.tickets if ct.id == "S2")
            
            # BLOCKED takes precedence over IN_PROGRESS
            assert s2_classified.column == BoardColumn.BLOCKED
    
    def test_fixture_board_view_counts(self, sample_project_tf_dir):
        """Test BoardView counts with fixture tickets."""
        from pi_tk_flow_ui.ticket_loader import YamlTicketLoader
        
        loader = YamlTicketLoader(sample_project_tf_dir)
        tickets = loader.load_all()
        
        # Configure specific states
        ticket_map = {t.id: t for t in tickets}
        
        # S1: READY
        if "S1" in ticket_map:
            ticket_map["S1"].status = "open"
            ticket_map["S1"].deps = []
        
        # S2: BLOCKED (depends on S1)
        if "S2" in ticket_map:
            ticket_map["S2"].status = "open"
            ticket_map["S2"].deps = ["S1"]
        
        # S3: IN_PROGRESS
        if "S3" in ticket_map:
            ticket_map["S3"].status = "in_progress"
            ticket_map["S3"].deps = []
        
        # S4: CLOSED
        if "S4" in ticket_map:
            ticket_map["S4"].status = "closed"
            ticket_map["S4"].deps = []
        
        classifier = BoardClassifier(tickets)
        view = classifier.classify()
        
        counts = view.counts
        
        # Verify counts match expected distribution
        assert counts["ready"] >= 1  # At least S1
        assert counts["blocked"] >= 1  # At least S2
        assert counts["in_progress"] >= 1  # At least S3
        assert counts["closed"] >= 1  # At least S4


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

    def test_classify_closed_ticket_with_deps_stays_closed(self):
        """Test that closed tickets with dependencies stay CLOSED (criterion #4 precedence)."""
        # Even if T1 has an open dependency (T2), it should still be CLOSED
        # because CLOSED status takes precedence over BLOCKED
        t1 = Ticket(id="T1", title="Done with deps", body="", status="closed", deps=["T2"], plan_name="p")
        t2 = Ticket(id="T2", title="Open dep", body="", status="open", plan_name="p")
        
        classifier = BoardClassifier([t1, t2])
        result = classifier.classify()
        
        t1_classified = next(ct for ct in result.tickets if ct.id == "T1")
        
        # CLOSED takes precedence over BLOCKED
        assert t1_classified.column == BoardColumn.CLOSED
        assert t1_classified.blocking_deps == []  # No need to report blockers for closed tickets

    def test_classify_mixed_known_unknown_deps(self):
        """Test tickets with mix of known open and unknown dependencies (criterion #5)."""
        # Known ticket T2 is open, UNKNOWN-DEP doesn't exist
        t1 = Ticket(id="T1", title="Mixed deps", body="", status="open", deps=["T2", "UNKNOWN-DEP"], plan_name="p")
        t2 = Ticket(id="T2", title="Open dep", body="", status="open", plan_name="p")
        
        classifier = BoardClassifier([t1, t2])
        result = classifier.classify()
        
        t1_classified = next(ct for ct in result.tickets if ct.id == "T1")
        
        assert t1_classified.column == BoardColumn.BLOCKED
        assert "T2" in t1_classified.blocking_deps
        assert "UNKNOWN-DEP" in t1_classified.blocking_deps

    def test_is_blocked_with_unknown_dep(self):
        """Test is_blocked helper with unknown dependencies (criterion #5)."""
        ticket = Ticket(id="T1", title="Unknown dep", body="", status="open", deps=["UNKNOWN"], plan_name="p")
        
        classifier = BoardClassifier([ticket])
        # Don't call classify() - test that is_blocked works without ticket_map initialized
        assert classifier.is_blocked(ticket) is True

    def test_is_blocked_helper_consistency(self):
        """Test is_blocked helper initializes ticket_map automatically."""
        t1 = Ticket(id="T1", title="Dep", body="", status="open", plan_name="p")
        t2 = Ticket(id="T2", title="Blocked", body="", status="open", deps=["T1"], plan_name="p")
        
        classifier = BoardClassifier([t1, t2])
        # Don't call classify() - test that is_blocked initializes ticket_map
        assert classifier.is_blocked(t2) is True
        assert classifier.is_blocked(t1) is False

    def test_get_ready_tickets_helper_consistency(self):
        """Test get_ready_tickets helper initializes ticket_map automatically."""
        t1 = Ticket(id="T1", title="Ready", body="", status="open", deps=[], plan_name="p")
        t2 = Ticket(id="T2", title="Blocked", body="", status="open", deps=["T1"], plan_name="p")
        t3 = Ticket(id="T3", title="In Progress", body="", status="in_progress", deps=[], plan_name="p")
        t4 = Ticket(id="T4", title="Closed", body="", status="closed", deps=[], plan_name="p")
        
        classifier = BoardClassifier([t1, t2, t3, t4])
        # Don't call classify() - test that get_ready_tickets initializes ticket_map
        ready = classifier.get_ready_tickets()
        
        # Only t1 is ready (open, no blockers, not in_progress)
        assert len(ready) == 1
        assert ready[0].id == "T1"
    
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
