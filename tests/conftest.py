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
def sample_plan_dir(sample_project_tf_dir: Path) -> Path:
    """Return the path to the sample plan directory."""
    return sample_project_tf_dir / "plans" / "sample-plan"


@pytest.fixture
def sample_tickets_dir(sample_project_fixture_dir: Path) -> Path:
    """Return the path to the sample tickets directory."""
    return sample_project_fixture_dir / ".tickets"


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
