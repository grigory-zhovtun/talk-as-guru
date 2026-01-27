"""
Integration with Claude Code CLI.
"""

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClaudeResult:
    """Result from running Claude Code CLI."""

    success: bool
    output: str
    error: Optional[str] = None
    return_code: int = 0


def check_claude_available() -> bool:
    """
    Check if Claude Code CLI is available.

    Returns:
        True if 'claude' command is found in PATH
    """
    return shutil.which("claude") is not None


def run_claude_code(
    prompt: str,
    timeout: int = 300,
    print_mode: bool = True,
) -> ClaudeResult:
    """
    Run Claude Code CLI with a prompt.

    Args:
        prompt: The prompt to send to Claude
        timeout: Timeout in seconds (default: 5 minutes)
        print_mode: Use --print flag for non-interactive output

    Returns:
        ClaudeResult with success status, output, and any errors
    """
    if not check_claude_available():
        return ClaudeResult(
            success=False,
            output="",
            error="Claude Code CLI not found. Please install it from https://claude.ai/code",
            return_code=-1,
        )

    # Build command
    cmd = ["claude"]
    if print_mode:
        cmd.append("--print")
    cmd.append(prompt)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return ClaudeResult(
                success=True,
                output=result.stdout.strip(),
                return_code=result.returncode,
            )
        else:
            return ClaudeResult(
                success=False,
                output=result.stdout.strip() if result.stdout else "",
                error=result.stderr.strip() if result.stderr else "Unknown error",
                return_code=result.returncode,
            )

    except subprocess.TimeoutExpired:
        return ClaudeResult(
            success=False,
            output="",
            error=f"Command timed out after {timeout} seconds",
            return_code=-1,
        )
    except Exception as e:
        return ClaudeResult(
            success=False,
            output="",
            error=str(e),
            return_code=-1,
        )


def run_claude_interactive(prompt: str) -> ClaudeResult:
    """
    Run Claude Code CLI in interactive mode.

    This opens an interactive session with the prompt as initial context.

    Args:
        prompt: The initial prompt/context

    Returns:
        ClaudeResult (note: output will be empty for interactive mode)
    """
    if not check_claude_available():
        return ClaudeResult(
            success=False,
            output="",
            error="Claude Code CLI not found",
            return_code=-1,
        )

    try:
        # Start interactive Claude session
        result = subprocess.run(
            ["claude", prompt],
            text=True,
        )

        return ClaudeResult(
            success=result.returncode == 0,
            output="",  # Interactive mode doesn't capture output
            return_code=result.returncode,
        )

    except Exception as e:
        return ClaudeResult(
            success=False,
            output="",
            error=str(e),
            return_code=-1,
        )


ENRICH_SYSTEM_PROMPT = """Ты — эксперт по созданию структурированных промптов для AI-ассистентов разработки.

Тебе дан запрос пользователя и контекст проекта из CLAUDE.md.
Твоя задача — создать обогащённый промпт, который включает:

1. **Роль** — определи оптимальную роль для выполнения задачи (напр. "Senior React/Next.js разработчик, специализирующийся на системах уведомлений")
2. **Задача** — переформулируй запрос пользователя чётко и конкретно
3. **Подзадачи** — разбей задачу на 3-7 конкретных шагов
4. **Релевантный контекст** — выбери ТОЛЬКО релевантные части из CLAUDE.md (не копируй всё!)
5. **Ограничения** — сформулируй технические ограничения на основе проекта

Формат ответа — чистый Markdown без пояснений. Используй русский язык."""


def enrich_prompt(
    user_query: str,
    claude_md_content: str,
    timeout: int = 120,
) -> ClaudeResult:
    """
    Use Claude Code CLI to enrich a user query into a structured prompt.

    Sends the user query + CLAUDE.md content to Claude for intelligent
    analysis, role detection, task decomposition, and context filtering.

    Args:
        user_query: The user's original query
        claude_md_content: Full content of CLAUDE.md
        timeout: Timeout in seconds

    Returns:
        ClaudeResult with the enriched prompt as output
    """
    if not check_claude_available():
        return ClaudeResult(
            success=False,
            output="",
            error="Claude Code CLI not found. Install from https://claude.ai/code",
            return_code=-1,
        )

    enrichment_prompt = f"""{ENRICH_SYSTEM_PROMPT}

---

## Запрос пользователя
{user_query}

---

## Контекст проекта (CLAUDE.md)
{claude_md_content}

---

Создай обогащённый промпт:"""

    return run_claude_code(enrichment_prompt, timeout=timeout, print_mode=True)
