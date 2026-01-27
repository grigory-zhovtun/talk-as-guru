"""
Parser for CLAUDE.md files.

Extracts structured sections from CLAUDE.md files including:
- Tech stack
- Conventions
- Constraints/rules
- General context
- Relevance-filtered context for specific queries
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ClaudeMarkdownParser:
    """
    Parser for CLAUDE.md files.

    Supports various heading formats:
    - Markdown headers: # Header, ## Header
    - Bold headers: **Header**
    - Underline headers: Header\n===

    Uses keyword matching to identify sections.
    """

    # Keywords for identifying different sections (case-insensitive)
    TECH_KEYWORDS = ["tech", "stack", "technology", "technologies", "tools", "dependencies"]
    CONVENTION_KEYWORDS = ["convention", "conventions", "style", "formatting", "patterns", "practices"]
    CONSTRAINT_KEYWORDS = ["constraint", "constraints", "rule", "rules", "restriction", "restrictions",
                          "important", "warning", "avoid", "never", "always", "must"]

    def __init__(self, filepath: Optional[Path] = None):
        """
        Initialize the parser.

        Args:
            filepath: Path to CLAUDE.md file (optional, can be set later with load())
        """
        self.filepath = filepath
        self._content: Optional[str] = None
        self._sections: Dict[str, str] = {}
        self._all_sections: List[Tuple[str, str]] = []  # All (title, content) pairs
        self._file_size: int = 0

    def load(self, filepath: Optional[Path] = None) -> "ClaudeMarkdownParser":
        """
        Load and parse a CLAUDE.md file.

        Args:
            filepath: Path to CLAUDE.md file (uses instance filepath if not provided)

        Returns:
            Self for chaining

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If no filepath is provided
        """
        if filepath:
            self.filepath = filepath

        if not self.filepath:
            raise ValueError("No filepath provided")

        if not self.filepath.exists():
            raise FileNotFoundError(f"CLAUDE.md not found at: {self.filepath}")

        self._content = self.filepath.read_text(encoding="utf-8")
        self._file_size = self.filepath.stat().st_size
        self._parse_sections()

        return self

    def reload(self) -> "ClaudeMarkdownParser":
        """
        Reload the CLAUDE.md file from disk.

        Returns:
            Self for chaining
        """
        return self.load(self.filepath)

    @property
    def content(self) -> str:
        """Get the raw content of the file."""
        return self._content or ""

    @property
    def file_size(self) -> int:
        """Get the file size in bytes."""
        return self._file_size

    def _parse_sections(self) -> None:
        """Parse the content into sections based on headings."""
        if not self._content:
            return

        self._sections = {}
        self._all_sections = self._split_into_sections(self._content)

        for title, content in self._all_sections:
            section_type = self._classify_section(title)
            if section_type:
                if section_type in self._sections:
                    self._sections[section_type] += "\n\n" + content
                else:
                    self._sections[section_type] = content

    def _split_into_sections(self, content: str) -> List[Tuple[str, str]]:
        """
        Split content into sections based on headings.

        Returns:
            List of (title, content) tuples
        """
        sections = []

        # Pattern to match various heading styles
        # - Markdown headers: # Header, ## Header, ### Header
        # - Bold headers: **Header**
        heading_pattern = re.compile(
            r"^(?:"
            r"(#{1,3})\s+(.+?)(?:\s*#*)$"  # Markdown headers
            r"|"
            r"\*\*(.+?)\*\*\s*$"  # Bold headers
            r")",
            re.MULTILINE
        )

        matches = list(heading_pattern.finditer(content))

        if not matches:
            # No sections found, treat entire content as context
            sections.append(("context", content.strip()))
            return sections

        for i, match in enumerate(matches):
            # Determine title from the match groups
            if match.group(2):  # Markdown header
                title = match.group(2).strip()
            else:  # Bold header
                title = match.group(3).strip()

            # Get content until next heading or end of file
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

            section_content = content[start:end].strip()
            if section_content:
                sections.append((title, section_content))

        return sections

    def _classify_section(self, title: str) -> Optional[str]:
        """
        Classify a section based on its title.

        Args:
            title: Section title

        Returns:
            Section type ('tech_stack', 'conventions', 'constraints') or None
        """
        title_lower = title.lower()

        # Check for tech stack
        for keyword in self.TECH_KEYWORDS:
            if keyword in title_lower:
                return "tech_stack"

        # Check for conventions
        for keyword in self.CONVENTION_KEYWORDS:
            if keyword in title_lower:
                return "conventions"

        # Check for constraints
        for keyword in self.CONSTRAINT_KEYWORDS:
            if keyword in title_lower:
                return "constraints"

        return None

    def extract_tech_stack(self) -> str:
        """Extract the tech stack section."""
        return self._sections.get("tech_stack", "")

    def extract_conventions(self) -> str:
        """Extract the conventions section."""
        return self._sections.get("conventions", "")

    def extract_constraints(self) -> str:
        """Extract the constraints/rules section."""
        return self._sections.get("constraints", "")

    def extract_context(self) -> str:
        """Extract the full context (entire file content)."""
        return self._content or ""

    def get_all_sections(self) -> Dict[str, str]:
        """
        Get all parsed sections as a dictionary.

        Returns:
            Dictionary with keys: 'tech_stack', 'conventions', 'constraints', 'context'
        """
        return {
            "tech_stack": self.extract_tech_stack(),
            "conventions": self.extract_conventions(),
            "constraints": self.extract_constraints(),
            "context": self.extract_context(),
        }

    def get_relevant_sections(self, query: str) -> str:
        """
        Get sections relevant to the user's query.

        Filters sections by matching query keywords against section titles and content.
        Returns only unclassified sections (not tech_stack/conventions/constraints),
        sorted by relevance to the query. This avoids dumping the entire file.

        Args:
            query: User's query string

        Returns:
            Filtered context string with only relevant sections
        """
        if not self._all_sections:
            return self._content or ""

        query_lower = query.lower()
        query_words = set(re.findall(r'[a-zA-Zа-яА-ЯёЁ]{3,}', query_lower))

        # Collect all unclassified sections (project-specific context)
        unclassified: List[Tuple[float, str, str]] = []

        for title, content in self._all_sections:
            section_type = self._classify_section(title)
            if section_type in ("tech_stack", "conventions", "constraints"):
                continue

            score = self._relevance_score(title, content, query_lower, query_words)
            unclassified.append((score, title, content))

        if not unclassified:
            return ""

        # Sort by relevance score descending (highest relevance first)
        unclassified.sort(key=lambda x: x[0], reverse=True)

        # Include sections with score > 0 first, then remaining sections
        # This ensures relevant sections are at the top
        parts = []
        for _score, title, content in unclassified:
            parts.append(f"## {title}\n{content}")

        return "\n\n".join(parts)

    def _relevance_score(
        self, title: str, content: str, query_lower: str, query_words: set
    ) -> float:
        """
        Calculate relevance score of a section to the query.

        Args:
            title: Section title
            content: Section content
            query_lower: Lowercased query string
            query_words: Set of query words (3+ chars)

        Returns:
            Relevance score (0 = not relevant)
        """
        title_lower = title.lower()
        content_lower = content.lower()
        combined = title_lower + " " + content_lower

        score = 0.0

        # Title matches are worth more
        for word in query_words:
            if word in title_lower:
                score += 3.0
            if word in content_lower:
                score += 1.0

        # Check for multi-word phrase matches in title
        if len(query_lower) > 5 and query_lower in combined:
            score += 5.0

        return score

    def get_summary(self) -> Dict[str, any]:
        """
        Get a summary of the parsed file.

        Returns:
            Dictionary with file stats and section availability
        """
        sections = self.get_all_sections()
        return {
            "filepath": str(self.filepath) if self.filepath else None,
            "file_size": self._file_size,
            "has_tech_stack": bool(sections["tech_stack"]),
            "has_conventions": bool(sections["conventions"]),
            "has_constraints": bool(sections["constraints"]),
            "sections_found": sum(1 for k, v in sections.items() if v and k != "context"),
        }
