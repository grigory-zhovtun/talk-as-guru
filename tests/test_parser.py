"""Tests for ClaudeMarkdownParser."""

import tempfile
from pathlib import Path

import pytest

from guru.parser import ClaudeMarkdownParser


class TestClaudeMarkdownParser:
    """Tests for the CLAUDE.md parser."""

    def test_load_simple_file(self, tmp_path: Path) -> None:
        """Test loading a simple CLAUDE.md file."""
        content = "# Test\nSome content"
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        assert parser.content == content
        assert parser.file_size > 0

    def test_extract_tech_stack(self, tmp_path: Path) -> None:
        """Test extracting tech stack section."""
        content = """# Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL

# Other
Something else"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        tech_stack = parser.extract_tech_stack()
        assert "Python 3.11" in tech_stack
        assert "FastAPI" in tech_stack
        assert "PostgreSQL" in tech_stack

    def test_extract_conventions(self, tmp_path: Path) -> None:
        """Test extracting conventions section."""
        content = """# Conventions
- Use type hints
- Follow PEP 8

# Tech Stack
- Python"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        conventions = parser.extract_conventions()
        assert "type hints" in conventions
        assert "PEP 8" in conventions

    def test_extract_constraints(self, tmp_path: Path) -> None:
        """Test extracting constraints/rules section."""
        content = """# Important Rules
- Never commit secrets
- Always write tests

# Conventions
- Use type hints"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        constraints = parser.extract_constraints()
        assert "Never commit secrets" in constraints
        assert "write tests" in constraints

    def test_extract_context_returns_full_content(self, tmp_path: Path) -> None:
        """Test that extract_context returns the full file content."""
        content = """# Tech Stack
- Python

# Conventions
- PEP 8"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        context = parser.extract_context()
        assert context == content

    def test_get_all_sections(self, tmp_path: Path) -> None:
        """Test getting all sections at once."""
        content = """# Tech Stack
- Python

# Conventions
- PEP 8

# Rules
- No secrets"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        sections = parser.get_all_sections()

        assert "tech_stack" in sections
        assert "conventions" in sections
        assert "constraints" in sections
        assert "context" in sections

    def test_reload(self, tmp_path: Path) -> None:
        """Test reloading a file after changes."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Original")

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        assert "Original" in parser.content

        # Modify the file
        claude_md.write_text("# Updated")

        # Reload
        parser.reload()

        assert "Updated" in parser.content

    def test_bold_heading_format(self, tmp_path: Path) -> None:
        """Test parsing bold heading format."""
        content = """**Tech Stack**
- Python

**Conventions**
- PEP 8"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        assert "Python" in parser.extract_tech_stack()
        assert "PEP 8" in parser.extract_conventions()

    def test_h2_heading_format(self, tmp_path: Path) -> None:
        """Test parsing ## heading format."""
        content = """## Tech Stack
- Python

## Conventions
- PEP 8"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        assert "Python" in parser.extract_tech_stack()
        assert "PEP 8" in parser.extract_conventions()

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test handling of missing file."""
        parser = ClaudeMarkdownParser(tmp_path / "nonexistent.md")

        with pytest.raises(FileNotFoundError):
            parser.load()

    def test_no_filepath_provided(self) -> None:
        """Test error when no filepath is provided."""
        parser = ClaudeMarkdownParser()

        with pytest.raises(ValueError):
            parser.load()

    def test_fallback_to_context_when_no_sections(self, tmp_path: Path) -> None:
        """Test that content is used as context when no sections found."""
        content = "Just some plain text without any recognizable sections."
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        sections = parser.get_all_sections()

        # Context should contain the full content
        assert sections["context"] == content

    def test_get_summary(self, tmp_path: Path) -> None:
        """Test get_summary method."""
        content = """# Tech Stack
- Python

# Conventions
- PEP 8"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(content)

        parser = ClaudeMarkdownParser(claude_md)
        parser.load()

        summary = parser.get_summary()

        assert summary["filepath"] == str(claude_md)
        assert summary["file_size"] > 0
        assert summary["has_tech_stack"] is True
        assert summary["has_conventions"] is True
        assert summary["sections_found"] >= 2


class TestAutoIncrement:
    """Tests for prompt number auto-increment."""

    def test_get_next_prompt_number_empty_dir(self, tmp_path: Path) -> None:
        """Test getting next number in empty directory."""
        from guru.utils import get_next_prompt_number

        assert get_next_prompt_number(tmp_path) == 1

    def test_get_next_prompt_number_with_existing(self, tmp_path: Path) -> None:
        """Test getting next number with existing prompts."""
        from guru.utils import get_next_prompt_number

        # Create some existing prompts
        (tmp_path / "prompt_01.md").write_text("test")
        (tmp_path / "prompt_02.md").write_text("test")
        (tmp_path / "prompt_05.md").write_text("test")

        assert get_next_prompt_number(tmp_path) == 6

    def test_get_next_prompt_number_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test getting next number for nonexistent directory."""
        from guru.utils import get_next_prompt_number

        nonexistent = tmp_path / "nonexistent"
        assert get_next_prompt_number(nonexistent) == 1
