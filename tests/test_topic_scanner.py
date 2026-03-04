"""Tests for topic_scanner module."""

import pytest

from pi_tk_flow_ui.topic_scanner import Topic, TopicScanner, TopicScanError


class TestTopic:
    """Test Topic dataclass."""
    
    def test_topic_creation(self, tmp_path):
        """Test basic topic creation."""
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test Topic")
        
        topic = Topic(
            id="test",
            title="Test Topic",
            topic_type="plan",
            file_path=file_path,
            keywords=["test", "example"]
        )
        
        assert topic.id == "test"
        assert topic.title == "Test Topic"
        assert topic.topic_type == "plan"
        assert topic.keywords == ["test", "example"]


class TestTopicScanner:
    """Test TopicScanner functionality."""
    
    @pytest.fixture
    def sample_knowledge_dir(self, tmp_path):
        """Create a sample knowledge directory with topics."""
        topics_dir = tmp_path / ".tf" / "knowledge" / "topics"
        topics_dir.mkdir(parents=True)
        
        # Create sample topics
        (topics_dir / "seed-python.md").write_text("""---
keywords: [python, setup]
---
# Python Project Setup

How to set up a Python project.
""")
        
        (topics_dir / "plan-impl.md").write_text("""# Implementation Planning

Planning workflow guide.
""")
        
        (topics_dir / "spike-auth.md").write_text("# Authentication Spike")
        
        (topics_dir / "baseline-errors.md").write_text("# Error Handling Baseline")
        
        (topics_dir / "misc-notes.md").write_text("# Miscellaneous Notes")
        
        # Create a non-markdown file (should be ignored)
        (topics_dir / "README.txt").write_text("Not a markdown file")
        
        return tmp_path / ".tf" / "knowledge"
    
    def test_scan_finds_all_topics(self, sample_knowledge_dir):
        """Test scanning finds all markdown topics."""
        scanner = TopicScanner(sample_knowledge_dir)
        topics = scanner.scan()
        
        # Should find 5 topics (not README.txt)
        assert len(topics) == 5
        
        # Check IDs
        ids = {t.id for t in topics}
        assert "seed-python" in ids
        assert "plan-impl" in ids
        assert "spike-auth" in ids
        assert "baseline-errors" in ids
        assert "misc-notes" in ids
    
    def test_classify_types(self, sample_knowledge_dir):
        """Test topic type classification."""
        scanner = TopicScanner(sample_knowledge_dir)
        topics = scanner.scan()
        
        by_id = {t.id: t for t in topics}
        
        assert by_id["seed-python"].topic_type == "seed"
        assert by_id["plan-impl"].topic_type == "plan"
        assert by_id["spike-auth"].topic_type == "spike"
        assert by_id["baseline-errors"].topic_type == "baseline"
        assert by_id["misc-notes"].topic_type == "other"
    
    def test_extract_titles(self, sample_knowledge_dir):
        """Test title extraction from headings."""
        scanner = TopicScanner(sample_knowledge_dir)
        topics = scanner.scan()
        
        by_id = {t.id: t for t in topics}
        
        assert by_id["seed-python"].title == "Python Project Setup"
        assert by_id["plan-impl"].title == "Implementation Planning"
        assert by_id["spike-auth"].title == "Authentication Spike"
    
    def test_extract_keywords(self, sample_knowledge_dir):
        """Test keyword extraction from frontmatter."""
        scanner = TopicScanner(sample_knowledge_dir)
        topics = scanner.scan()
        
        by_id = {t.id: t for t in topics}
        
        assert by_id["seed-python"].keywords == ["python", "setup"]
        assert by_id["plan-impl"].keywords == []
    
    def test_missing_topics_directory(self, tmp_path):
        """Test scanning when topics directory doesn't exist."""
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        knowledge_dir.mkdir(parents=True)
        
        scanner = TopicScanner(knowledge_dir)
        topics = scanner.scan()
        
        assert topics == []
    
    def test_empty_topics_directory(self, tmp_path):
        """Test scanning empty topics directory."""
        topics_dir = tmp_path / ".tf" / "knowledge" / "topics"
        topics_dir.mkdir(parents=True)
        
        scanner = TopicScanner(tmp_path / ".tf" / "knowledge")
        topics = scanner.scan()
        
        assert topics == []
    
    def test_group_by_type(self, sample_knowledge_dir):
        """Test grouping topics by type."""
        scanner = TopicScanner(sample_knowledge_dir)
        topics = scanner.scan()
        groups = scanner.group_by_type(topics)
        
        assert "seed" in groups
        assert "plan" in groups
        assert "spike" in groups
        assert "baseline" in groups
        assert "other" in groups
        
        assert len(groups["seed"]) == 1
        assert len(groups["plan"]) == 1
        assert groups["seed"][0].id == "seed-python"
    
    def test_get_by_id(self, sample_knowledge_dir):
        """Test getting topic by ID."""
        scanner = TopicScanner(sample_knowledge_dir)
        
        topic = scanner.get_by_id("plan-impl")
        assert topic is not None
        assert topic.title == "Implementation Planning"
        
        missing = scanner.get_by_id("nonexistent")
        assert missing is None
    
    def test_search_by_id(self, sample_knowledge_dir):
        """Test searching topics by ID."""
        scanner = TopicScanner(sample_knowledge_dir)
        
        results = scanner.search("plan")
        ids = {t.id for t in results}
        assert "plan-impl" in ids
    
    def test_search_by_title(self, sample_knowledge_dir):
        """Test searching topics by title."""
        scanner = TopicScanner(sample_knowledge_dir)
        
        results = scanner.search("Python")
        assert len(results) == 1
        assert results[0].id == "seed-python"
    
    def test_search_by_keyword(self, sample_knowledge_dir):
        """Test searching topics by keyword."""
        scanner = TopicScanner(sample_knowledge_dir)
        
        results = scanner.search("setup")
        assert len(results) == 1
        assert results[0].id == "seed-python"
    
    def test_search_case_insensitive(self, sample_knowledge_dir):
        """Test search is case insensitive."""
        scanner = TopicScanner(sample_knowledge_dir)
        
        results_lower = scanner.search("python")
        results_upper = scanner.search("PYTHON")
        
        assert len(results_lower) == len(results_upper) == 1
    
    def test_no_heading_uses_filename(self, tmp_path):
        """Test that files without headings use filename as title."""
        topics_dir = tmp_path / ".tf" / "knowledge" / "topics"
        topics_dir.mkdir(parents=True)
        
        # Create file without heading
        (topics_dir / "no-heading.md").write_text("Just some content without a heading.")
        
        scanner = TopicScanner(tmp_path / ".tf" / "knowledge")
        topics = scanner.scan()
        
        assert len(topics) == 1
        assert topics[0].title == "no-heading"  # Falls back to filename
    
    def test_title_with_formatting(self, tmp_path):
        """Test that formatting is stripped from titles."""
        topics_dir = tmp_path / ".tf" / "knowledge" / "topics"
        topics_dir.mkdir(parents=True)
        
        (topics_dir / "formatted.md").write_text("# **Bold** and _italic_ title")
        
        scanner = TopicScanner(tmp_path / ".tf" / "knowledge")
        topics = scanner.scan()
        
        assert topics[0].title == "Bold and italic title"


class TestTopicSorting:
    """Test topic sorting behavior."""
    
    def test_sorting_by_type_and_title(self, tmp_path):
        """Test topics are sorted by type priority then title."""
        topics_dir = tmp_path / ".tf" / "knowledge" / "topics"
        topics_dir.mkdir(parents=True)
        
        # Create topics in reverse order (prefix determines type)
        (topics_dir / "z-topic.md").write_text("# Z Topic")  # other
        (topics_dir / "spike-a-topic.md").write_text("# A Topic")  # spike
        (topics_dir / "plan-m-topic.md").write_text("# M Topic")  # plan
        
        scanner = TopicScanner(tmp_path / ".tf" / "knowledge")
        topics = scanner.scan()
        
        # Should be sorted by type priority: plan, spike, other
        assert topics[0].topic_type == "plan"
        assert topics[1].topic_type == "spike"
        assert topics[2].topic_type == "other"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
