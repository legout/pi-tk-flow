"""Tests for ticket_loader module."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from pi_tk_flow_ui.ticket_loader import (
    Ticket,
    TicketLoadError,
    YamlTicketLoader,
)


@pytest.fixture
def sample_tf_dir(tmp_path):
    """Create a sample .tf directory structure."""
    tf_dir = tmp_path / ".tf"
    plans_dir = tf_dir / "plans"
    plan_dir = plans_dir / "test-plan"
    plan_dir.mkdir(parents=True)
    
    tickets_yaml = {
        "epic": {
            "title": "Test Epic",
            "type": "epic",
            "description": "Epic description",
            "tags": ["testing"],
        },
        "slices": [
            {
                "key": "S1",
                "title": "First slice",
                "type": "feature",
                "priority": 1,
                "tags": ["feature"],
                "description": "First slice description",
                "blocked_by": [],
            },
            {
                "key": "S2",
                "title": "Second slice",
                "type": "bug",
                "priority": 2,
                "tags": ["bug", "urgent"],
                "description": "Second slice description",
                "blocked_by": ["S1"],
                "assignee": "developer1",
            },
        ],
    }
    
    with open(plan_dir / "tickets.yaml", "w") as f:
        yaml.dump(tickets_yaml, f)
    
    return tf_dir


class TestTicket:
    """Test Ticket dataclass."""
    
    def test_ticket_creation(self):
        """Test basic ticket creation."""
        ticket = Ticket(
            id="TEST-1",
            title="Test Ticket",
            body="Test description",
            plan_name="test-plan",
        )
        
        assert ticket.id == "TEST-1"
        assert ticket.title == "Test Ticket"
        assert ticket.body == "Test description"
        assert ticket.status == "open"  # default
        assert ticket.deps == []
        assert ticket.tags == []


class TestYamlTicketLoader:
    """Test YamlTicketLoader functionality."""
    
    def test_find_tf_dir_from_cwd(self, tmp_path, monkeypatch):
        """Test .tf directory discovery from current working directory."""
        monkeypatch.chdir(tmp_path)
        
        # Create .tf directory
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        
        loader = YamlTicketLoader()
        assert loader.tf_dir == tf_dir
    
    def test_load_plan_success(self, sample_tf_dir):
        """Test loading tickets from a plan directory."""
        loader = YamlTicketLoader(sample_tf_dir)
        plan_dir = sample_tf_dir / "plans" / "test-plan"
        
        tickets = loader.load_plan(plan_dir)
        
        # Should have epic + 2 slices = 3 tickets
        assert len(tickets) == 3
        
        # Find the slice tickets
        s1 = next(t for t in tickets if t.id == "S1")
        s2 = next(t for t in tickets if t.id == "S2")
        epic = next(t for t in tickets if t.id == "epic-test-plan")
        
        assert s1.title == "First slice"
        assert s1.priority == 1
        assert s1.deps == []
        
        assert s2.title == "Second slice"
        assert s2.priority == 2
        assert s2.deps == ["S1"]
        assert s2.assignee == "developer1"
        
        assert epic.ticket_type == "epic"
    
    def test_load_all_plans(self, sample_tf_dir):
        """Test loading tickets from all plan directories."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        tickets = loader.load_all()
        
        assert len(tickets) == 3  # epic + 2 slices
    
    def test_multi_plan_aggregation(self, tmp_path):
        """Test loading tickets from multiple plan directories (criterion #1)."""
        tf_dir = tmp_path / ".tf"
        plans_dir = tf_dir / "plans"
        
        # Create first plan
        plan1_dir = plans_dir / "plan-alpha"
        plan1_dir.mkdir(parents=True)
        with open(plan1_dir / "tickets.yaml", "w") as f:
            yaml.dump({
                "slices": [{"key": "A1", "title": "Alpha ticket"}]
            }, f)
        
        # Create second plan
        plan2_dir = plans_dir / "plan-beta"
        plan2_dir.mkdir(parents=True)
        with open(plan2_dir / "tickets.yaml", "w") as f:
            yaml.dump({
                "slices": [{"key": "B1", "title": "Beta ticket"}]
            }, f)
        
        # Create third plan
        plan3_dir = plans_dir / "plan-gamma"
        plan3_dir.mkdir(parents=True)
        with open(plan3_dir / "tickets.yaml", "w") as f:
            yaml.dump({
                "slices": [{"key": "G1", "title": "Gamma ticket"}]
            }, f)
        
        loader = YamlTicketLoader(tf_dir)
        tickets = loader.load_all()
        
        # Should aggregate tickets from all 3 plans
        assert len(tickets) == 3
        
        # Verify plan_name and plan_dir are preserved for each
        ticket_ids = {t.id: t for t in tickets}
        assert ticket_ids["A1"].plan_name == "plan-alpha"
        assert ticket_ids["B1"].plan_name == "plan-beta"
        assert ticket_ids["G1"].plan_name == "plan-gamma"
        assert str(plan1_dir) in ticket_ids["A1"].plan_dir
        assert str(plan2_dir) in ticket_ids["B1"].plan_dir
        assert str(plan3_dir) in ticket_ids["G1"].plan_dir
    
    def test_empty_plans_directory(self, tmp_path):
        """Test loading when plans directory is empty."""
        tf_dir = tmp_path / ".tf"
        plans_dir = tf_dir / "plans"
        plans_dir.mkdir(parents=True)
        
        loader = YamlTicketLoader(tf_dir)
        tickets = loader.load_all()
        
        assert tickets == []
    
    def test_missing_plans_directory(self, tmp_path):
        """Test loading when plans directory doesn't exist."""
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        
        loader = YamlTicketLoader(tf_dir)
        tickets = loader.load_all()
        
        assert tickets == []
    
    def test_invalid_yaml_skipped_with_warning(self, sample_tf_dir, caplog):
        """Test that invalid YAML files are skipped with explicit warning (criterion #3)."""
        import logging
        
        # Add an invalid YAML file
        bad_plan_dir = sample_tf_dir / "plans" / "bad-plan"
        bad_plan_dir.mkdir()
        with open(bad_plan_dir / "tickets.yaml", "w") as f:
            f.write("invalid: yaml: [")
        
        loader = YamlTicketLoader(sample_tf_dir)
        
        # Should not raise, just skip the bad file
        with caplog.at_level(logging.WARNING):
            tickets = loader.load_all()
        
        # Should still have tickets from the good plan
        assert len(tickets) == 3
        
        # Should have logged a warning about the bad plan being skipped
        assert any("bad-plan" in record.message and "skipping" in record.message.lower() 
                   for record in caplog.records)
    
    def test_missing_tickets_yaml_warning(self, tmp_path, caplog):
        """Test that missing tickets.yaml produces explicit warning (criterion #3)."""
        import logging
        
        tf_dir = tmp_path / ".tf"
        plans_dir = tf_dir / "plans"
        
        # Create a plan directory without tickets.yaml
        plan_dir = plans_dir / "empty-plan"
        plan_dir.mkdir(parents=True)
        # Create a placeholder file so directory is detected as a plan
        (plan_dir / "README.md").write_text("# Empty Plan")
        
        loader = YamlTicketLoader(tf_dir)
        
        with caplog.at_level(logging.WARNING):
            tickets = loader.load_all()
        
        assert tickets == []
        assert any("empty-plan" in record.message and "no tickets.yaml" in record.message.lower() 
                   for record in caplog.records)
    
    def test_empty_yaml_skipped_with_warning(self, sample_tf_dir, caplog):
        """Test that empty YAML files are skipped with warning (criterion #3)."""
        import logging
        
        # Add an empty YAML file
        empty_plan_dir = sample_tf_dir / "plans" / "empty-plan"
        empty_plan_dir.mkdir()
        with open(empty_plan_dir / "tickets.yaml", "w") as f:
            f.write("")  # Empty content
        
        loader = YamlTicketLoader(sample_tf_dir)
        
        with caplog.at_level(logging.WARNING):
            tickets = loader.load_all()
        
        # Should still have tickets from the good plan
        assert len(tickets) == 3
        
        # Should have logged a warning about empty YAML
        assert any("empty-plan" in record.message and "empty" in record.message.lower() 
                   for record in caplog.records)
    
    def test_non_dict_yaml_skipped_with_warning(self, sample_tf_dir, caplog):
        """Test that non-dict top-level YAML shapes are skipped with warning (criterion #3)."""
        import logging
        
        # Add a YAML file with non-dict top-level (list instead of dict)
        bad_plan_dir = sample_tf_dir / "plans" / "list-plan"
        bad_plan_dir.mkdir()
        with open(bad_plan_dir / "tickets.yaml", "w") as f:
            yaml.dump(["item1", "item2"])  # List at top level
        
        loader = YamlTicketLoader(sample_tf_dir)
        
        with caplog.at_level(logging.WARNING):
            tickets = loader.load_all()
        
        # Should still have tickets from the good plan
        assert len(tickets) == 3
        
        # Should have logged a warning about invalid format
        assert any("list-plan" in record.message for record in caplog.records)
    
    def test_parse_deps_string(self, sample_tf_dir):
        """Test parsing blocked_by as string."""
        plan_dir = sample_tf_dir / "plans" / "test-plan"
        
        # Modify tickets.yaml to use string for blocked_by
        tickets_yaml = {
            "slices": [
                {
                    "key": "S3",
                    "title": "String dep",
                    "blocked_by": "S1",  # String instead of list
                }
            ]
        }
        with open(plan_dir / "tickets.yaml", "w") as f:
            yaml.dump(tickets_yaml, f)
        
        loader = YamlTicketLoader(sample_tf_dir)
        tickets = loader.load_plan(plan_dir)
        
        s3 = next(t for t in tickets if t.id == "S3")
        assert s3.deps == ["S1"]
    
    def test_parse_tags_string(self, sample_tf_dir):
        """Test parsing tags as string."""
        plan_dir = sample_tf_dir / "plans" / "test-plan"
        
        tickets_yaml = {
            "slices": [
                {
                    "key": "S3",
                    "title": "String tags",
                    "tags": "single-tag",  # String instead of list
                }
            ]
        }
        with open(plan_dir / "tickets.yaml", "w") as f:
            yaml.dump(tickets_yaml, f)
        
        loader = YamlTicketLoader(sample_tf_dir)
        tickets = loader.load_plan(plan_dir)
        
        s3 = next(t for t in tickets if t.id == "S3")
        assert s3.tags == ["single-tag"]


