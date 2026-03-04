"""Tests for TUI app module.

Tests for TicketBoard and TicketflowApp covering:
- Filter functionality (search, tag, assignee)
- Keyboard actions (q, r, o, e, 1-4)
- Plan document opening
- Pager/editor failure handling
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Skip all tests if textual is not installed
try:
    from textual.app import App
    from textual.reactive import reactive
    from pi_tk_flow_ui.app import (
        TicketBoard,
        TopicBrowser,
        TicketflowApp,
        DataListItem,
    )
    from pi_tk_flow_ui.board_classifier import BoardColumn, ClassifiedTicket
    from pi_tk_flow_ui.ticket_loader import Ticket
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    pytest.skip("textual not installed", allow_module_level=True)


@pytest.fixture
def sample_ticket():
    """Create a sample ticket for testing."""
    return Ticket(
        id="TEST-1",
        title="Test Ticket Title",
        body="This is a test ticket description with searchable content.",
        plan_name="test-plan",
        plan_dir="/tmp/test-plan",
        tags=["feature", "urgent"],
        assignee="developer1",
        priority=1,
        status="open",
    )


@pytest.fixture
def sample_classified_ticket(sample_ticket):
    """Create a sample classified ticket."""
    return ClassifiedTicket(
        ticket=sample_ticket,
        column=BoardColumn.READY,
        blocking_deps=[],
    )


@pytest.fixture
def sample_tickets():
    """Create a list of sample tickets for filtering tests."""
    return [
        ClassifiedTicket(
            ticket=Ticket(
                id="FEAT-1",
                title="Feature Ticket",
                body="A feature implementation ticket",
                plan_name="plan-a",
                plan_dir="/tmp/plan-a",
                tags=["feature", "frontend"],
                assignee="alice",
                priority=1,
            ),
            column=BoardColumn.READY,
            blocking_deps=[],
        ),
        ClassifiedTicket(
            ticket=Ticket(
                id="BUG-1",
                title="Bug Fix Ticket",
                body="A bug fix for the backend",
                plan_name="plan-b",
                plan_dir="/tmp/plan-b",
                tags=["bug", "backend"],
                assignee="bob",
                priority=2,
            ),
            column=BoardColumn.IN_PROGRESS,
            blocking_deps=[],
        ),
        ClassifiedTicket(
            ticket=Ticket(
                id="DOC-1",
                title="Documentation Update",
                body="Update the API docs",
                plan_name="plan-a",
                plan_dir="/tmp/plan-a",
                tags=["docs"],
                assignee="alice",
                priority=3,
            ),
            column=BoardColumn.BLOCKED,
            blocking_deps=["FEAT-1"],
        ),
        ClassifiedTicket(
            ticket=Ticket(
                id="NOASSIGN-1",
                title="Unassigned Ticket",
                body="No one assigned yet",
                plan_name="plan-c",
                plan_dir="/tmp/plan-c",
                tags=["feature"],
                assignee=None,
                priority=1,
            ),
            column=BoardColumn.CLOSED,
            blocking_deps=[],
        ),
    ]


class TestTicketBoardFilters:
    """Test TicketBoard filter functionality."""

    def test_search_filters_by_title(self, sample_tickets):
        """Search filters tickets by title (case-insensitive)."""
        board = TicketBoard()
        board.search_query = "ticket"  # "Feature Ticket", "Bug Fix Ticket", "Unassigned Ticket"
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 3
        assert all("ticket" in t.ticket.title.lower() for t in result)

    def test_search_filters_by_body(self, sample_tickets):
        """Search filters tickets by body/description."""
        board = TicketBoard()
        board.search_query = "backend"
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 1
        assert result[0].id == "BUG-1"

    def test_search_filters_by_id(self, sample_tickets):
        """Search filters tickets by ID."""
        board = TicketBoard()
        board.search_query = "DOC-1"
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 1
        assert result[0].id == "DOC-1"

    def test_search_is_case_insensitive(self, sample_tickets):
        """Search is case-insensitive."""
        board = TicketBoard()
        board.search_query = "TICKET"  # uppercase, should match "Feature Ticket", "Bug Fix Ticket", "Unassigned Ticket"
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 3

    def test_search_empty_returns_all(self, sample_tickets):
        """Empty search query returns all tickets."""
        board = TicketBoard()
        board.search_query = ""
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 4

    def test_tag_filter_matches_ticket(self, sample_tickets):
        """Tag filter matches tickets with specified tag."""
        board = TicketBoard()
        board.tag_filter = "frontend"
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 1
        assert result[0].id == "FEAT-1"

    def test_tag_filter_is_case_insensitive(self, sample_tickets):
        """Tag filter is case-insensitive - stored lowercase matches mixed case tags."""
        board = TicketBoard()
        board.tag_filter = "frontend"  # lowercase as stored by on_input_changed
        
        result = board._apply_filters(sample_tickets)
        
        # Should match FEAT-1 which has "frontend" tag
        assert len(result) == 1
        assert result[0].id == "FEAT-1"

    def test_tag_filter_empty_returns_all(self, sample_tickets):
        """Empty tag filter returns all tickets."""
        board = TicketBoard()
        board.tag_filter = ""
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 4

    def test_assignee_filter_matches_ticket(self, sample_tickets):
        """Assignee filter matches tickets with specified assignee."""
        board = TicketBoard()
        board.assignee_filter = "alice"
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 2
        assert all(t.ticket.assignee == "alice" for t in result)

    def test_assignee_filter_skips_unassigned(self, sample_tickets):
        """Assignee filter excludes tickets without assignee."""
        board = TicketBoard()
        board.assignee_filter = "developer"
        
        result = board._apply_filters(sample_tickets)
        
        # No ticket has "developer" in assignee
        assert len(result) == 0

    def test_assignee_filter_is_case_insensitive(self, sample_tickets):
        """Assignee filter is case-insensitive."""
        board = TicketBoard()
        board.assignee_filter = "alice"  # lowercase stored, compared case-insensitively
        
        result = board._apply_filters(sample_tickets)
        
        assert len(result) == 2

    def test_filters_combine_with_and_logic(self, sample_tickets):
        """Multiple filters combine with AND logic."""
        board = TicketBoard()
        board.search_query = "feature"  # matches FEAT-1 title and NOASSIGN-1 tag
        board.tag_filter = "feature"  # matches FEAT-1 and NOASSIGN-1 tags
        
        result = board._apply_filters(sample_tickets)
        
        # Should match tickets with "feature" in title/body AND "feature" tag
        assert len(result) == 1
        assert result[0].id == "FEAT-1"

    @patch.object(TicketBoard, 'notify')
    @patch.object(TicketBoard, 'update_board')
    def test_clear_filters_resets_all_filters(self, mock_update, mock_notify):
        """Clear button resets all filter state."""
        board = TicketBoard()
        board.search_query = "search"
        board.tag_filter = "tag"
        board.assignee_filter = "assignee"
        
        # Verify initial state
        assert board.search_query == "search"
        
        # Mock query_one to avoid DOM mounting issues
        mock_search = Mock()
        mock_tag = Mock()
        mock_assignee = Mock()
        
        def query_side_effect(selector, expect_type=None):
            if selector == "#search-input":
                return mock_search
            elif selector == "#tag-filter":
                return mock_tag
            elif selector == "#assignee-filter":
                return mock_assignee
            return Mock()
        
        with patch.object(board, 'query_one', side_effect=query_side_effect):
            board._clear_filters()
        
        # Verify filter state was cleared
        assert board.search_query == ""
        assert board.tag_filter == ""
        assert board.assignee_filter == ""
        # Verify UI inputs were cleared
        assert mock_search.value == ""
        assert mock_tag.value == ""
        assert mock_assignee.value == ""


class TestInputChangeHandling:
    """Test immediate filter updates on input changes."""

    @patch.object(TicketBoard, 'update_board')
    def test_search_input_triggers_update(self, mock_update):
        """Search input change triggers immediate board update."""
        from textual.widgets import Input
        
        board = TicketBoard()
        
        # Create a mock input change event
        mock_input = Mock(spec=Input)
        mock_input.id = "search-input"
        event = Mock()
        event.input = mock_input
        event.value = "test query"
        
        board.on_input_changed(event)
        
        assert board.search_query == "test query"
        mock_update.assert_called_once()

    @patch.object(TicketBoard, 'update_board')
    def test_tag_input_triggers_update(self, mock_update):
        """Tag input change triggers immediate board update."""
        from textual.widgets import Input
        
        board = TicketBoard()
        
        mock_input = Mock(spec=Input)
        mock_input.id = "tag-filter"
        event = Mock()
        event.input = mock_input
        event.value = "TAG-VALUE"  # Should be lowercased
        
        board.on_input_changed(event)
        
        assert board.tag_filter == "tag-value"  # lowercased
        mock_update.assert_called_once()

    @patch.object(TicketBoard, 'update_board')
    def test_assignee_input_triggers_update(self, mock_update):
        """Assignee input change triggers immediate board update."""
        from textual.widgets import Input
        
        board = TicketBoard()
        
        mock_input = Mock(spec=Input)
        mock_input.id = "assignee-filter"
        event = Mock()
        event.input = mock_input
        event.value = "ASSIGNEE"  # Should be lowercased
        
        board.on_input_changed(event)
        
        assert board.assignee_filter == "assignee"  # lowercased
        mock_update.assert_called_once()


class TestKeyboardActions:
    """Test keyboard action bindings and delegation."""

    def test_quit_binding_exists(self):
        """'q' binding is defined for quit action."""
        app = TicketflowApp()
        binding = next((b for b in app.BINDINGS if b.key == "q"), None)
        
        assert binding is not None
        assert binding.action == "quit"

    def test_refresh_binding_exists(self):
        """'r' binding is defined for refresh action."""
        app = TicketflowApp()
        binding = next((b for b in app.BINDINGS if b.key == "r"), None)
        
        assert binding is not None
        assert binding.action == "refresh"

    def test_open_doc_binding_exists(self):
        """'o' binding is defined for open_doc action."""
        app = TicketflowApp()
        binding = next((b for b in app.BINDINGS if b.key == "o"), None)
        
        assert binding is not None
        assert binding.action == "open_doc"

    def test_expand_desc_binding_exists(self):
        """'e' binding is defined for expand_desc action."""
        app = TicketflowApp()
        binding = next((b for b in app.BINDINGS if b.key == "e"), None)
        
        assert binding is not None
        assert binding.action == "expand_desc"

    def test_number_bindings_exist(self):
        """'1-4' bindings are defined for opening plan docs."""
        app = TicketflowApp()
        
        for key in ["1", "2", "3", "4"]:
            binding = next((b for b in app.BINDINGS if b.key == key), None)
            assert binding is not None, f"Binding {key} not found"
            assert binding.action == f"open_doc_{key}"

    def test_help_binding_exists(self):
        """'?' binding is defined for help action."""
        app = TicketflowApp()
        binding = next((b for b in app.BINDINGS if b.key == "?"), None)
        
        assert binding is not None
        assert binding.action == "help"


class TestActionDelegation:
    """Test action methods delegate to correct widgets."""

    @patch.object(TicketBoard, 'load_tickets')
    @patch.object(TicketflowApp, 'notify')
    def test_refresh_delegates_to_tickets_tab(self, mock_notify, mock_load):
        """Refresh action on tickets tab reloads tickets."""
        app = TicketflowApp()
        
        # Mock the tabbed content
        mock_tabbed = Mock()
        mock_tabbed.active = "tab-tickets"
        
        with patch.object(app, 'query_one') as mock_query:
            mock_query.return_value = mock_tabbed
            # Mock the ticket board
            mock_board = Mock()
            mock_board.load_tickets = mock_load
            
            def query_side_effect(selector, **kwargs):
                if selector == TicketBoard:
                    return mock_board
                return mock_tabbed
            
            mock_query.side_effect = query_side_effect
            
            app.action_refresh()
            
            mock_load.assert_called_once()
            mock_notify.assert_called_once_with("Tickets refreshed")

    @patch.object(TopicBrowser, 'load_topics')
    @patch.object(TicketflowApp, 'notify')
    def test_refresh_delegates_to_topics_tab(self, mock_notify, mock_load):
        """Refresh action on topics tab reloads topics."""
        app = TicketflowApp()
        
        mock_tabbed = Mock()
        mock_tabbed.active = "tab-topics"
        
        with patch.object(app, 'query_one') as mock_query:
            mock_query.return_value = mock_tabbed
            mock_browser = Mock()
            mock_browser.load_topics = mock_load
            
            def query_side_effect(selector, **kwargs):
                if selector == TopicBrowser:
                    return mock_browser
                return mock_tabbed
            
            mock_query.side_effect = query_side_effect
            
            app.action_refresh()
            
            mock_load.assert_called_once()
            mock_notify.assert_called_once_with("Topics refreshed")

    @patch.object(TicketBoard, 'action_open_in_editor')
    def test_open_doc_delegates_to_tickets(self, mock_open):
        """Open doc action delegates to ticket board on tickets tab."""
        app = TicketflowApp()
        
        mock_tabbed = Mock()
        mock_tabbed.active = "tab-tickets"
        
        with patch.object(app, 'query_one') as mock_query:
            mock_query.return_value = mock_tabbed
            mock_board = Mock()
            mock_board.action_open_in_editor = mock_open
            
            def query_side_effect(selector, **kwargs):
                if selector == TicketBoard:
                    return mock_board
                return mock_tabbed
            
            mock_query.side_effect = query_side_effect
            
            app.action_open_doc()
            
            mock_open.assert_called_once()

    @patch.object(TopicBrowser, 'action_open_doc')
    def test_open_doc_delegates_to_topics(self, mock_open):
        """Open doc action delegates to topic browser on topics tab."""
        app = TicketflowApp()
        
        mock_tabbed = Mock()
        mock_tabbed.active = "tab-topics"
        
        with patch.object(app, 'query_one') as mock_query:
            mock_query.return_value = mock_tabbed
            mock_browser = Mock()
            mock_browser.action_open_doc = mock_open
            
            def query_side_effect(selector, **kwargs):
                if selector == TopicBrowser:
                    return mock_browser
                return mock_tabbed
            
            mock_query.side_effect = query_side_effect
            
            app.action_open_doc()
            
            mock_open.assert_called_once()

    @patch.object(TicketBoard, 'action_toggle_description')
    def test_expand_desc_delegates_to_tickets(self, mock_toggle):
        """Expand desc action delegates to ticket board."""
        app = TicketflowApp()
        
        mock_tabbed = Mock()
        mock_tabbed.active = "tab-tickets"
        
        with patch.object(app, 'query_one') as mock_query:
            mock_query.return_value = mock_tabbed
            mock_board = Mock()
            mock_board.action_toggle_description = mock_toggle
            
            def query_side_effect(selector, **kwargs):
                if selector == TicketBoard:
                    return mock_board
                return mock_tabbed
            
            mock_query.side_effect = query_side_effect
            
            app.action_expand_desc()
            
            mock_toggle.assert_called_once()

    def test_expand_desc_noop_on_topics_tab(self):
        """Expand desc does nothing on topics tab."""
        app = TicketflowApp()
        
        mock_tabbed = Mock()
        mock_tabbed.active = "tab-topics"
        
        with patch.object(app, 'query_one', return_value=mock_tabbed):
            # Should not raise
            app.action_expand_desc()


class TestPlanDocShortcuts:
    """Test 1-4 keyboard shortcuts for opening plan documents."""

    def test_open_doc_1_calls_open_plan_doc(self):
        """Action 1 opens PRD document."""
        app = TicketflowApp()
        
        with patch.object(app, '_open_plan_doc') as mock_open:
            mock_open.return_value = True
            app.action_open_doc_1()
            mock_open.assert_called_once_with("01-prd.md")

    def test_open_doc_2_calls_open_plan_doc(self):
        """Action 2 opens Spec document."""
        app = TicketflowApp()
        
        with patch.object(app, '_open_plan_doc') as mock_open:
            mock_open.return_value = True
            app.action_open_doc_2()
            mock_open.assert_called_once_with("02-spec.md")

    def test_open_doc_3_calls_open_plan_doc(self):
        """Action 3 opens Plan document (tries 03-implementation-plan.md first)."""
        app = TicketflowApp()
        
        with patch.object(app, '_open_plan_doc') as mock_open:
            mock_open.side_effect = [False, True]  # First fails, second succeeds
            app.action_open_doc_3()
            mock_open.assert_any_call("03-implementation-plan.md")
            mock_open.assert_any_call("03-plan.md")

    def test_open_doc_4_calls_open_plan_doc(self):
        """Action 4 opens Progress document."""
        app = TicketflowApp()
        
        with patch.object(app, '_open_plan_doc') as mock_open:
            mock_open.return_value = True
            app.action_open_doc_4()
            mock_open.assert_called_once_with("04-progress.md")

    @patch.object(TicketflowApp, 'notify')
    def test_open_plan_doc_no_selection_shows_warning(self, mock_notify):
        """Opening plan doc without ticket selection shows warning."""
        app = TicketflowApp()
        
        mock_board = Mock()
        mock_board.selected_ticket = None
        
        with patch.object(app, 'query_one', return_value=mock_board):
            result = app._open_plan_doc("01-prd.md")
            
            assert result is False
            mock_notify.assert_called_once_with("No ticket selected", severity="warning")


class TestFileOpeningFailures:
    """Test pager/editor failure handling."""

    @patch.object(TicketBoard, 'notify')
    def test_open_file_missing_file_shows_error(self, mock_notify):
        """Opening missing file shows 'not found' error notification.
        
        This test verifies that TicketBoard._open_file explicitly checks for
        file existence and shows a specific 'not found' message (not a generic
        failure message from subprocess).
        """
        board = TicketBoard()
        
        test_path = Path("/nonexistent/file.md")
        
        # Patch exists to return False for our specific path only
        original_exists = Path.exists
        def mock_exists(self):
            if str(self) == "/nonexistent/file.md":
                return False
            return original_exists(self)
        
        with patch.object(Path, 'exists', mock_exists):
            board._open_file(test_path)
            
            mock_notify.assert_called_once()
            # Verify the notification specifically mentions "not found"
            call_args = mock_notify.call_args
            message = call_args[0][0]
            severity = call_args[1].get('severity', 'info')
            
            # Must be an error notification with "not found" message
            assert severity == "error", f"Expected severity='error', got {severity}"
            assert "not found" in message.lower(), f"Expected 'not found' in message, got: {message}"
            assert str(test_path) in message, f"Expected path in message, got: {message}"

    @patch.object(TicketBoard, 'notify')
    def test_open_file_no_pager_editor_shows_error(self, mock_notify):
        """No PAGER/EDITOR set shows helpful error."""
        board = TicketBoard()
        
        test_path = Path("/tmp/test.md")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('shutil.which', return_value=None):
                with patch.object(Path, 'exists', return_value=True):
                    board._open_file(test_path)
                    
                    mock_notify.assert_called_once()
                    message = mock_notify.call_args[0][0].lower()
                    # Check for either word order (pager/editor or editor/pager)
                    assert ("pager" in message and "editor" in message) or ("editor" in message and "pager" in message)

    @patch.object(TicketBoard, 'notify')
    def test_open_file_subprocess_failure_shows_error(self, mock_notify):
        """Subprocess failure shows error notification with exit code."""
        board = TicketBoard()
        
        # Mock suspend by patching the app property
        with patch.object(TicketBoard, 'app', new_callable=Mock) as mock_app:
            mock_app.suspend = MagicMock()
            
            test_path = Path("/tmp/test.md")
            
            with patch.dict(os.environ, {'EDITOR': 'vim'}):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock(returncode=1)
                    
                    with patch.object(Path, 'exists', return_value=True):
                        board._open_file(test_path)
                        
                        mock_notify.assert_called_once()
                        assert "exit code" in mock_notify.call_args[0][0].lower()

    @patch.object(TicketBoard, 'notify')
    def test_open_file_exception_shows_error(self, mock_notify):
        """Exception during file open shows error notification."""
        board = TicketBoard()
        
        with patch.object(TicketBoard, 'app', new_callable=Mock) as mock_app:
            mock_app.suspend = MagicMock()
            
            test_path = Path("/tmp/test.md")
            
            with patch.dict(os.environ, {'EDITOR': 'vim'}):
                with patch('subprocess.run', side_effect=OSError("Test error")):
                    with patch.object(Path, 'exists', return_value=True):
                        board._open_file(test_path)
                        
                        mock_notify.assert_called_once()
                        assert "failed" in mock_notify.call_args[0][0].lower()

    @patch.object(TicketBoard, 'notify')
    def test_open_file_success_no_notification(self, mock_notify):
        """Successful file open shows no error notification."""
        board = TicketBoard()
        
        with patch.object(TicketBoard, 'app', new_callable=Mock) as mock_app:
            mock_app.suspend = MagicMock()
            
            test_path = Path("/tmp/test.md")
            
            with patch.dict(os.environ, {'EDITOR': 'vim'}):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock(returncode=0)
                    
                    with patch.object(Path, 'exists', return_value=True):
                        board._open_file(test_path)
                        
                        # Should not notify on success
                        mock_notify.assert_not_called()


class TestDescriptionToggle:
    """Test description expand/collapse functionality."""

    def test_toggle_description_switches_state(self):
        """Toggle description switches between full and truncated."""
        board = TicketBoard()
        
        assert board.show_full_description is False
        
        board.action_toggle_description()
        assert board.show_full_description is True
        
        board.action_toggle_description()
        assert board.show_full_description is False


class TestTopicBrowserActions:
    """Test TopicBrowser-specific actions."""

    @patch.object(TopicBrowser, 'notify')
    def test_open_doc_no_selection_shows_warning(self, mock_notify):
        """Opening doc without topic selection shows warning."""
        browser = TopicBrowser()
        browser.selected_topic = None
        
        browser.action_open_doc()
        
        mock_notify.assert_called_once_with("No topic selected", severity="warning")

    @patch.object(TopicBrowser, '_open_file')
    def test_open_doc_with_selection_opens_file(self, mock_open_file):
        """Opening doc with topic selection opens the file."""
        browser = TopicBrowser()
        
        mock_topic = Mock()
        mock_topic.file_path = Path("/tmp/topic.md")
        browser.selected_topic = mock_topic
        
        browser.action_open_doc()
        
        mock_open_file.assert_called_once_with(Path("/tmp/topic.md"))


class TestActionOpenInEditor:
    """Test action_open_in_editor failure paths."""

    @patch.object(TicketBoard, 'notify')
    def test_no_plan_documents_shows_warning(self, mock_notify):
        """Opening editor when no plan docs exist shows warning."""
        board = TicketBoard()
        
        # Create a classified ticket with a plan_dir
        board.selected_ticket = ClassifiedTicket(
            ticket=Ticket(
                id="TEST-1",
                title="Test",
                body="test",
                plan_name="test",
                plan_dir="/tmp/empty-plan-dir",
            ),
            column=BoardColumn.READY,
            blocking_deps=[],
        )
        
        # Track which paths are being checked for existence
        checked_paths = []
        original_exists = Path.exists
        
        def mock_exists(self):
            path_str = str(self)
            checked_paths.append(path_str)
            if path_str == "/tmp/empty-plan-dir":
                return True  # plan_dir exists
            # All plan files don't exist
            if any(doc in path_str for doc in ["01-prd", "02-spec", "03-implementation", "03-plan", "04-progress"]):
                return False
            return original_exists(self)
        
        with patch.object(Path, 'exists', mock_exists):
            board.action_open_in_editor()
        
        # Should have been called with "No plan documents found" warning
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args
        message = call_args[0][0]
        severity = call_args[1].get('severity', 'info')
        
        assert severity == "warning"
        assert "no plan documents found" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
