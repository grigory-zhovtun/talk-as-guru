"""
CLI entry point for Guru.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .parser import ClaudeMarkdownParser
from .prompt_builder import PromptBuilder
from .config import ConfigManager
from .repl import GuruREPL
from .utils import find_claude_md, format_file_size
from .claude_integration import check_claude_available, enrich_prompt

# Create Typer app
app = typer.Typer(
    name="guru",
    help="CLI utility for analyzing CLAUDE.md and generating structured prompts for Claude Code.",
    add_completion=False,
    invoke_without_command=True,
)

# Rich console for output
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"Guru v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(
        None,
        help="Optional query to process (skips REPL if provided).",
    ),
    claude_md: Optional[Path] = typer.Option(
        None,
        "--claude-md",
        "-c",
        help="Path to CLAUDE.md file (auto-detected if not specified).",
    ),
    prompts_dir: Optional[Path] = typer.Option(
        None,
        "--prompts-dir",
        "-p",
        help="Directory for saving prompts (default: ./prompts).",
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Template name to use.",
    ),
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        help="Load a saved profile.",
    ),
    smart: bool = typer.Option(
        False,
        "--smart",
        "-s",
        help="Use Claude Code CLI to enrich the prompt with AI analysis.",
    ),
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """
    Guru - CLI utility for generating structured prompts from CLAUDE.md.

    Start Guru REPL or process a single query.
    If a query is provided, processes it and exits.
    Otherwise, starts the interactive REPL.
    """
    # Skip if a subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return

    # Initialize config manager
    config = ConfigManager()
    config.ensure_config_dirs()

    # Load profile if specified
    if profile:
        profile_data = config.load_profile(profile)
        if profile_data:
            if not claude_md:
                claude_md = Path(profile_data.get("claude_md_path", "./CLAUDE.md"))
            if not template:
                template = profile_data.get("template")
            if not prompts_dir:
                prompts_dir = Path(profile_data.get("prompts_dir", "./prompts"))
        else:
            console.print(f"[yellow]Warning:[/yellow] Profile '{profile}' not found, using defaults.")

    # Find CLAUDE.md
    if claude_md:
        claude_md_path = claude_md if claude_md.is_absolute() else Path.cwd() / claude_md
    else:
        claude_md_path = find_claude_md()

    if not claude_md_path or not claude_md_path.exists():
        _show_no_claude_md_error(claude_md_path)
        raise typer.Exit(1)

    # Initialize parser
    try:
        parser = ClaudeMarkdownParser(claude_md_path)
        parser.load()
    except Exception as e:
        console.print(f"[red]Error loading CLAUDE.md:[/red] {e}")
        raise typer.Exit(1)

    # Initialize prompt builder
    template_path = None
    if template and template != "default":
        template_path = config.get_template_path(template)
        if not template_path:
            console.print(f"[yellow]Warning:[/yellow] Template '{template}' not found, using default.")

    builder = PromptBuilder(template_path)

    # Set prompts directory
    if prompts_dir is None:
        prompts_dir = Path.cwd() / "prompts"
    elif not prompts_dir.is_absolute():
        prompts_dir = Path.cwd() / prompts_dir

    # Single query mode
    if query:
        _process_single_query(query, parser, builder, prompts_dir, smart)
        return

    # Start REPL
    try:
        repl = GuruREPL(
            console=console,
            parser=parser,
            builder=builder,
            config=config,
            prompts_dir=prompts_dir,
        )
        repl.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _show_no_claude_md_error(attempted_path: Optional[Path]) -> None:
    """Display error message when CLAUDE.md is not found."""
    error_text = """
[bold red]CLAUDE.md not found![/bold red]

Guru needs a CLAUDE.md file to understand your project context.

[bold]To fix this:[/bold]
1. Create a CLAUDE.md file in your project root
2. Or specify a path with: [cyan]guru --claude-md /path/to/CLAUDE.md[/cyan]

[bold]Example CLAUDE.md:[/bold]
[dim]
# Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL

# Conventions
- Use type hints everywhere
- Follow PEP 8 style guide
- Write docstrings for public functions

# Rules
- Never commit secrets
- Always write tests
[/dim]
"""
    if attempted_path:
        error_text = f"[dim]Looked for: {attempted_path}[/dim]\n" + error_text

    console.print(Panel(error_text.strip(), title="Error", border_style="red"))


def _process_single_query(
    query: str,
    parser: ClaudeMarkdownParser,
    builder: PromptBuilder,
    prompts_dir: Path,
    smart: bool = False,
) -> None:
    """Process a single query without starting the REPL."""
    try:
        if smart:
            # Smart mode: use Claude Code CLI to enrich the prompt
            if not check_claude_available():
                console.print("[red]Error:[/red] Claude Code CLI not found for --smart mode.")
                console.print("[dim]Install from: https://claude.ai/code[/dim]")
                console.print("[dim]Falling back to standard mode...[/dim]")
                _process_standard_query(query, parser, builder, prompts_dir)
                return

            console.print("[blue]Smart mode: enriching prompt via Claude Code...[/blue]")

            with console.status("[blue]Analyzing query...[/blue]", spinner="dots"):
                result = enrich_prompt(query, parser.extract_context())

            if result.success and result.output:
                # Save the enriched prompt
                from .utils import ensure_directory, get_next_prompt_number
                ensure_directory(prompts_dir)
                number = get_next_prompt_number(prompts_dir)
                filename = f"prompt_{number:02d}.md"
                filepath = prompts_dir / filename
                filepath.write_text(result.output, encoding="utf-8")

                console.print(f"[green]Saved (smart):[/green] {filepath}")
            else:
                console.print(f"[yellow]Smart mode failed:[/yellow] {result.error}")
                console.print("[dim]Falling back to standard mode...[/dim]")
                _process_standard_query(query, parser, builder, prompts_dir)
        else:
            _process_standard_query(query, parser, builder, prompts_dir)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _process_standard_query(
    query: str,
    parser: ClaudeMarkdownParser,
    builder: PromptBuilder,
    prompts_dir: Path,
) -> None:
    """Process a query using the standard template-based approach."""
    claude_md_data = parser.get_all_sections()
    # Replace full context dump with relevant sections only
    claude_md_data["relevant_context"] = parser.get_relevant_sections(query)
    content, filepath = builder.build_and_save(query, claude_md_data, prompts_dir)
    console.print(f"[green]Saved:[/green] {filepath}")


def run() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()
