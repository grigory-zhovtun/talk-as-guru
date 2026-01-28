"""
REPL (Read-Eval-Print Loop) for Guru CLI.
"""

import readline
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text

from . import __version__
from .parser import ClaudeMarkdownParser
from .prompt_builder import PromptBuilder
from .config import ConfigManager
from .claude_integration import run_claude_code, check_claude_available, enrich_prompt
from .utils import format_file_size, ensure_directory, get_next_prompt_number


class GuruREPL:
    """
    Interactive REPL for Guru CLI.

    Commands:
    - /reload     - Re-read CLAUDE.md
    - /history    - Show query history
    - /template   - Switch or list templates
    - /profile    - Load or list profiles
    - /run        - Send last prompt to Claude Code
    - /smart      - Re-generate last query with AI enrichment
    - /help       - Show help
    - /exit       - Exit
    """

    def __init__(
        self,
        console: Console,
        parser: ClaudeMarkdownParser,
        builder: PromptBuilder,
        config: ConfigManager,
        prompts_dir: Optional[Path] = None,
    ):
        """
        Initialize the REPL.

        Args:
            console: Rich console for output
            parser: CLAUDE.md parser
            builder: Prompt builder
            config: Configuration manager
            prompts_dir: Directory for saving prompts
        """
        self.console = console
        self.parser = parser
        self.builder = builder
        self.config = config
        self.prompts_dir = prompts_dir or Path.cwd() / "prompts"

        self.history: List[str] = []
        self.last_prompt_content: Optional[str] = None
        self.last_prompt_path: Optional[Path] = None
        self.last_query: Optional[str] = None
        self.running = False

        # Command handlers
        self.commands: Dict[str, Callable[[str], None]] = {
            "/reload": self._cmd_reload,
            "/history": self._cmd_history,
            "/template": self._cmd_template,
            "/profile": self._cmd_profile,
            "/run": self._cmd_run,
            "/smart": self._cmd_smart,
            "/file": self._cmd_file,
            "/help": self._cmd_help,
            "/exit": self._cmd_exit,
            "/quit": self._cmd_exit,
        }

        # Setup readline for history
        self._setup_readline()

    def _setup_readline(self) -> None:
        """Configure readline for command history and completion."""
        # Enable tab completion
        readline.set_completer(self._completer)
        readline.parse_and_bind("tab: complete")

        # Set history file
        history_file = Path.home() / ".guru_history"
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass

        # Save history on exit
        import atexit
        atexit.register(readline.write_history_file, history_file)

    def _completer(self, text: str, state: int) -> Optional[str]:
        """Readline completer for commands."""
        if text.startswith("/"):
            options = [cmd for cmd in self.commands.keys() if cmd.startswith(text)]
            if state < len(options):
                return options[state]
        return None

    def show_welcome(self) -> None:
        """Display the welcome message."""
        summary = self.parser.get_summary()
        file_size = format_file_size(summary["file_size"])
        sections = summary["sections_found"]

        welcome_text = Text()
        welcome_text.append("Guru ", style="bold magenta")
        welcome_text.append(f"v{__version__}", style="dim")
        welcome_text.append(" | CLAUDE.md loaded ", style="")
        welcome_text.append(f"({file_size}, {sections} sections)", style="dim cyan")

        self.console.print()
        self.console.print(Panel(welcome_text, border_style="cyan", padding=(0, 1)))
        self.console.print("[dim]Type your query or /help for commands[/dim]")
        self.console.print()

    def run(self) -> None:
        """Run the REPL loop."""
        self.running = True
        self.show_welcome()

        while self.running:
            try:
                # Get input with colored prompt
                user_input = Prompt.ask("[bold cyan]guru[/bold cyan]")
                user_input = user_input.strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                else:
                    self._process_query(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[dim]Use /exit to quit[/dim]")
            except EOFError:
                self._cmd_exit("")
                break

    def _handle_command(self, input_text: str) -> None:
        """Handle a slash command."""
        parts = input_text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command in self.commands:
            self.commands[command](args)
        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("[dim]Type /help for available commands[/dim]")

    def _process_query(self, query: str) -> None:
        """Process a user query using smart mode (Claude API) by default."""
        # Add to history
        self.history.append(query)
        self.last_query = query
        if len(self.history) > 100:  # Keep last 100 queries
            self.history = self.history[-100:]

        # Use smart mode by default
        if check_claude_available():
            self.console.print("[blue]Generating prompt via Claude Code...[/blue]")
            try:
                with self.console.status("[blue]Analyzing query...[/blue]", spinner="dots"):
                    result = enrich_prompt(query, self.parser.extract_context())

                if result.success and result.output:
                    ensure_directory(self.prompts_dir)
                    number = get_next_prompt_number(self.prompts_dir)
                    filename = f"prompt_{number:02d}.md"
                    filepath = self.prompts_dir / filename
                    filepath.write_text(result.output, encoding="utf-8")

                    self.last_prompt_content = result.output
                    self.last_prompt_path = filepath

                    self.console.print(f"[green]Saved:[/green] {filepath}")
                    return
                else:
                    self.console.print(f"[yellow]Smart mode failed:[/yellow] {result.error}")
                    self.console.print("[dim]Falling back to local template...[/dim]")
            except Exception as e:
                self.console.print(f"[yellow]Smart mode error:[/yellow] {e}")
                self.console.print("[dim]Falling back to local template...[/dim]")

        # Fallback: local template
        try:
            claude_md_data = self.parser.get_all_sections()
            claude_md_data["relevant_context"] = self.parser.get_relevant_sections(query)

            content, filepath = self.builder.build_and_save(
                query, claude_md_data, self.prompts_dir
            )

            self.last_prompt_content = content
            self.last_prompt_path = filepath

            self.console.print(f"[green]Saved:[/green] {filepath}")

        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")

    # --- Command Handlers ---

    def _cmd_reload(self, args: str) -> None:
        """Reload CLAUDE.md from disk."""
        try:
            self.parser.reload()
            summary = self.parser.get_summary()
            file_size = format_file_size(summary["file_size"])
            self.console.print(f"[green]Reloaded:[/green] CLAUDE.md ({file_size})")
        except Exception as e:
            self.console.print(f"[red]Error reloading:[/red] {e}")

    def _cmd_history(self, args: str) -> None:
        """Show query history."""
        if not self.history:
            self.console.print("[dim]No history yet[/dim]")
            return

        # Show last 10 entries
        recent = self.history[-10:]

        table = Table(title="Recent Queries", show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=4)
        table.add_column("Query")

        start_idx = len(self.history) - len(recent) + 1
        for i, query in enumerate(recent, start=start_idx):
            # Truncate long queries
            display = query if len(query) <= 60 else query[:57] + "..."
            table.add_row(str(i), display)

        self.console.print(table)

    def _cmd_template(self, args: str) -> None:
        """Switch or list templates."""
        if not args:
            # List available templates
            templates = self.config.list_templates()
            if not templates:
                self.console.print("[dim]No custom templates found[/dim]")
                self.console.print(f"[dim]Add templates to: {self.config.templates_dir}[/dim]")
            else:
                self.console.print("[bold]Available templates:[/bold]")
                for t in templates:
                    self.console.print(f"  - {t}")

            current = "default" if not self.builder.template_path else self.builder.template_path.stem
            self.console.print(f"\n[dim]Current: {current}[/dim]")
            return

        # Switch template
        template_name = args.strip()

        if template_name == "default":
            self.builder.template_path = None
            self.builder._load_template()
            self.console.print("[green]Switched to default template[/green]")
            return

        template_path = self.config.get_template_path(template_name)
        if template_path:
            self.builder.set_template(template_path)
            self.console.print(f"[green]Switched to template:[/green] {template_name}")
        else:
            self.console.print(f"[red]Template not found:[/red] {template_name}")

    def _cmd_profile(self, args: str) -> None:
        """Load or list profiles."""
        if not args:
            # List available profiles
            profiles = self.config.list_profiles()
            if not profiles:
                self.console.print("[dim]No profiles found[/dim]")
                self.console.print(f"[dim]Add profiles to: {self.config.profiles_dir}[/dim]")
            else:
                self.console.print("[bold]Available profiles:[/bold]")
                for p in profiles:
                    self.console.print(f"  - {p}")
            return

        # Load profile
        profile_name = args.strip()
        profile = self.config.load_profile(profile_name)

        if not profile:
            self.console.print(f"[red]Profile not found:[/red] {profile_name}")
            return

        # Apply profile settings
        try:
            # Update CLAUDE.md path
            claude_path = Path(profile.get("claude_md_path", "./CLAUDE.md"))
            if not claude_path.is_absolute():
                claude_path = Path.cwd() / claude_path

            if claude_path.exists():
                self.parser.load(claude_path)
                self.console.print(f"[green]Loaded CLAUDE.md:[/green] {claude_path}")
            else:
                self.console.print(f"[yellow]Warning:[/yellow] CLAUDE.md not found at {claude_path}")

            # Update template
            template = profile.get("template", "default")
            if template != "default":
                template_path = self.config.get_template_path(template)
                if template_path:
                    self.builder.set_template(template_path)

            # Update prompts directory
            prompts_dir = profile.get("prompts_dir", "./prompts")
            self.prompts_dir = Path(prompts_dir)
            if not self.prompts_dir.is_absolute():
                self.prompts_dir = Path.cwd() / self.prompts_dir

            self.console.print(f"[green]Profile loaded:[/green] {profile_name}")

        except Exception as e:
            self.console.print(f"[red]Error loading profile:[/red] {e}")

    def _cmd_run(self, args: str) -> None:
        """Send last prompt to Claude Code."""
        if not self.last_prompt_content:
            self.console.print("[yellow]No prompt to run.[/yellow] Make a query first.")
            return

        if not check_claude_available():
            self.console.print("[red]Claude Code CLI not found.[/red]")
            self.console.print("[dim]Install it from: https://claude.ai/code[/dim]")
            return

        self.console.print("[blue]Sending to Claude Code...[/blue]")

        try:
            with self.console.status("[blue]Running...[/blue]", spinner="dots"):
                result = run_claude_code(self.last_prompt_content)

            if result.success:
                self.console.print(Panel(
                    result.output,
                    title="Claude Response",
                    border_style="green"
                ))
            else:
                self.console.print(f"[red]Error:[/red] {result.error}")

        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")

    def _cmd_smart(self, args: str) -> None:
        """Re-generate last query with AI enrichment via Claude Code CLI."""
        query = args.strip() if args.strip() else self.last_query

        if not query:
            self.console.print("[yellow]No query to enrich.[/yellow] Make a query first or provide one: /smart <query>")
            return

        if not check_claude_available():
            self.console.print("[red]Claude Code CLI not found.[/red]")
            self.console.print("[dim]Install from: https://claude.ai/code[/dim]")
            return

        self.console.print("[blue]Smart mode: enriching prompt via Claude Code...[/blue]")

        try:
            with self.console.status("[blue]Analyzing query...[/blue]", spinner="dots"):
                result = enrich_prompt(query, self.parser.extract_context())

            if result.success and result.output:
                # Save the enriched prompt
                ensure_directory(self.prompts_dir)
                number = get_next_prompt_number(self.prompts_dir)
                filename = f"prompt_{number:02d}.md"
                filepath = self.prompts_dir / filename
                filepath.write_text(result.output, encoding="utf-8")

                self.last_prompt_content = result.output
                self.last_prompt_path = filepath
                self.last_query = query

                # Add to history if new query
                if not args.strip():
                    pass  # Already in history from original query
                else:
                    self.history.append(query)

                self.console.print(f"[green]Saved (smart):[/green] {filepath}")
            else:
                self.console.print(f"[yellow]Smart mode failed:[/yellow] {result.error}")
                self.console.print("[dim]Use regular query instead.[/dim]")

        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")

    def _cmd_file(self, args: str) -> None:
        """Read query from file and process it."""
        if not args.strip():
            self.console.print("[yellow]Usage:[/yellow] /file <path>")
            self.console.print("[dim]Reads content from file and processes it as a query.[/dim]")
            return

        file_path = Path(args.strip())
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path

        if not file_path.exists():
            self.console.print(f"[red]File not found:[/red] {file_path}")
            return

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.console.print(f"[red]Error reading file:[/red] {e}")
            return

        self.console.print(f"[dim]Read {len(content)} chars from {file_path.name}[/dim]")
        self._process_query(content)

    def _cmd_help(self, args: str) -> None:
        """Show help information."""
        help_text = """
[bold]Commands:[/bold]
  [cyan]/reload[/cyan]          Re-read CLAUDE.md from disk
  [cyan]/history[/cyan]         Show recent query history
  [cyan]/template[/cyan] [name] Switch template (no arg = list)
  [cyan]/profile[/cyan] [name]  Load profile (no arg = list)
  [cyan]/run[/cyan]             Send last prompt to Claude Code
  [cyan]/smart[/cyan] [query]   Enrich prompt via Claude Code AI
  [cyan]/file[/cyan] <path>     Read query from file
  [cyan]/help[/cyan]            Show this help
  [cyan]/exit[/cyan]            Exit Guru

[bold]Usage:[/bold]
  Type any query to generate a structured prompt.
  Use [cyan]/smart[/cyan] after a query to re-generate it with AI analysis.
  Use [cyan]--smart[/cyan] flag in CLI mode: [dim]guru --smart "your query"[/dim]
  Prompts are saved to ./prompts/ with auto-incrementing names.
"""
        self.console.print(Panel(help_text.strip(), title="Guru Help", border_style="cyan"))

    def _cmd_exit(self, args: str) -> None:
        """Exit the REPL."""
        self.console.print("[dim]Goodbye![/dim]")
        self.running = False
