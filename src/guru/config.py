"""
Configuration management for Guru CLI.

Handles user configuration, templates, and project profiles.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

from .utils import ensure_directory


# Default configuration directory
DEFAULT_CONFIG_DIR = Path.home() / ".guru"
TEMPLATES_DIR_NAME = "templates"
PROFILES_DIR_NAME = "profiles"


class ConfigManager:
    """
    Manager for Guru configuration, templates, and profiles.

    Configuration structure:
    ~/.guru/
    ├── templates/        # Custom Jinja2 templates
    │   └── custom.md.j2
    └── profiles/         # Project profiles (YAML)
        └── my-project.yaml
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Custom configuration directory (defaults to ~/.guru)
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.templates_dir = self.config_dir / TEMPLATES_DIR_NAME
        self.profiles_dir = self.config_dir / PROFILES_DIR_NAME

    def ensure_config_dirs(self) -> None:
        """Create configuration directories if they don't exist."""
        ensure_directory(self.config_dir)
        ensure_directory(self.templates_dir)
        ensure_directory(self.profiles_dir)

    # --- Template Management ---

    def list_templates(self) -> List[str]:
        """
        List available custom templates.

        Returns:
            List of template names (without extension)
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        for path in self.templates_dir.glob("*.j2"):
            templates.append(path.stem.replace(".md", ""))
        for path in self.templates_dir.glob("*.jinja2"):
            templates.append(path.stem.replace(".md", ""))

        return sorted(set(templates))

    def get_template_path(self, name: str) -> Optional[Path]:
        """
        Get the path to a template by name.

        Args:
            name: Template name (without extension)

        Returns:
            Path to the template file, or None if not found
        """
        # Try different extensions
        for ext in [".md.j2", ".j2", ".md.jinja2", ".jinja2"]:
            path = self.templates_dir / f"{name}{ext}"
            if path.exists():
                return path

        return None

    def load_template(self, name: str) -> Optional[str]:
        """
        Load a template by name.

        Args:
            name: Template name

        Returns:
            Template content, or None if not found
        """
        path = self.get_template_path(name)
        if path:
            return path.read_text(encoding="utf-8")
        return None

    def save_template(self, name: str, content: str) -> Path:
        """
        Save a custom template.

        Args:
            name: Template name
            content: Template content

        Returns:
            Path to the saved template
        """
        self.ensure_config_dirs()
        path = self.templates_dir / f"{name}.md.j2"
        path.write_text(content, encoding="utf-8")
        return path

    # --- Profile Management ---

    def list_profiles(self) -> List[str]:
        """
        List available project profiles.

        Returns:
            List of profile names (without extension)
        """
        if not self.profiles_dir.exists():
            return []

        profiles = []
        for path in self.profiles_dir.glob("*.yaml"):
            profiles.append(path.stem)
        for path in self.profiles_dir.glob("*.yml"):
            profiles.append(path.stem)

        return sorted(set(profiles))

    def get_profile_path(self, name: str) -> Optional[Path]:
        """
        Get the path to a profile by name.

        Args:
            name: Profile name (without extension)

        Returns:
            Path to the profile file, or None if not found
        """
        for ext in [".yaml", ".yml"]:
            path = self.profiles_dir / f"{name}{ext}"
            if path.exists():
                return path

        return None

    def load_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a project profile by name.

        Args:
            name: Profile name

        Returns:
            Profile data as dictionary, or None if not found

        Profile format:
        ```yaml
        name: my-project
        claude_md_path: ./CLAUDE.md
        template: default
        prompts_dir: ./prompts
        ```
        """
        path = self.get_profile_path(name)
        if not path:
            return None

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def save_profile(self, name: str, data: Dict[str, Any]) -> Path:
        """
        Save a project profile.

        Args:
            name: Profile name
            data: Profile data

        Returns:
            Path to the saved profile
        """
        self.ensure_config_dirs()
        path = self.profiles_dir / f"{name}.yaml"

        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

        return path

    def delete_profile(self, name: str) -> bool:
        """
        Delete a project profile.

        Args:
            name: Profile name

        Returns:
            True if deleted, False if not found
        """
        path = self.get_profile_path(name)
        if path:
            path.unlink()
            return True
        return False


class ProfileData:
    """
    Data class for project profile settings.
    """

    def __init__(
        self,
        name: str,
        claude_md_path: str = "./CLAUDE.md",
        template: str = "default",
        prompts_dir: str = "./prompts",
    ):
        self.name = name
        self.claude_md_path = claude_md_path
        self.template = template
        self.prompts_dir = prompts_dir

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for saving."""
        return {
            "name": self.name,
            "claude_md_path": self.claude_md_path,
            "template": self.template,
            "prompts_dir": self.prompts_dir,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfileData":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "unnamed"),
            claude_md_path=data.get("claude_md_path", "./CLAUDE.md"),
            template=data.get("template", "default"),
            prompts_dir=data.get("prompts_dir", "./prompts"),
        )
