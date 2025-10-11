---
title: Programmatic Usage
---

# Programmatic Usage

mdxlate can be used as a Python library for integration into your applications, scripts, or automation workflows.

## Quick Start

### Basic Usage

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

start_translation(
    docs_src=Path("docs_src"),
    out_dir=Path("out"),
    base_language="en",
    languages=["de", "fr"],
    model="gpt-4o-mini",
    provider="openai",
    api_key=None,  # Uses environment variable
    base_url=None,
    cache_dir=None,
)
```

## API Reference

### start_translation()

Main entry point for programmatic translation.

#### Signature

```python
def start_translation(
    docs_src: Path,
    out_dir: Path,
    base_language: str,
    languages: list[str],
    model: str = "gpt-4o-mini",
    provider: Provider = "openai",
    api_key: str | None = None,
    base_url: str | None = None,
    cache_dir: Path | None = None,
) -> None
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `docs_src` | Path | Yes | - | Source directory containing markdown files |
| `out_dir` | Path | Yes | - | Output directory for translations |
| `base_language` | str | Yes | - | Source language code (e.g., "en") |
| `languages` | list[str] | Yes | - | List of target language codes |
| `model` | str | No | `"gpt-4o-mini"` | LLM model name |
| `provider` | str | No | `"openai"` | Provider: "openai" or "openrouter" |
| `api_key` | str \| None | No | None | API key (uses env var if None) |
| `base_url` | str \| None | No | None | Custom API endpoint URL |
| `cache_dir` | Path \| None | No | None | Cache directory (defaults to source) |

#### Example

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

# Translate documentation to multiple languages
start_translation(
    docs_src=Path("./documentation"),
    out_dir=Path("./site/i18n"),
    base_language="en",
    languages=["de", "fr", "es", "ja"],
    model="gpt-4o-mini",
)
```

## Advanced Usage

### Custom Provider Configuration

#### OpenRouter

```python
import os
from pathlib import Path
from mdxlate.start_translation import start_translation

start_translation(
    docs_src=Path("docs"),
    out_dir=Path("output"),
    base_language="en",
    languages=["de", "fr"],
    model="anthropic/claude-3-opus",
    provider="openrouter",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
)
```

#### Custom Base URL

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

start_translation(
    docs_src=Path("docs"),
    out_dir=Path("output"),
    base_language="en",
    languages=["de"],
    model="gpt-4o-mini",
    provider="openai",
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
)
```

### Using the Translator Class

For more control, use the `Translator` class directly:

```python
import asyncio
from pathlib import Path
from mdxlate.client import make_client
from mdxlate.translator import Translator

def translate_with_custom_settings():
    # Create client
    client = make_client(
        provider="openai",
        api_key="sk-...",
        base_url=None
    )
    
    # Create translator with custom settings
    translator = Translator(
        client=client,
        base_language="en",
        languages=["de", "fr", "es"],
        model="gpt-4o-mini",
        translation_instruction_text="Custom translation prompt...",
        max_concurrency=16,  # Increase parallelism
        force_translation=False,
        cache_dir=Path("/tmp/cache"),
    )
    
    # Run translation
    asyncio.run(translator.translate_directory(
        source_dir=Path("docs"),
        output_dir=Path("output")
    ))

translate_with_custom_settings()
```

### Custom Translation Instruction

```python
from pathlib import Path
from mdxlate.translator import Translator
from mdxlate.client import make_client
import asyncio

# Read custom prompt from file
custom_prompt = Path("./my-prompt.txt").read_text(encoding="utf-8")

client = make_client(provider="openai", api_key="sk-...")

translator = Translator(
    client=client,
    base_language="en",
    languages=["de"],
    model="gpt-4o-mini",
    translation_instruction_text=custom_prompt,
)

asyncio.run(translator.translate_directory(
    source_dir=Path("docs"),
    output_dir=Path("output")
))
```

## Integration Examples

### Django Management Command

```python
# myapp/management/commands/translate_docs.py
from django.core.management.base import BaseCommand
from pathlib import Path
from mdxlate.start_translation import start_translation

class Command(BaseCommand):
    help = 'Translate documentation to multiple languages'

    def add_arguments(self, parser):
        parser.add_argument('--languages', nargs='+', default=['de', 'fr'])
        parser.add_argument('--model', default='gpt-4o-mini')

    def handle(self, *args, **options):
        self.stdout.write('Starting translation...')
        
        start_translation(
            docs_src=Path("docs/en"),
            out_dir=Path("docs"),
            base_language="en",
            languages=options['languages'],
            model=options['model'],
        )
        
        self.stdout.write(self.style.SUCCESS('Translation complete!'))
```

Usage:
```bash
python manage.py translate_docs --languages de fr es --model gpt-4o
```

### Flask Application

```python
from flask import Flask, request, jsonify
from pathlib import Path
from mdxlate.start_translation import start_translation
import tempfile
import shutil

app = Flask(__name__)

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploaded content
        src_dir = Path(tmpdir) / "source"
        src_dir.mkdir()
        
        for filename, content in data['files'].items():
            (src_dir / filename).write_text(content)
        
        # Translate
        out_dir = Path(tmpdir) / "output"
        start_translation(
            docs_src=src_dir,
            out_dir=out_dir,
            base_language=data['base_language'],
            languages=data['languages'],
            model=data.get('model', 'gpt-4o-mini'),
        )
        
        # Collect results
        results = {}
        for lang in data['languages']:
            lang_dir = out_dir / lang
            for file in lang_dir.rglob('*.md'):
                key = f"{lang}/{file.relative_to(lang_dir)}"
                results[key] = file.read_text()
        
        return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
```

### Celery Task

