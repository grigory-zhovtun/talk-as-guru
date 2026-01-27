# Guru

CLI utility for analyzing CLAUDE.md files and generating structured prompts for Claude Code.

Guru reads your project's CLAUDE.md file and uses it to generate context-aware prompts that include role detection, relevant context filtering, tech stack, coding conventions, and project constraints.

## Installation

```bash
# From PyPI (when published)
pip install talk-as-guru

# From source
git clone https://github.com/grigory-zhovtun/talk-as-guru.git
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
guru "create a REST API endpoint for user authentication"
```

3. Result — a structured prompt in `./prompts/prompt_01.md`:

```markdown
# Роль
Senior Backend разработчик (FastAPI, Python, PostgreSQL)

# Задача
create a REST API endpoint for user authentication

# Техническое окружение
- Python 3.11
- FastAPI
- PostgreSQL

# Релевантный контекст
[Only relevant sections from CLAUDE.md]

# Конвенции
- Use type hints everywhere
- Follow PEP 8 style guide

# Ограничения и правила
- Never commit secrets
- Always write tests for new features
```

## Two Modes

### Standard Mode (default)

Generates a prompt locally using a template with:
- **Automatic role detection** — determines the role from query keywords and tech stack (e.g. "Senior Frontend разработчик (Next.js, React, TypeScript)")
- **Relevant context filtering** — includes only project-specific sections from CLAUDE.md, sorted by relevance to the query
- **Structured output** — role, task, tech environment, context, conventions, constraints

```bash
guru "add a notification bell to the header"
```

### Smart Mode (`--smart`)

Uses Claude Code CLI to analyze the query and generate an enriched prompt with:
- **AI-powered role selection** — specific specialization for the task
- **Task decomposition** — 3-7 concrete subtasks with details
- **Intelligent context filtering** — only the most relevant parts of CLAUDE.md
- **Technical constraints** — derived from project architecture

```bash
guru --smart "add a notification bell to the header"
```

Requires Claude Code CLI installed (`claude` command in PATH).

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
guru --smart / -s              Enrich prompt via Claude Code AI
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
| `/smart [query]` | Enrich prompt via Claude Code AI |
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
- Automatically detected role
- Your query/task
- Tech stack from CLAUDE.md
- Relevant project context (filtered, not full dump)
- Project conventions
- Constraints and rules

## Templates

Guru uses Jinja2 templates for prompt generation.

### Available Template Variables

| Variable | Description |
|----------|-------------|
| `user_query` | The user's query/task |
| `role` | Auto-detected role |
| `tech_stack` | Tech stack section |
| `relevant_context` | Filtered relevant sections |
| `conventions` | Conventions section |
| `constraints` | Constraints/rules section |
| `context` | Full file content (legacy) |

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

## Claude Code Integration

### `/run` — Execute prompt

Send the last generated prompt to Claude Code CLI:

```
guru> create a user model
Saved: ./prompts/prompt_01.md

guru> /run
Sending to Claude Code...
[Claude's response appears here]
```

### `/smart` — AI-enriched prompts

Re-generate the last query with AI analysis:

```
guru> add notifications to the header
Saved: ./prompts/prompt_01.md

guru> /smart
Smart mode: enriching prompt via Claude Code...
Saved (smart): ./prompts/prompt_02.md
```

Or provide a new query directly:

```
guru> /smart add API endpoint for notifications
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

All other sections are treated as project context and included based on relevance to the query.

Supported heading formats:

```markdown
# Heading
## Heading
**Heading**
```

## Role Detection

Guru automatically detects the appropriate role based on query keywords and tech stack:

| Keywords | Role |
|----------|------|
| react, next.js, frontend, css, ui, компонент | Senior Frontend разработчик |
| python, fastapi, backend, api, endpoint | Senior Backend разработчик |
| sql, postgres, database, модел | Senior Database разработчик |
| docker, kubernetes, deploy, devops | Senior DevOps инженер |
| test, pytest, jest, e2e | Senior QA инженер |
| security, auth, jwt, oauth | Senior Security инженер |
| go, golang, goroutine | Senior Go разработчик |

The role is enhanced with specific technologies from the project's tech stack (e.g. "Senior Frontend разработчик (Next.js, React, TypeScript)").

## Examples

### Basic Workflow

```bash
# Navigate to your project
cd my-project

# Generate a prompt
guru "implement user authentication with JWT"
# Saved: ./prompts/prompt_01.md

# Generate an AI-enriched prompt
guru --smart "add rate limiting to the API"
# Saved (smart): ./prompts/prompt_02.md
```

### REPL Workflow

```bash
guru

guru> implement user authentication with JWT
Saved: ./prompts/prompt_01.md

guru> /smart
Smart mode: enriching prompt via Claude Code...
Saved (smart): ./prompts/prompt_02.md

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
