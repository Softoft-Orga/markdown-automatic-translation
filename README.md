# mdxlate

Translate Markdown docs into multiple languages using LLMs.  
Batteries included: prompt template, CLI, OpenAI/OpenRouter provider switch, and a simple change-detection cache.

## Install
```bash
pip install -e .
````

## Quick start

1. Initialize the editable prompt (creates `~/.mdxlate/translation_instruction.txt`):

```bash
mdx init
```

2. Run translations:

```bash
export OPENAI_API_KEY=sk-...   # or use OPEN_ROUTER_API_KEY when provider=openrouter
mdx run docs_src out --languages de fr --model gpt-4o-mini
```

Result: translated files under `out/<lang>/...`, preserving the original folder structure.
A cache file `.mdxlate.hashes.json` is written in `docs_src`.

## CLI

```bash
mdx run [OPTIONS] DOCS_SRC OUT_DIR
```

**Options**

* `--base-language TEXT` – Base language (default: `en`)
* `--languages TEXT...` – Target languages, space-separated (default: `de`)
* `--model TEXT` – Model name (default: `gpt-4o-mini`)
* `--provider [openai|openrouter]` – Backend provider (default: `openai`)
* `--api-key TEXT` – API key (overrides env)
* `--api-env-key TEXT` – Env var to read (default: `OPENAI_API_KEY`)
* `--base-url TEXT` – Custom base URL (e.g., OpenRouter)
* `--prompt-path PATH` – Use a custom prompt file instead of the default
* `--force` – Force re-translation, bypassing cache

## Examples

OpenAI (env var):

```bash
export OPENAI_API_KEY=sk-...
mdx run docs_src out --languages de fr --model gpt-4o-mini
```

OpenRouter:

```bash
export OPEN_ROUTER_API_KEY=or-...
mdx run docs_src out --languages de --provider openrouter --model google/gemini-2.5-pro
```

Custom prompt:

```bash
mdx run docs_src out --languages de --prompt-path ./my_prompt.txt
```

## Behavior

* **Prompt:** default lives at `~/.mdxlate/translation_instruction.txt` (created by `mdx init`). You can edit it freely or pass `--prompt-path`.
* **Cache:** re-translation is skipped if *file bytes + prompt content + model + language* are unchanged.
* **Structure:** each language gets its own mirror tree under `OUT_DIR/<lang>/`.

## Programmatic use

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

start_translation(
    docs_src=Path("docs_src"),
    out_dir=Path("out"),
    base_language="en",
    languages=["de", "fr"],
    model="gpt-4o-mini",
    provider="openai",  # or "openrouter"
    api_key=None,       # pass explicitly or rely on env
    base_url=None,
    prompt_path=None,
)
```

## Files of interest

* `mdxlate/cli.py` – Typer CLI (`mdx init`, `mdx run`)
* `mdxlate/client.py` – `make_client()` factory (OpenAI/OpenRouter)
* `mdxlate/translator.py` – translation, hashing, and I/O
* `mdxlate/translation_instruction.txt` – default prompt template

## License

MIT

## Layout

```
repo/
  pyproject.toml
  README.md
  src/
    mdxlate/
      __init__.py
      cli.py
      client.py
      translator.py
      start_translation.py
      translation_instruction.txt
  tests/            # optional
  main.py           # optional local test runner
```

````

---

# pyproject.toml
```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mdxlate"
version = "0.1.0"
description = "Translate Markdown docs into multiple languages using LLMs."
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [{ name = "Tobias Bück" }]
dependencies = [
  "typer>=0.12",
  "openai>=1.40",
  "tenacity>=8.2",
]

[project.scripts]
mdx = "mdxlate.cli:app"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["mdxlate*"]

[tool.setuptools.package-data]
mdxlate = ["translation_instruction.txt"]

[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["tests"]
