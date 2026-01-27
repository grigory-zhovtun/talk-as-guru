# Guru

CLI utility for analyzing CLAUDE.md files and generating structured prompts for Claude Code.

Guru reads your project's CLAUDE.md file and uses it to generate context-aware prompts that include your tech stack, coding conventions, and project constraints.

## Installation

```bash
# From PyPI (when published)
pip install talk-as-guru

# From source
git clone https://github.com/grigoriizhovtun/talk-as-guru.git
cd talk-as-guru
pip install -e .
```

## Quick Start

1. Create a `CLAUDE.md` file in your project root:

```markdown
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
- Always write tests for new features
```

2. Run Guru:

```bash
guru
```

3. Enter your query:

```
guru> create a REST API endpoint for user authentication
Saved: ./prompts/prompt_01.md
```

## Usage

### Interactive REPL Mode

Start the interactive shell:

```bash
guru
```

### Single Query Mode

Process a query without entering the REPL:

```bash
guru "create a function for email validation"
```

### Command Line Options

```
guru --help                    Show help
guru --version                 Show version
guru -c /path/to/CLAUDE.md     Use specific CLAUDE.md file
guru -p ./my-prompts           Save prompts to custom directory
guru -t custom                 Use a custom template
guru --profile my-project      Load a saved profile
```

## REPL Commands

| Command | Description |
|---------|-------------|
| `/reload` | Re-read CLAUDE.md from disk |
| `/history` | Show recent query history |
| `/template [name]` | Switch template (no arg = list available) |
| `/profile [name]` | Load profile (no arg = list available) |
| `/run` | Send last prompt to Claude Code CLI |
| `/help` | Show help |
| `/exit` | Exit Guru |

## Generated Prompts

Prompts are saved to `./prompts/` with auto-incrementing filenames:

```
prompts/
├── prompt_01.md
├── prompt_02.md
└── prompt_03.md
```

Each prompt includes:
- Your query/task
- Tech stack from CLAUDE.md
- Project conventions
- Constraints and rules
- Full project context

## Templates

Guru uses Jinja2 templates for prompt generation.

### Custom Templates

Create custom templates in `~/.guru/templates/`:

```bash
mkdir -p ~/.guru/templates
```

Example template (`~/.guru/templates/detailed.md.j2`):

```jinja2
# Task Description
{{ user_query }}

## Technical Context
### Tech Stack
{{ tech_stack }}

### Coding Standards
{{ conventions }}

### Important Rules
{{ constraints }}

## Full Project Context
{{ context }}
```

Use it with:

```bash
guru -t detailed
# or in REPL
guru> /template detailed
```

## Profiles

Save project configurations as profiles in `~/.guru/profiles/`:

```yaml
# ~/.guru/profiles/my-project.yaml
name: my-project
claude_md_path: ./docs/CLAUDE.md
template: detailed
prompts_dir: ./generated-prompts
```

Load with:

```bash
guru --profile my-project
# or in REPL
guru> /profile my-project
```

## Claude Code Integration

The `/run` command sends your last prompt to Claude Code CLI:

```
guru> create a user model
Saved: ./prompts/prompt_01.md

guru> /run
Sending to Claude Code...
[Claude's response appears here]
```

Requirements:
- Claude Code CLI must be installed and in your PATH
- Install from: https://claude.ai/code

## CLAUDE.md Format

Guru recognizes sections based on keywords in headings:

| Section | Keywords |
|---------|----------|
| Tech Stack | tech, stack, technology, tools, dependencies |
| Conventions | convention, style, formatting, patterns, practices |
| Constraints | constraint, rule, restriction, important, warning |

Supported heading formats:

```markdown
# Heading
## Heading
**Heading**
```

If no sections are recognized, the entire file is used as context.

## Examples

### Basic Workflow

```bash
# Navigate to your project
cd my-project

# Ensure CLAUDE.md exists
cat CLAUDE.md

# Start Guru
guru

# Generate prompts
guru> implement user authentication with JWT
Saved: ./prompts/prompt_01.md

guru> add rate limiting to the API
Saved: ./prompts/prompt_02.md

# Review history
guru> /history

# Exit
guru> /exit
```

### Using with Claude Code

```bash
guru "refactor the database module"
# Opens ./prompts/prompt_01.md
# Copy content to Claude Code or use /run command
```

## Configuration Directory

Guru stores configuration in `~/.guru/`:

```
~/.guru/
├── templates/      # Custom Jinja2 templates
│   └── custom.md.j2
└── profiles/       # Project profiles
    └── my-project.yaml
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Lint
ruff src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