class TestStatusQuery:
    """Test tk CLI status querying."""
    
    def test_status_query_success(self, sample_tf_dir):
        """Test successful status query from tk CLI."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        mock_response = json.dumps({"status": "in_progress"})
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=mock_response,
                stderr=""
            )
            
            status = loader._query_tk_status("S1")
            
            assert status == "in_progress"
            mock_run.assert_called_once()
    
    def test_tk_command_contract(self, sample_tf_dir):
        """Test that tk is invoked with exact command/flags and timeout (criterion #2)."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps({"status": "open"}),
                stderr=""
            )
            
            loader._query_tk_status("TEST-123")
            
            # Verify exact command structure
            mock_run.assert_called_once_with(
                ["tk", "show", "TEST-123", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5,
            )
    
    def test_status_query_data_payload(self, sample_tf_dir):
        """Test status query with {'data': {'status': ...}} payload shape (criterion #2)."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        # Test with nested "data" key
        mock_response = json.dumps({"data": {"status": "in_progress"}})
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=mock_response,
                stderr=""
            )
            
            status = loader._query_tk_status("S1")
            
            assert status == "in_progress"
    
    def test_status_query_nested_json(self, sample_tf_dir):
        """Test status query with nested JSON structure."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        # Test with nested "ticket" key
        mock_response = json.dumps({"ticket": {"status": "closed"}})
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=mock_response,
                stderr=""
            )
            
            status = loader._query_tk_status("S1")
            
            assert status == "closed"
    
    def test_status_query_failure_defaults_open(self, sample_tf_dir):
        """Test that failed queries default to 'open'."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="error"
            )
            
            status = loader._query_tk_status("S1")
            
            assert status == "open"
    
    def test_status_query_invalid_json_defaults_open(self, sample_tf_dir):
        """Test that invalid JSON defaults to 'open'."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="invalid json",
                stderr=""
            )
            
            status = loader._query_tk_status("S1")
            
            assert status == "open"
    
    def test_status_query_timeout_defaults_open(self, sample_tf_dir):
        """Test that timeout defaults to 'open'."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired("tk", 5)
            
            status = loader._query_tk_status("S1")
            
            assert status == "open"
    
    def test_status_query_tk_not_found(self, sample_tf_dir):
        """Test behavior when tk CLI is not installed."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("tk not found")
            
            status = loader._query_tk_status("S1")
            
            assert status == "open"
    
    def test_status_caching(self, sample_tf_dir):
        """Test that status queries are cached."""
        loader = YamlTicketLoader(sample_tf_dir)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps({"status": "closed"}),
                stderr=""
            )
            
            # First call should query
            status1 = loader.refresh_status("S1")
            assert mock_run.call_count == 1
            
            # Second call should use cache
            status2 = loader.refresh_status("S1")
            assert mock_run.call_count == 1  # No additional calls
            
            assert status1 == status2 == "closed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