```python
from celery import shared_task
from pathlib import Path
from mdxlate.start_translation import start_translation

@shared_task
def translate_documentation(source_path, output_path, languages):
    """
    Asynchronous documentation translation task.
    """
    try:
        start_translation(
            docs_src=Path(source_path),
            out_dir=Path(output_path),
            base_language="en",
            languages=languages,
            model="gpt-4o-mini",
        )
        return {"status": "success", "languages": languages}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

Usage:
```python
from myapp.tasks import translate_documentation

# Queue translation task
result = translate_documentation.delay(
    source_path="/path/to/docs",
    output_path="/path/to/output",
    languages=["de", "fr", "es"]
)

# Check result
print(result.get())
```

### CI/CD Script

```python
#!/usr/bin/env python3
"""
Automated translation script for CI/CD pipelines.
"""
import os
import sys
from pathlib import Path
from mdxlate.start_translation import start_translation

def main():
    # Configuration from environment
    docs_src = Path(os.getenv("DOCS_SOURCE", "docs"))
    out_dir = Path(os.getenv("OUTPUT_DIR", "site/i18n"))
    languages = os.getenv("LANGUAGES", "de,fr,es").split(",")
    model = os.getenv("MODEL", "gpt-4o-mini")
    
    print(f"Translating {docs_src} to languages: {', '.join(languages)}")
    
    try:
        start_translation(
            docs_src=docs_src,
            out_dir=out_dir,
            base_language="en",
            languages=languages,
            model=model,
            cache_dir=Path("/tmp/mdxlate-cache"),
        )
        print("✓ Translation successful!")
        return 0
    except Exception as e:
        print(f"✗ Translation failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Pre-commit Hook

```python
#!/usr/bin/env python3
"""
Pre-commit hook to translate documentation.
"""
from pathlib import Path
from mdxlate.start_translation import start_translation
import subprocess

def get_modified_docs():
    """Get list of modified markdown files."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True,
        text=True
    )
    files = result.stdout.strip().split('\n')
    return [f for f in files if f.endswith('.md') and f.startswith('docs/en/')]

def main():
    modified_docs = get_modified_docs()
    
    if not modified_docs:
        return 0
    
    print(f"Translating {len(modified_docs)} modified documentation files...")
    
    start_translation(
        docs_src=Path("docs/en"),
        out_dir=Path("docs"),
        base_language="en",
        languages=["de", "fr"],
        model="gpt-4o-mini",
    )
    
    # Stage translated files
    subprocess.run(['git', 'add', 'docs/de/', 'docs/fr/'])
    
    return 0

if __name__ == "__main__":
    exit(main())
```

## Error Handling

### Basic Error Handling

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

try:
    start_translation(
        docs_src=Path("docs"),
        out_dir=Path("output"),
        base_language="en",
        languages=["de", "fr"],
    )
except Exception as e:
    print(f"Translation failed: {e}")
    # Handle error (log, retry, notify, etc.)
```

### Check for Failures

```python
from pathlib import Path
import json
from mdxlate.start_translation import start_translation

docs_src = Path("docs")

start_translation(
    docs_src=docs_src,
    out_dir=Path("output"),
    base_language="en",
    languages=["de", "fr"],
)

# Check for failure report
failure_report = docs_src / ".mdxlate.failures.json"
if failure_report.exists():
    failures = json.loads(failure_report.read_text())
    print(f"Warning: {len(failures['failures'])} files failed to translate")
    for failure in failures['failures']:
        print(f"  - {failure['file']}: {failure['error']}")
```

## Performance Tuning

### Adjust Concurrency

```python
from mdxlate.translator import Translator
from mdxlate.client import make_client
import asyncio
from pathlib import Path

client = make_client(provider="openai", api_key="sk-...")

# Increase concurrency for faster translation
translator = Translator(
    client=client,
    base_language="en",
    languages=["de", "fr", "es"],
    model="gpt-4o-mini",
    max_concurrency=20,  # Default is 8
)

asyncio.run(translator.translate_directory(
    source_dir=Path("docs"),
    output_dir=Path("output")
))
```

### Force Translation

```python
from mdxlate.translator import Translator
from mdxlate.client import make_client
import asyncio
from pathlib import Path

client = make_client(provider="openai", api_key="sk-...")

# Force re-translation (bypass cache)
translator = Translator(
    client=client,
    base_language="en",
    languages=["de"],
    model="gpt-4o-mini",
    force_translation=True,  # Ignore cache
)

asyncio.run(translator.translate_directory(
    source_dir=Path("docs"),
    output_dir=Path("output")
))
```

## Best Practices

### 1. Use Environment Variables for API Keys

```python
import os
from pathlib import Path
from mdxlate.start_translation import start_translation

start_translation(
    docs_src=Path("docs"),
    out_dir=Path("output"),
    base_language="en",
    languages=["de", "fr"],
    api_key=os.getenv("OPENAI_API_KEY"),  # Explicit env var
)
```

### 2. Validate Paths

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

docs_src = Path("docs")
out_dir = Path("output")

if not docs_src.exists():
    raise ValueError(f"Source directory does not exist: {docs_src}")

start_translation(
    docs_src=docs_src,
    out_dir=out_dir,
    base_language="en",
    languages=["de", "fr"],
)
```

### 3. Log Translation Progress

```python
import logging
from pathlib import Path
from mdxlate.start_translation import start_translation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

logger.info("Starting translation...")
start_translation(
    docs_src=Path("docs"),
    out_dir=Path("output"),
    base_language="en",
    languages=["de", "fr"],
)
logger.info("Translation complete!")
```

## Next Steps

- Learn about the [Caching System](caching.md)
- Customize the [Translation Prompt](custom-prompt.md)
- Set up [Error Handling](error-handling.md) for production
