"""Tests for plan_scanner module."""

from pathlib import Path

import pytest

from pi_tk_flow_ui.plan_scanner import Plan, PlanScanner


class TestPlan:
    """Test Plan dataclass."""

    def test_plan_creation(self, tmp_path: Path):
        """Test basic plan creation."""
        plan_dir = tmp_path / "sample-plan"
        plan_dir.mkdir()

        plan = Plan(
            id="sample-plan",
            title="Sample Plan",
            plan_date="2026-03-06",
            plan_topic="sample-plan",
            dir_path=plan_dir,
        )

        assert plan.id == "sample-plan"
        assert plan.title == "Sample Plan"
        assert plan.plan_date == "2026-03-06"
        assert plan.plan_topic == "sample-plan"
        assert plan.dir_path == plan_dir
        assert plan.ticket_breakdown_path is None


class TestPlanScannerWithFixtures:
    """Test PlanScanner using deterministic sample fixtures."""

    def test_scan_finds_sample_plan(self, sample_project_tf_dir: Path):
        """Scanner finds the sample fixture plan directory."""
        scanner = PlanScanner(sample_project_tf_dir / "plans")
        plans = scanner.scan()

        assert len(plans) == 1
        assert plans[0].id == "sample-plan"

    def test_fixture_plan_metadata(self, sample_project_tf_dir: Path):
        """Scanner extracts metadata and document paths from fixtures."""
        scanner = PlanScanner(sample_project_tf_dir / "plans")
        plan = scanner.get_by_id("sample-plan")

        assert plan is not None
        assert plan.title == "Product Requirements Document (PRD)"
        assert plan.plan_date == ""
        assert plan.plan_topic == "sample-plan"
        assert plan.prd_path is not None
        assert plan.prd_path.name == "01-prd.md"
        assert plan.spec_path is not None
        assert plan.spec_path.name == "02-spec.md"
        assert plan.impl_plan_path is not None
        assert plan.impl_plan_path.name == "03-implementation-plan.md"
        assert plan.ticket_breakdown_path is not None
        assert plan.ticket_breakdown_path.name == "04-ticket-breakdown.md"

    def test_search_matches_title_and_topic(self, sample_project_tf_dir: Path):
        """Search works across title and topic fields."""
        scanner = PlanScanner(sample_project_tf_dir / "plans")

        by_topic = scanner.search("sample-plan")
        by_title = scanner.search("requirements")

        assert len(by_topic) == 1
        assert by_topic[0].id == "sample-plan"
        assert len(by_title) == 1
        assert by_title[0].id == "sample-plan"


class TestPlanScannerBehavior:
    """Test PlanScanner behavior and legacy compatibility."""

    def test_missing_plans_directory_returns_empty(self, tmp_path: Path):
        """Missing .tf/plans directory returns an empty list."""
        scanner = PlanScanner(tmp_path / ".tf" / "plans")
        assert scanner.scan() == []

    def test_auto_discovery_stays_within_repo_boundary(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Auto-discovery should not escape to an unrelated ancestor .tf directory."""
        outer = tmp_path / "outer"
        project = outer / "coding" / "example-project"
        subdir = project / "nested"

        (outer / ".tf" / "plans" / "wrong-plan").mkdir(parents=True)
        (project / ".git").mkdir(parents=True)
        subdir.mkdir(parents=True)

        monkeypatch.chdir(subdir)

        scanner = PlanScanner()

        assert scanner.plans_dir == project / ".tf" / "plans"
        assert scanner.scan() == []

    def test_sorts_newest_date_first(self, tmp_path: Path):
        """Dated plan directories are sorted newest-first."""
        plans_dir = tmp_path / ".tf" / "plans"
        newest = plans_dir / "2026-03-06-newest-plan"
        oldest = plans_dir / "2026-03-01-oldest-plan"
        newest.mkdir(parents=True)
        oldest.mkdir(parents=True)

        (newest / "01-prd.md").write_text("# Newest Plan\n", encoding="utf-8")
        (oldest / "01-prd.md").write_text("# Oldest Plan\n", encoding="utf-8")

        scanner = PlanScanner(plans_dir)
        plans = scanner.scan()

        assert [plan.id for plan in plans] == ["2026-03-06-newest-plan", "2026-03-01-oldest-plan"]

    def test_uses_legacy_plan_and_progress_files_as_fallbacks(self, tmp_path: Path):
        """Legacy 03-plan.md and 04-progress.md are still recognized."""
        plan_dir = tmp_path / ".tf" / "plans" / "legacy-plan"
        plan_dir.mkdir(parents=True)

        (plan_dir / "01-prd.md").write_text("# Legacy Plan\n", encoding="utf-8")
        (plan_dir / "03-plan.md").write_text("# Legacy Implementation Plan\n", encoding="utf-8")
        (plan_dir / "04-progress.md").write_text("# Legacy Progress\n", encoding="utf-8")

        scanner = PlanScanner(tmp_path / ".tf" / "plans")
        plan = scanner.get_by_id("legacy-plan")

        assert plan is not None
        assert plan.impl_plan_path is not None
        assert plan.impl_plan_path.name == "03-plan.md"
        assert plan.ticket_breakdown_path is not None
        assert plan.ticket_breakdown_path.name == "04-progress.md"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
