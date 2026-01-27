"""
Prompt builder for generating structured prompts from CLAUDE.md data.
"""

from pathlib import Path
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape, Template

from .utils import ensure_directory, get_next_prompt_number


# Default template content (fallback if template file not found)
DEFAULT_TEMPLATE = """# Задача
{{ user_query }}

{% if tech_stack %}
# Стек технологий
{{ tech_stack }}
{% endif %}

{% if conventions %}
# Конвенции проекта
{{ conventions }}
{% endif %}

{% if constraints %}
# Ограничения и правила
{{ constraints }}
{% endif %}

{% if context %}
# Контекст проекта
{{ context }}
{% endif %}
"""


class PromptBuilder:
    """
    Builder for generating structured prompts using Jinja2 templates.
    """

    def __init__(self, template_path: Optional[Path] = None):
        """
        Initialize the prompt builder.

        Args:
            template_path: Path to a custom Jinja2 template file.
                          If None, uses the default built-in template.
        """
        self.template_path = template_path
        self._template: Optional[Template] = None
        self._load_template()

    def _load_template(self) -> None:
        """Load the Jinja2 template."""
        if self.template_path and self.template_path.exists():
            # Load from file
            env = Environment(
                loader=FileSystemLoader(self.template_path.parent),
                autoescape=select_autoescape(default=False),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            self._template = env.get_template(self.template_path.name)
        else:
            # Use default template
            env = Environment(
                autoescape=select_autoescape(default=False),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            self._template = env.from_string(DEFAULT_TEMPLATE)

    def set_template(self, template_path: Path) -> "PromptBuilder":
        """
        Set a new template.

        Args:
            template_path: Path to the template file

        Returns:
            Self for chaining
        """
        self.template_path = template_path
        self._load_template()
        return self

    def build(self, user_query: str, claude_md_data: Dict[str, str]) -> str:
        """
        Build a prompt from user query and CLAUDE.md data.

        Args:
            user_query: The user's query/task description
            claude_md_data: Dictionary with keys: 'tech_stack', 'conventions',
                           'constraints', 'context'

        Returns:
            Rendered prompt string
        """
        if not self._template:
            self._load_template()

        context = {
            "user_query": user_query.strip(),
            "tech_stack": claude_md_data.get("tech_stack", "").strip(),
            "conventions": claude_md_data.get("conventions", "").strip(),
            "constraints": claude_md_data.get("constraints", "").strip(),
            "context": claude_md_data.get("context", "").strip(),
        }

        return self._template.render(**context).strip()

    def save_prompt(
        self,
        content: str,
        prompts_dir: Optional[Path] = None,
        filename: Optional[str] = None,
    ) -> Path:
        """
        Save a prompt to a file with auto-incrementing filename.

        Args:
            content: The prompt content to save
            prompts_dir: Directory to save prompts (defaults to ./prompts)
            filename: Custom filename (optional, auto-generates if not provided)

        Returns:
            Path to the saved file
        """
        if prompts_dir is None:
            prompts_dir = Path.cwd() / "prompts"

        ensure_directory(prompts_dir)

        if filename:
            filepath = prompts_dir / filename
        else:
            # Auto-increment filename
            number = get_next_prompt_number(prompts_dir)
            filename = f"prompt_{number:02d}.md"
            filepath = prompts_dir / filename

        filepath.write_text(content, encoding="utf-8")
        return filepath

    def build_and_save(
        self,
        user_query: str,
        claude_md_data: Dict[str, str],
        prompts_dir: Optional[Path] = None,
    ) -> tuple[str, Path]:
        """
        Build a prompt and save it to a file.

        Args:
            user_query: The user's query/task description
            claude_md_data: Dictionary from ClaudeMarkdownParser.get_all_sections()
            prompts_dir: Directory to save prompts

        Returns:
            Tuple of (prompt content, path to saved file)
        """
        content = self.build(user_query, claude_md_data)
        filepath = self.save_prompt(content, prompts_dir)
        return content, filepath
