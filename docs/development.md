---
title: Development Guide
---

# Development Guide

Welcome to the mdxlate development guide! This document helps you understand the project structure, set up your development environment, and contribute to mdxlate.

## Project Overview

mdxlate is a Python-based tool for translating Markdown documentation using Large Language Models (LLMs). It provides both a CLI and programmatic API.

### Key Features

- ✅ CLI and programmatic Python API
- ✅ OpenAI and OpenRouter provider support
- ✅ Smart caching to avoid re-translation
- ✅ Concurrent translation processing
- ✅ YAML frontmatter preservation (Jekyll, Hugo, etc.)
- ✅ Error handling and failure reporting
- ✅ Customizable translation prompts

## Repository Structure

```
markdown-automatic-translation/
├── src/
│   └── mdxlate/
│       ├── __init__.py              # Package initialization
│       ├── cli.py                   # Typer CLI (mdx init, mdx run)
│       ├── client.py                # API client factory (OpenAI/OpenRouter)
│       ├── translator.py            # Core translation logic
│       ├── start_translation.py     # Main programmatic entry point
│       ├── cache.py                 # Translation cache implementation
│       └── translation_instruction.txt  # Default prompt template
├── tests/
│   ├── test_cli.py                  # CLI tests
│   ├── test_mdxlate.py              # Core functionality tests
│   ├── test_cache.py                # Cache system tests
│   └── test_client.py               # Client tests
├── docs/
│   ├── index.md                     # Documentation home
│   ├── cli.md                       # CLI reference
│   ├── programmatic.md              # Programmatic usage
│   ├── caching.md                   # Cache documentation
│   ├── custom-prompt.md             # Prompt customization
│   ├── error-handling.md            # Error handling guide
│   ├── development.md               # This file
│   ├── faq.md                       # FAQ / Troubleshooting
│   └── integrations/
│       └── jekyll.md                # Jekyll integration guide
├── pyproject.toml                   # Project configuration
├── README.md                        # Main project README
└── _config.yml                      # Jekyll documentation config

```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip or uv for package management
- Git

### Clone the Repository

```bash
git clone https://github.com/Softoft-Orga/markdown-automatic-translation.git
cd markdown-automatic-translation
```

### Install Dependencies

#### Using pip

```bash
pip install -e .
```

#### Using uv (recommended for development)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install package in editable mode
uv pip install -e .
```

### Verify Installation

```bash
mdx --help
```

Expected output:
```
Usage: mdx [OPTIONS] COMMAND [ARGS]...

Commands:
  init  Initialize editable translation prompt file.
  run   Run translation...
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

Edit source files in `src/mdxlate/`

### 3. Run Tests

```bash
pytest tests/
```

### 4. Run Linter

```bash
# Using ruff (if available)
ruff check src/ tests/

# Or use flake8/black
flake8 src/ tests/
black src/ tests/
```

### 5. Test CLI Manually

```bash
# Test init command
mdx init --prompt-path /tmp/test-prompt.txt

# Test run command
mdx run data/test-markdown/en output --languages de --model gpt-4o-mini
```

### 6. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

### 7. Push and Create PR

```bash
git push origin feature/my-feature
# Create pull request on GitHub
```

## Key Components

### CLI (`cli.py`)

Entry point for the command-line interface using Typer.

**Commands:**
- `mdx init` - Initialize translation prompt
- `mdx run` - Run translation

**Key code:**
```python
import typer

app = typer.Typer(add_completion=False)

@app.command()
def init(prompt_path: Path = ...):
    """Initialize editable translation prompt file."""
    # Implementation

@app.command()
def run(docs_src: Path, out_dir: Path, ...):
    """Run translation."""
    # Implementation
```

### Client (`client.py`)

API client factory for OpenAI and OpenRouter.

**Key code:**
```python
from openai import AsyncOpenAI

def make_client(
    provider: Provider,
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncOpenAI:
    # Returns configured client
```

