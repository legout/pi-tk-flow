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
    
    def test_invalid_yaml_skipped(self, sample_tf_dir):
        """Test that invalid YAML files are skipped with warning."""
        # Add an invalid YAML file
        bad_plan_dir = sample_tf_dir / "plans" / "bad-plan"
        bad_plan_dir.mkdir()
        with open(bad_plan_dir / "tickets.yaml", "w") as f:
            f.write("invalid: yaml: [")
        
        loader = YamlTicketLoader(sample_tf_dir)
        
        # Should not raise, just skip the bad file
        tickets = loader.load_all()
        
        # Should still have tickets from the good plan
        assert len(tickets) == 3
    
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
