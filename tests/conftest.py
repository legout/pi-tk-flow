"""Shared pytest fixtures for pi-tk-flow-ui tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

# Path to the sample fixture project
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_PROJECT_DIR = FIXTURES_DIR / "sample_project"


@pytest.fixture
def sample_project_fixture_dir() -> Path:
    """Return the path to the sample project fixture directory.
    
    This fixture provides a stable, read-only reference to the deterministic
    sample project structure used across tests.
    """
    return SAMPLE_PROJECT_DIR


@pytest.fixture
def sample_project_tf_dir(tmp_path: Path) -> Path:
    """Create a copy of the sample .tf directory in a temp location.
    
    This fixture copies the deterministic sample project to a temporary
    directory, allowing tests to modify files without affecting the fixture.
    """
    source_tf = SAMPLE_PROJECT_DIR / ".tf"
    dest_tf = tmp_path / ".tf"
    
    if source_tf.exists():
        shutil.copytree(source_tf, dest_tf)
    
    return dest_tf


@pytest.fixture
def sample_tf_dir(sample_project_tf_dir: Path) -> Path:
    """Alias for sample_project_tf_dir for backward compatibility."""
    return sample_project_tf_dir


@pytest.fixture
def sample_knowledge_dir(sample_tf_dir: Path) -> Path:
    """Return the path to the sample knowledge directory."""
    return sample_tf_dir / "knowledge"


@pytest.fixture
def sample_plan_dir(sample_tf_dir: Path) -> Path:
    """Return the path to the sample plan directory."""
    return sample_tf_dir / "plans" / "sample-plan"


@pytest.fixture
def empty_tf_dir(tmp_path: Path) -> Path:
    """Create an empty .tf directory structure."""
    tf_dir = tmp_path / ".tf"
    tf_dir.mkdir()
    return tf_dir


@pytest.fixture
def mock_plan_dir(tmp_path: Path) -> Path:
    """Create a temporary plan directory with configurable tickets.yaml.
    
    Returns the plan directory path. Tests should write their own
    tickets.yaml to this directory.
    """
    plans_dir = tmp_path / ".tf" / "plans"
    plan_dir = plans_dir / "test-plan"
    plan_dir.mkdir(parents=True)
    return plan_dir


@pytest.fixture
def write_tickets_yaml(mock_plan_dir: Path):
    """Helper fixture to write tickets.yaml to a plan directory.
    
    Returns a function that accepts a dict and writes it as tickets.yaml.
    
    Example:
        def test_example(write_tickets_yaml, mock_plan_dir):
            write_tickets_yaml({
                "slices": [{"key": "T1", "title": "Test"}]
            })
            # Now mock_plan_dir / "tickets.yaml" exists
    """
    def _write(data: dict) -> Path:
        tickets_file = mock_plan_dir / "tickets.yaml"
        with open(tickets_file, "w") as f:
            yaml.dump(data, f)
        return tickets_file
    
    return _write


@pytest.fixture
def create_plan_dir(tmp_path: Path):
    """Helper fixture to create additional plan directories.
    
    Returns a function that creates a plan directory with the given name
    and optional tickets.yaml content.
    
    Example:
        def test_multi_plan(create_plan_dir):
            plan1 = create_plan_dir("plan-a", {"slices": [{"key": "A1", "title": "A"}]})
            plan2 = create_plan_dir("plan-b", {"slices": [{"key": "B1", "title": "B"}]})
    """
    def _create(name: str, tickets_data: dict | None = None) -> Path:
        plans_dir = tmp_path / ".tf" / "plans"
        plan_dir = plans_dir / name
        plan_dir.mkdir(parents=True)
        
        if tickets_data is not None:
            tickets_file = plan_dir / "tickets.yaml"
            with open(tickets_file, "w") as f:
                yaml.dump(tickets_data, f)
        
        return plan_dir
    
    return _create


@pytest.fixture
def fixture_ticket_ids() -> dict[str, dict]:
    """Return expected ticket IDs and properties from the sample fixture.
    
    This provides a stable reference for tests to assert against without
    hardcoding values multiple times.
    """
    return {
        "epic-sample-plan": {
            "title": "Sample Epic for Testing",
            "type": "epic",
            "tags": ["testing", "ui", "epic-tag"],
            "assignee": "epic-owner",
        },
        "S1": {
            "title": "Ready slice - no dependencies",
            "type": "feature",
            "priority": 1,
            "deps": [],
        },
        "S2": {
            "title": "Blocked slice - depends on S1",
            "type": "feature",
            "priority": 2,
            "deps": ["S1"],
        },
        "S3": {
            "title": "In Progress slice",
            "type": "chore",
            "priority": 1,
            "assignee": "testuser",
        },
        "S4": {
            "title": "Closed slice",
            "type": "feature",
            "priority": 3,
            "external_ref": "github.com/org/repo/issues/42",
        },
        "S5": {
            "title": "Multiple dependencies",
            "type": "feature",
            "priority": 2,
            "deps": ["S1", "S2"],
            "assignee": "developer2",
        },
        "S6": {
            "title": "String dependency test",
            "type": "bug",
            "priority": 1,
            "deps": ["S1"],  # String converted to list
        },
        "S7": {
            "title": "String tag test",
            "type": "docs",
            "priority": 3,
            "tags": ["single-tag"],  # String converted to list
        },
    }


@pytest.fixture
def fixture_topic_ids() -> dict[str, dict]:
    """Return expected topic IDs and properties from the sample fixture.
    
    This provides a stable reference for tests to assert against.
    """
    return {
        "seed-sample": {
            "title": "Seed Topic - Project Scaffolding",
            "type": "seed",
            "keywords": ["scaffolding", "project", "setup"],
        },
        "plan-sample": {
            "title": "Plan Topic - Implementation Workflow",
            "type": "plan",
            "keywords": ["planning", "workflow", "implementation"],
        },
        "spike-sample": {
            "title": "Spike Topic - Technical Investigation",
            "type": "spike",
            "keywords": ["spike", "research", "investigation"],
        },
        "baseline-testing": {
            "title": "Baseline Testing Patterns",
            "type": "baseline",
            "keywords": ["testing", "pytest", "fixtures"],
        },
    }
