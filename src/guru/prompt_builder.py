"""
Prompt builder for generating structured prompts from CLAUDE.md data.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape, Template

from .utils import ensure_directory, get_next_prompt_number


# Default template content (fallback if template file not found)
DEFAULT_TEMPLATE = """{% if role %}
# Роль
{{ role }}
{% endif %}

# Задача
{{ user_query }}

{% if tech_stack %}
# Техническое окружение
{{ tech_stack }}
{% endif %}

{% if relevant_context %}
# Релевантный контекст
{{ relevant_context }}
{% endif %}

{% if conventions %}
# Конвенции
{{ conventions }}
{% endif %}

{% if constraints %}
# Ограничения и правила
{{ constraints }}
{% endif %}
"""

# Role mapping: technology keywords -> role description
ROLE_MAP: List[Tuple[List[str], str]] = [
    (["react", "next.js", "nextjs", "next", "jsx", "tsx", "frontend", "фронтенд", "шапк", "компонент",
      "кнопк", "форм", "стил", "css", "tailwind", "ui", "ux", "интерфейс", "уведомлен", "колокольчик",
      "модальн", "страниц", "layout"],
     "Senior Frontend разработчик"),
    (["python", "fastapi", "django", "flask", "backend", "бэкенд", "api", "endpoint", "серверн",
      "маршрут", "route", "миграц", "alembic"],
     "Senior Backend разработчик (Python)"),
    (["sql", "postgres", "postgresql", "mysql", "database", "db", "база данных", "запрос", "модел",
      "таблиц", "индекс"],
     "Senior Database разработчик"),
    (["docker", "kubernetes", "k8s", "ci/cd", "deploy", "nginx", "devops", "деплой", "контейнер"],
     "Senior DevOps инженер"),
    (["test", "тест", "pytest", "jest", "cypress", "e2e", "unit", "integration"],
     "Senior QA инженер"),
    (["security", "безопасност", "auth", "аутентификац", "авторизац", "jwt", "oauth", "csrf", "xss"],
     "Senior Security инженер"),
    (["go", "golang", "goroutine", "channel"],
     "Senior Go разработчик"),
    (["typescript", "ts", "type", "interface", "generic"],
     "Senior TypeScript разработчик"),
]


def detect_role(query: str, tech_stack: str) -> str:
    """
    Detect the appropriate role based on the query and tech stack.

    Args:
        query: User's query
        tech_stack: Extracted tech stack from CLAUDE.md

    Returns:
        Role description string
    """
    combined = (query + " " + tech_stack).lower()

    best_role = ""
    best_score = 0

    for keywords, role in ROLE_MAP:
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            best_role = role

    if not best_role:
        return "Senior разработчик"

    # Enhance role with specific tech from stack if relevant
    tech_details = []
    tech_lower = tech_stack.lower()
    if "next.js" in tech_lower or "nextjs" in tech_lower or "next" in tech_lower:
        tech_details.append("Next.js")
    if "react" in tech_lower:
        tech_details.append("React")
    if "typescript" in tech_lower:
        tech_details.append("TypeScript")
    if "fastapi" in tech_lower:
        tech_details.append("FastAPI")
    if "python" in tech_lower:
        tech_details.append("Python")
    if "tailwind" in tech_lower:
        tech_details.append("Tailwind CSS")
    if "postgresql" in tech_lower or "postgres" in tech_lower:
        tech_details.append("PostgreSQL")

    if tech_details and "Frontend" in best_role:
        return f"{best_role} ({', '.join(tech_details[:3])})"
    elif tech_details and "Backend" in best_role:
        backend_tech = [t for t in tech_details if t in ("FastAPI", "Python", "PostgreSQL")]
        if backend_tech:
            return f"{best_role.split('(')[0].strip()} ({', '.join(backend_tech[:3])})"

    return best_role


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
                           'constraints', 'relevant_context'
                           (also accepts legacy 'context' key)

        Returns:
            Rendered prompt string
        """
        if not self._template:
            self._load_template()

        tech_stack = claude_md_data.get("tech_stack", "").strip()
        role = detect_role(user_query, tech_stack)

        context = {
            "user_query": user_query.strip(),
            "role": role,
            "tech_stack": tech_stack,
            "conventions": claude_md_data.get("conventions", "").strip(),
            "constraints": claude_md_data.get("constraints", "").strip(),
            "relevant_context": claude_md_data.get("relevant_context", "").strip(),
            # Legacy support
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
