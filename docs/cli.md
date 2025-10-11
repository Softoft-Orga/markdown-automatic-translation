---
title: CLI Reference
---

# CLI Reference

The `mdx` command-line interface provides two main commands for working with mdxlate.

## Commands Overview

- `mdx init` – Initialize editable translation prompt file
- `mdx run` – Run translation on markdown files

## mdx init

Initialize an editable translation prompt template.

### Usage

```bash
mdx init [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--prompt-path` | Path | `~/.mdxlate/translation_instruction.txt` | Path for editable prompt template |

### Examples

**Create default prompt file:**
```bash
mdx init
```

**Create prompt in custom location:**
```bash
mdx init --prompt-path ./my-custom-prompt.txt
```

### Output

```
✓ Created prompt template at: /home/user/.mdxlate/translation_instruction.txt

Edit this file to customize translations.
Use: mdx run ... --prompt-path /home/user/.mdxlate/translation_instruction.txt
```

## mdx run

Translate markdown files from source directory to target languages.

### Usage

```bash
mdx run [OPTIONS] DOCS_SRC OUT_DIR
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `DOCS_SRC` | Yes | Source directory containing markdown files to translate |
| `OUT_DIR` | Yes | Output directory for translated files |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--base-language` | TEXT | `en` | Source language code |
| `--languages` | TEXT... | `de` | Target language codes (space-separated) |
| `--model` | TEXT | `gpt-4o-mini` | LLM model name |
| `--provider` | Choice | `openai` | Provider: `openai` or `openrouter` |
| `--api-key` | TEXT | None | API key (overrides environment variable) |
| `--api-env-key` | TEXT | `OPENAI_API_KEY` | Environment variable name for API key |
| `--base-url` | TEXT | None | Custom base URL for API endpoint |
| `--prompt-path` | Path | None | Path to custom translation instruction file |
| `--force` | Flag | False | Force re-translation, bypassing cache |
| `--cache-dir` | Path | None | Directory for cache file (defaults to source directory) |

### Examples

#### Basic Translation

Translate to German and French:
```bash
mdx run docs output --languages de fr
```

#### OpenAI with Custom Model

```bash
export OPENAI_API_KEY=sk-...
mdx run docs_src out --languages de fr es --model gpt-4o --provider openai
```

#### OpenRouter Provider

```bash
export OPEN_ROUTER_API_KEY=sk-or-v1-...
mdx run docs output --languages ja ko zh --provider openrouter --api-env-key OPEN_ROUTER_API_KEY
```

#### Custom Base URL

```bash
mdx run docs out --languages de --base-url https://api.openai.com/v1
```

#### Custom Prompt

```bash
mdx run docs out --languages de fr --prompt-path ./custom-prompt.txt
```

#### Force Re-translation

Bypass cache and re-translate everything:
```bash
mdx run docs out --languages de --force
```

#### Custom Cache Directory

Useful for read-only source directories:
```bash
mdx run docs out --languages de --cache-dir /tmp/mdxlate-cache
```

## Environment Variables

mdxlate respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | None |
| `OPEN_ROUTER_API_KEY` | OpenRouter API key | None |

You can override the environment variable name using `--api-env-key`:

```bash
export MY_API_KEY=sk-...
mdx run docs out --languages de --api-env-key MY_API_KEY
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (API failure, invalid arguments, etc.) |

## Workflows

### Translate New Content Only

The cache ensures only new or modified files are translated:

```bash
# First run - translates all files
mdx run docs out --languages de fr

# Modify docs/new-page.md

# Second run - only translates new-page.md
mdx run docs out --languages de fr
```

### Multi-Language Documentation Site

```bash
# Translate to multiple languages
mdx run en/ output/ --languages de fr es ja zh --model gpt-4o-mini

# Directory structure:
# output/
#   de/...
#   fr/...
#   es/...
#   ja/...
#   zh/...
```

### CI/CD Pipeline

```bash
#!/bin/bash
set -e

# Initialize prompt
mdx init

# Translate documentation
mdx run docs output --languages de fr es --model gpt-4o-mini --cache-dir /tmp

# Check for failures
if [ -f "docs/.mdxlate.failures.json" ]; then
  echo "Translation failures detected!"
  cat docs/.mdxlate.failures.json
  exit 1
fi
```

### Production Deployment

```bash
# Use specific model and provider
mdx run docs site/i18n \
  --languages de fr es it pt \
  --model gpt-4o \
  --provider openai \
  --api-key $OPENAI_API_KEY \
  --cache-dir ./cache
```

## Common Patterns

### Translate Specific Directory

```bash
# Only translate API reference
mdx run docs/api output/api --languages de fr
```

### Multiple Source Languages

Translate from different base languages:

```bash
# English to German
mdx run en/ output/ --base-language en --languages de

# German to French
mdx run de/ output/ --base-language de --languages fr
```

### Testing Translations

Use a small subset and force re-translation:

```bash
# Test with single file
mdx run test-doc/ output/ --languages de --force
```

## Tips & Best Practices

### API Key Security
- Never commit API keys to version control
- Use environment variables or secret management tools
- Rotate keys regularly

### Cost Optimization
- Use cache to avoid re-translating unchanged files
- Start with `gpt-4o-mini` for cost-effective translations
- Use `gpt-4o` or `gpt-4` for higher quality when needed

### Performance
- Default concurrency (8) works well for most cases
- Larger projects benefit from parallel processing
- Cache directory on fast storage (e.g., SSD) improves performance

### Error Recovery
- Check `.mdxlate.failures.json` for failed translations
- Re-run the same command to retry failed files (cache helps!)
- Use `--force` only when you want to re-translate everything

## Troubleshooting

See the [FAQ / Troubleshooting](faq.md) page for common issues and solutions.
