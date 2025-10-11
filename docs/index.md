---
title: Getting Started
---

# Getting Started with mdxlate

**mdxlate** is a powerful tool for translating Markdown documentation into multiple languages using Large Language Models (LLMs). It comes with batteries included: a customizable prompt template, CLI, OpenAI/OpenRouter provider support, and intelligent change-detection caching.

## Quick Navigation

- **[CLI Reference](cli.md)** – Complete command-line interface documentation
- **[Programmatic Usage](programmatic.md)** – Python API and integration examples
- **[Caching System](caching.md)** – How the cache works and configuration
- **[Custom Prompt](custom-prompt.md)** – Customize the translation prompt
- **[Error Handling](error-handling.md)** – Failure reports and recovery
- **[Development Guide](development.md)** – Contributing and project structure
- **[FAQ / Troubleshooting](faq.md)** – Common issues and solutions
- **[Jekyll Integration](integrations/jekyll.md)** – Translating Jekyll sites

## Installation

Install mdxlate using pip:

```bash
pip install mdxlate
```

Or for development from source:

```bash
git clone https://github.com/Softoft-Orga/markdown-automatic-translation.git
cd markdown-automatic-translation
pip install -e .
```

## Quick Start

### 1. Initialize the Translation Prompt

Create an editable translation prompt template:

```bash
mdx init
```

This creates `~/.mdxlate/translation_instruction.txt` which you can customize to fit your translation needs.

### 2. Set Up API Key

Configure your API key as an environment variable:

```bash
export OPENAI_API_KEY=sk-...
# or for OpenRouter
export OPEN_ROUTER_API_KEY=...
```

### 3. Run Your First Translation

Translate your markdown files:

```bash
mdx run docs_src out --languages de fr --model gpt-4o-mini
```

This command:
- Reads markdown files from `docs_src/`
- Translates them to German (`de`) and French (`fr`)
- Outputs translated files to `out/de/...` and `out/fr/...`
- Creates a cache file `.mdxlate.hashes.json` in `docs_src` to skip unchanged files

## Minimal Example

Let's translate a simple documentation directory:

**Input structure:**
```
docs/
  index.md
  guide.md
  api/
    reference.md
```

**Command:**
```bash
mdx run docs output --languages es ja --model gpt-4o-mini
```

**Output structure:**
```
output/
  es/
    index.md
    guide.md
    api/
      reference.md
  ja/
    index.md
    guide.md
    api/
      reference.md
```

The original folder structure is preserved for each language!

## Key Features

### 🔄 Smart Caching
Re-translation is skipped if the file content, prompt, model, and target language haven't changed. This saves time and API costs.

### 📝 Customizable Prompt
Edit `~/.mdxlate/translation_instruction.txt` to control translation style, terminology, and special handling (like Jekyll frontmatter preservation).

### 🌐 Multiple Providers
Switch between OpenAI and OpenRouter with a single flag:
```bash
mdx run docs out --provider openrouter --languages de fr
```

### ⚡ Concurrent Processing
Multiple files are translated in parallel for faster processing (default: 8 concurrent requests).

### 🛡️ Error Recovery
If some files fail to translate, mdxlate continues processing others and generates a failure report for easy retry.

## Next Steps

- Learn about all [CLI options](cli.md)
- Explore [programmatic usage](programmatic.md) in Python
- Understand the [caching system](caching.md)
- Customize your [translation prompt](custom-prompt.md)
- Set up [error handling](error-handling.md) for production
- Read the [development guide](development.md) to contribute

## Common Use Cases

### Static Site Generators
- **[Jekyll](integrations/jekyll.md)** – Complete guide with frontmatter preservation
- **Hugo** – Works with Hugo's frontmatter format
- **VitePress** – Translate VitePress documentation
- **MkDocs** – Generate multilingual MkDocs sites

### Documentation Projects
- Translate technical documentation
- Create multilingual API references
- Localize README files
- Generate i18n content for docs sites

### Content Migration
- Batch translate markdown content
- Migrate documentation to new languages
- Update translations when source changes (using cache)
