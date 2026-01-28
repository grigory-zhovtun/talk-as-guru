# Guru

CLI utility for analyzing CLAUDE.md files and generating structured prompts for Claude Code.

Guru reads your project's CLAUDE.md file and uses Claude Code CLI to generate context-aware, AI-enriched prompts with role detection, task decomposition, relevant context filtering, and technical constraints.

## Installation

```bash
# From PyPI
pip install talk-as-guru

# From source
git clone https://github.com/grigory-zhovtun/talk-as-guru.git
cd talk-as-guru
pip install -e .
```

## Prerequisites

Guru uses [Claude Code CLI](https://claude.ai/code) to generate prompts. Make sure the `claude` command is available in your PATH.

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
guru "create a REST API endpoint for user authentication"
```

3. Result — an AI-enriched structured prompt saved to `./prompts/prompt_01.md`:

```markdown
# Enriched Prompt

## Role
Senior Python/FastAPI developer specializing in async API
and authentication systems with SQLAlchemy and PostgreSQL experience.

## Task
Implement a REST API endpoint for user authentication
with JWT token support.

## Subtasks
1. Analyze existing auth models and endpoints
2. Define Pydantic response schemas
3. Implement POST /api/auth/login endpoint
4. Add input validation
5. Write unit tests

## Relevant Context
- Backend: FastAPI + SQLAlchemy async + PostgreSQL
- Existing files: routes/auth.py, db/models/user.py

## Constraints
- Use async/await for all DB operations
- Validate all user input
- Never hardcode secrets
```

## How It Works

Guru sends your query along with the parsed CLAUDE.md content to Claude Code CLI, which analyzes the task and generates a structured prompt with:

- **AI-powered role selection** — specific specialization for the task
- **Task decomposition** — 3-7 concrete subtasks with details
- **Intelligent context filtering** — only the most relevant parts of CLAUDE.md
- **Technical constraints** — derived from project architecture

If Claude Code CLI is unavailable, Guru falls back to a local template-based mode with automatic role detection and keyword-based context filtering.

## Usage

### Single Query Mode

```bash
guru "create a function for email validation"
```

### Interactive REPL Mode

```bash
guru
```

### Disable AI Enrichment

Use `--no-smart` to generate prompts using local templates only (no Claude Code CLI):

```bash
guru --no-smart "create a function for email validation"
```

### Read Query from File

Use `--file / -f` to read query content from a file (useful for multi-line specs with special characters):

```bash
guru -f spec.md                    # Read query from file
guru -f spec.md "additional context"  # File content + extra text
```

### Command Line Options

```
guru --help                    Show help
guru --version                 Show version
guru --file / -f <path>        Read query from file
guru --no-smart / -S           Use local template instead of Claude Code AI
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
| `/file <path>` | Read query from file and process it |
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

## Templates

Guru uses Jinja2 templates for the local fallback mode.

### Available Template Variables

| Variable | Description |
|----------|-------------|
| `user_query` | The user's query/task |
| `role` | Auto-detected role |
| `tech_stack` | Tech stack section |
| `relevant_context` | Filtered relevant sections |
| `conventions` | Conventions section |
| `constraints` | Constraints/rules section |

### Custom Templates

Create custom templates in `~/.guru/templates/`:

```bash
mkdir -p ~/.guru/templates
```

Example template (`~/.guru/templates/detailed.md.j2`):

```jinja2
# Role
{{ role }}

# Task Description
{{ user_query }}

## Technical Context
### Tech Stack
{{ tech_stack }}

### Relevant Context
{{ relevant_context }}

### Coding Standards
{{ conventions }}

### Important Rules
{{ constraints }}
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

## CLAUDE.md Format

Guru recognizes sections based on keywords in headings:

| Section | Keywords |
|---------|----------|
| Tech Stack | tech, stack, technology, tools, dependencies |
| Conventions | convention, style, formatting, patterns, practices |
| Constraints | constraint, rule, restriction, important, warning |

All other sections are treated as project context and included based on relevance to the query.

Supported heading formats:

```markdown
# Heading
## Heading
**Heading**
```

## Examples

### Basic Workflow

```bash
# Navigate to your project
cd my-project

# Generate an AI-enriched prompt (default)
guru "implement user authentication with JWT"
# Saved: ./prompts/prompt_01.md

# Generate a local template prompt (no AI)
guru --no-smart "add rate limiting to the API"
# Saved: ./prompts/prompt_02.md
```

### REPL Workflow

```bash
guru

guru> implement user authentication with JWT
Generating prompt via Claude Code...
Saved: ./prompts/prompt_01.md

guru> /run
Sending to Claude Code...

guru> /history
guru> /exit
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