### Translator (`translator.py`)

Core translation logic with caching and error handling.

**Key classes:**
- `Translator` - Main translation orchestrator

**Key methods:**
- `translate_text()` - Translate single text with retry logic
- `translate_directory()` - Translate entire directory
- `process_file()` - Process single file with caching
- `clean_up_unused_files()` - Remove stale translations

**Key code:**
```python
class Translator:
    async def translate_directory(self, source_dir: Path, output_dir: Path):
        # Load cache, translate files, save cache
    
    @tenacity.retry(...)
    async def translate_text(self, content: str, target_language: str) -> str:
        # Call LLM with retry logic
```

### Cache (`cache.py`)

Translation cache for avoiding re-translation.

**Key class:**
- `TranslationCache` - Manages cache state

**Key methods:**
- `calc_key()` - Calculate cache key from file + settings
- `is_up_to_date()` - Check if translation is cached
- `mark()` - Mark translation as complete

**Key code:**
```python
class TranslationCache:
    def calc_key(self, rel: Path, lang: str, file_bytes: bytes, 
                 prompt: str, model: str) -> str:
        # Returns unique hash
    
    def is_up_to_date(self, rel: Path, lang: str, key: str) -> bool:
        # Check cache hit
```

### Start Translation (`start_translation.py`)

Programmatic entry point.

**Key function:**
```python
def start_translation(
    docs_src: Path,
    out_dir: Path,
    base_language: str,
    languages: list[str],
    model: str = "gpt-4o-mini",
    provider: Provider = "openai",
    ...
) -> None:
    # Create client and translator, run translation
```

## Testing

### Test Structure

```
tests/
├── test_cli.py          # CLI command tests
├── test_mdxlate.py      # Core translation tests
├── test_cache.py        # Cache functionality tests
└── test_client.py       # Client creation tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cli.py

# Run specific test
pytest tests/test_cli.py::test_init_creates_default_prompt_file

# Run with coverage
pytest --cov=mdxlate tests/

# Run with verbose output
pytest -v
```

### Writing Tests

Example test:

```python
def test_translate_directory_writes_expected_files(sample_docs):
    src, out = sample_docs
    
    translator = Translator(
        client=None,  # Mock client
        base_language="en",
        languages=["de", "fr"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )
    
    # Mock translate method
    async def fake_translate(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] {content}"
    
    translator.translate_text = fake_translate.__get__(translator, Translator)
    
    # Run translation
    asyncio.run(translator.translate_directory(src, out))
    
    # Assert files created
    assert (out / "de" / "a.md").exists()
    assert (out / "fr" / "a.md").exists()
```

### Test Fixtures

```python
@pytest.fixture
def sample_docs(tmp_path: Path):
    """Create sample documentation structure."""
    src = tmp_path / "src"
    out = tmp_path / "out"
    
    src.mkdir()
    (src / "a.md").write_text("# Hello", encoding="utf-8")
    (src / "b.md").write_text("# World", encoding="utf-8")
    
    return src, out
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Max line length: 120 characters
- Use f-strings for formatting

### Naming Conventions

- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Type Hints

```python
from pathlib import Path

