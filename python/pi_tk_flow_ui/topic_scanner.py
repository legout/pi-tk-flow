"""Topic scanning for knowledge base browsing.

This module provides on-the-fly scanning of .tf/knowledge/topics/*.md files
with title extraction and prefix-based classification.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Topic:
    """Represents a knowledge topic.
    
    Attributes:
        id: Topic identifier (filename without extension)
        title: Extracted title from first # heading
        topic_type: Classification (seed, plan, spike, baseline, other)
        file_path: Full path to the markdown file
        keywords: Extracted keywords from frontmatter or content
    """
    id: str
    title: str
    topic_type: str
    file_path: Path
    keywords: list[str] = field(default_factory=list)


class TopicScanError(Exception):
    """Raised when topic scanning fails."""
    pass


class TopicScanner:
    """Scans knowledge base topics from .tf/knowledge/topics/*.md.
    
    This scanner:
    1. Finds all .md files in the topics directory
    2. Extracts titles from the first # heading
    3. Classifies topics by filename prefix
    4. Returns sorted, grouped topic metadata
    
    Topic types (by filename prefix):
    - seed-*: Project scaffolding topics
    - plan-*: Planning workflow topics  
    - spike-*: Spike/research topics
    - baseline-*: Baseline pattern topics
    - other: Anything else
    
    Example:
        >>> scanner = TopicScanner()
        >>> topics = scanner.scan()
        >>> for topic in topics:
        ...     print(f"{topic.topic_type}: {topic.title}")
    """
    
    def __init__(self, knowledge_dir: Optional[Path] = None):
        """Initialize the scanner.
        
        Args:
            knowledge_dir: Path to knowledge directory. If None, auto-discovers.
        """
        if knowledge_dir is None:
            knowledge_dir = self._find_knowledge_dir()
        
        self.knowledge_dir = Path(knowledge_dir)
        self.topics_dir = self.knowledge_dir / "topics"
    
    def _find_knowledge_dir(self) -> Path:
        """Find the knowledge directory by walking up from cwd."""
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            tf_dir = parent / ".tf"
            if tf_dir.is_dir():
                knowledge_dir = tf_dir / "knowledge"
                if knowledge_dir.is_dir():
                    return knowledge_dir
        # Fallback
        return cwd / ".tf" / "knowledge"
    
    def scan(self) -> list[Topic]:
        """Scan all topics from the topics directory.
        
        Returns:
            List of Topic objects sorted by type and title.
            Returns empty list if topics directory doesn't exist.
        """
        if not self.topics_dir.exists():
            logger.debug(f"Topics directory not found: {self.topics_dir}")
            return []
        
        topics: list[Topic] = []
        
        try:
            for file_path in self.topics_dir.iterdir():
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() != ".md":
                    continue
                
                try:
                    topic = self._parse_topic(file_path)
                    if topic:
                        topics.append(topic)
                except Exception as e:
                    logger.warning(f"Failed to parse topic {file_path.name}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error scanning topics directory: {e}")
            return []
        
        # Sort by type priority then title (plan first, then spike, then seed/baseline/other)
        type_priority = {"plan": 0, "spike": 1, "seed": 2, "baseline": 3, "other": 4}
        topics.sort(key=lambda t: (type_priority.get(t.topic_type, 99), t.title.lower()))
        
        return topics
    
    def _parse_topic(self, file_path: Path) -> Optional[Topic]:
        """Parse a single topic file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Topic object or None if invalid
        """
        topic_id = file_path.stem
        topic_type = self._classify_type(topic_id)
        
        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Cannot read {file_path}: {e}")
            return None
        
        # Extract title from first # heading
        title = self._extract_title(content) or topic_id
        
        # Extract keywords from frontmatter if present
        keywords = self._extract_keywords(content)
        
        return Topic(
            id=topic_id,
            title=title,
            topic_type=topic_type,
            file_path=file_path,
            keywords=keywords
        )
    
    def _classify_type(self, filename: str) -> str:
        """Classify topic type from filename prefix.
        
        Args:
            filename: The filename (without extension)
            
        Returns:
            Topic type string
        """
        # Check for prefix patterns
        if filename.startswith("seed-"):
            return "seed"
        elif filename.startswith("plan-"):
            return "plan"
        elif filename.startswith("spike-"):
            return "spike"
        elif filename.startswith("baseline-"):
            return "baseline"
        else:
            return "other"
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from first # heading in markdown.
        
        Args:
            content: Markdown file content
            
        Returns:
            Title string or None if no heading found
        """
        # Look for first # heading (not ## or ###)
        # Match lines starting with # followed by space
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# ") and not line.startswith("##"):
                # Extract title (remove # and whitespace)
                title = line[2:].strip()
                # Remove any formatting
                title = re.sub(r"\*\*|__|\*|_", "", title)
                return title
        
        return None
    
    def _extract_keywords(self, content: str) -> list[str]:
        """Extract keywords from YAML frontmatter if present.
        
        Args:
            content: Markdown file content
            
        Returns:
            List of keywords
        """
        # Check for YAML frontmatter
        if not content.startswith("---"):
            return []
        
        try:
            # Find end of frontmatter
            end_match = re.search(r"\n---\s*\n", content[3:])
            if not end_match:
                return []
            
            frontmatter = content[3:3+end_match.start()]
            
            # Parse frontmatter as YAML for robust keyword extraction
            import yaml
            try:
                data = yaml.safe_load(frontmatter)
                if isinstance(data, dict) and "keywords" in data:
                    keywords = data["keywords"]
                    if isinstance(keywords, list):
                        return [str(k).strip() for k in keywords if k]
                    elif isinstance(keywords, str):
                        return [keywords.strip()]
            except yaml.YAMLError:
                # Fallback to regex parsing if YAML fails
                pass
            
            # Fallback: Look for keywords field with regex
            keywords_match = re.search(r"^keywords:\s*(.+)$", frontmatter, re.MULTILINE)
            if keywords_match:
                keywords_str = keywords_match.group(1).strip()
                # Handle list format: [a, b, c]
                if keywords_str.startswith("[") and keywords_str.endswith("]"):
                    inner = keywords_str[1:-1]
                    return [k.strip().strip('"\'') for k in inner.split(",") if k.strip()]
                else:
                    # Single keyword
                    return [keywords_str]
            
        except Exception as e:
            logger.debug(f"Error extracting keywords: {e}")
        
        return []
    
    def group_by_type(self, topics: Optional[list[Topic]] = None) -> dict[str, list[Topic]]:
        """Group topics by type.
        
        Args:
            topics: List of topics to group. Uses scanned topics if None.
            
        Returns:
            Dictionary mapping type to list of topics
        """
        if topics is None:
            topics = self.scan()
        
        groups: dict[str, list[Topic]] = {
            "seed": [],
            "plan": [],
            "spike": [],
            "baseline": [],
            "other": []
        }
        
        for topic in topics:
            groups.setdefault(topic.topic_type, []).append(topic)
        
        return groups
    
    def get_by_id(self, topic_id: str) -> Optional[Topic]:
        """Get a topic by its ID.
        
        Args:
            topic_id: The topic ID to look up
            
        Returns:
            The topic if found, None otherwise
        """
        topics = self.scan()
        for topic in topics:
            if topic.id == topic_id:
                return topic
        return None
    
    def search(self, query: str) -> list[Topic]:
        """Search topics by query string.
        
        Searches in:
        - Topic ID
        - Title
        - Keywords
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of matching topics
        """
        topics = self.scan()
        query_lower = query.lower()
        
        results = []
        for topic in topics:
            # Search in ID
            if query_lower in topic.id.lower():
                results.append(topic)
                continue
            # Search in title
            if query_lower in topic.title.lower():
                results.append(topic)
                continue
            # Search in keywords
            if any(query_lower in kw.lower() for kw in topic.keywords):
                results.append(topic)
                continue
        
        return results
