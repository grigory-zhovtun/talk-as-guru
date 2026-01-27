"""
Utility functions for Guru CLI.
"""

import re
from pathlib import Path
from typing import Optional


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        The path to the directory
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_next_prompt_number(prompts_dir: Path) -> int:
    """
    Get the next prompt number for auto-incrementing filenames.

    Scans the prompts directory for existing prompt_NN.md files
    and returns the next available number.

    Args:
        prompts_dir: Path to the prompts directory

    Returns:
        The next available prompt number (starting from 1)
    """
    if not prompts_dir.exists():
        return 1

    existing = list(prompts_dir.glob("prompt_*.md"))
    if not existing:
        return 1

    numbers = []
    pattern = re.compile(r"prompt_(\d+)\.md$")

    for filepath in existing:
        match = pattern.match(filepath.name)
        if match:
            numbers.append(int(match.group(1)))

    if not numbers:
        return 1

    return max(numbers) + 1


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "2.3 KB", "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def find_claude_md(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find CLAUDE.md file starting from a given path.

    First checks the current directory, then walks up the directory tree.

    Args:
        start_path: Starting path to search from (defaults to cwd)

    Returns:
        Path to CLAUDE.md if found, None otherwise
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Check current directory first
    claude_md = current / "CLAUDE.md"
    if claude_md.exists():
        return claude_md

    # Walk up the directory tree
    for parent in current.parents:
        claude_md = parent / "CLAUDE.md"
        if claude_md.exists():
            return claude_md

    return None


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename.

    Args:
        name: String to sanitize

    Returns:
        Sanitized string safe for use as filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')

    # Limit length
    name = name[:50]

    # Remove leading/trailing whitespace and dots
    name = name.strip('. ')

    return name or "unnamed"