def translate_file(
    source: Path,
    target_lang: str,
    model: str = "gpt-4o-mini"
) -> str:
    """Translate a file to target language."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def process_file(file_path: Path, output_dir: Path) -> None:
    """Process a single file for translation.
    
    Args:
        file_path: Path to the source file
        output_dir: Directory for translated output
        
    Raises:
        ValueError: If file_path does not exist
        IOError: If output cannot be written
    """
    ...
```

## Adding New Features

### Example: Add New Provider

1. **Update `client.py`:**

```python
from typing import Literal

Provider = Literal["openai", "openrouter", "anthropic"]  # Add anthropic

def make_client(
    provider: Provider,
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncOpenAI:
    if provider == "anthropic":
        return AsyncOpenAI(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            base_url=base_url or "https://api.anthropic.com/v1",
        )
    # ... rest of code
```

2. **Update CLI in `cli.py`:**

```python
@app.command()
def run(
    # ...
    provider: Provider = typer.Option("openai"),  # Will include anthropic
    # ...
):
    ...
```

3. **Add tests:**

```python
def test_anthropic_provider():
    client = make_client(provider="anthropic", api_key="test-key")
    assert client.api_key == "test-key"
```

4. **Update documentation:**
- Add to [CLI Reference](cli.md)
- Update [Programmatic Usage](programmatic.md)
- Add example to README.md

## Debugging

### Debug CLI Commands

```bash
# Run with Python debugger
python -m pdb -m mdxlate.cli run docs output --languages de
```

### Debug in IDE

**VS Code `launch.json`:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug mdx run",
            "type": "python",
            "request": "launch",
            "module": "mdxlate.cli",
            "args": ["run", "docs", "output", "--languages", "de"],
            "env": {
                "OPENAI_API_KEY": "sk-..."
            }
        }
    ]
}
```

### Logging

Add logging to debug issues:

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
```

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Release Process

### Version Numbering

Use semantic versioning (SemVer): `MAJOR.MINOR.PATCH`

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Creating a Release

1. **Update version in `pyproject.toml`:**

```toml
[project]
name = "mdxlate"
version = "0.2.0"  # Update this
```

2. **Update CHANGELOG:**

Create or update `CHANGELOG.md`:

```markdown
## [0.2.0] - 2024-01-15

### Added
- Support for Anthropic provider
- Batch translation mode

### Fixed
- Cache invalidation bug
- Unicode handling in filenames
```

3. **Create Git tag:**

```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

4. **Build and publish (maintainers only):**

```bash
# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Contributing Guidelines

### Before You Start

- Check existing issues and PRs
- Discuss major changes in an issue first
- Follow the code style guide
- Write tests for new features

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Update documentation
6. Ensure tests pass
7. Submit PR with clear description

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] All tests pass
```

### Code Review

- Be respectful and constructive
- Address all review comments
- Keep PRs focused and small
- Update PR based on feedback

## Common Development Tasks

### Add a New CLI Option

1. Update `cli.py`:
```python
@app.command()
def run(
    # ... existing options ...
    new_option: str = typer.Option("default", help="New option description"),
):
    # Use new_option
```

2. Update `start_translation.py` if needed
3. Add tests in `test_cli.py`
4. Update [CLI Reference](cli.md)

### Modify Translation Logic

1. Update `translator.py`
2. Add tests in `test_mdxlate.py`
3. Verify with integration test
4. Update relevant documentation

### Update Default Prompt

1. Edit `src/mdxlate/translation_instruction.txt`
2. Test with various markdown files
3. Update [Custom Prompt](custom-prompt.md) with examples

### Add Integration Guide

1. Create `docs/integrations/[framework].md`
2. Follow structure of `jekyll.md`
3. Include working examples
4. Link from main documentation

## Resources

### Internal Resources

- [Architecture Decision Records](https://github.com/Softoft-Orga/markdown-automatic-translation/tree/main/docs/adr) (if exists)
- [Issue Tracker](https://github.com/Softoft-Orga/markdown-automatic-translation/issues)
- [Discussions](https://github.com/Softoft-Orga/markdown-automatic-translation/discussions)

### External Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Tenacity (Retry) Documentation](https://tenacity.readthedocs.io/)
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html)

## Getting Help

- **Issues:** Report bugs or request features on GitHub Issues
- **Discussions:** Ask questions on GitHub Discussions  
- **Email:** Contact maintainers (check README)
- **Documentation:** Read the [full documentation](index.md)

## License

mdxlate is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

Thank you to all contributors who help make mdxlate better!

---

Ready to contribute? Start by [forking the repository](https://github.com/Softoft-Orga/markdown-automatic-translation/fork) and exploring the code!
