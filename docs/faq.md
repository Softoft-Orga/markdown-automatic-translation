---
title: FAQ / Troubleshooting
---

# FAQ / Troubleshooting

Common questions, issues, and solutions for mdxlate.

## Frequently Asked Questions

### General Questions

#### What is mdxlate?

mdxlate is a tool for translating Markdown documentation into multiple languages using Large Language Models (LLMs). It provides a CLI and Python API with intelligent caching, error handling, and support for static site generators like Jekyll.

#### Which LLM providers are supported?

- **OpenAI** (default): GPT-4o, GPT-4o-mini, GPT-4, etc.
- **OpenRouter**: Access to multiple models including Claude, Gemini, etc.

#### What file formats are supported?

Currently, mdxlate supports:
- Markdown files (`.md`)
- Markdown with YAML frontmatter (Jekyll, Hugo, VitePress, etc.)

#### Is mdxlate free?

mdxlate is free and open-source (MIT License), but you need to pay for LLM API usage (OpenAI, OpenRouter, etc.).

#### How accurate are the translations?

Translation quality depends on:
- **Model choice**: GPT-4o > GPT-4o-mini > GPT-3.5
- **Prompt quality**: Well-crafted prompts improve results
- **Content complexity**: Technical content may need custom prompts

For best results, use GPT-4o or GPT-4 with a customized prompt.

### Installation & Setup

#### How do I install mdxlate?

```bash
pip install mdxlate
```

Or from source:
```bash
git clone https://github.com/Softoft-Orga/markdown-automatic-translation.git
cd markdown-automatic-translation
pip install -e .
```

#### How do I set up my API key?

```bash
# For OpenAI
export OPENAI_API_KEY=sk-...

# For OpenRouter
export OPEN_ROUTER_API_KEY=sk-or-v1-...
```

Or pass directly in command:
```bash
mdx run docs output --languages de --api-key sk-...
```

#### Where is the translation prompt stored?

Default location: `~/.mdxlate/translation_instruction.txt`

Create it with:
```bash
mdx init
```

### Usage Questions

#### How do I translate to multiple languages at once?

```bash
mdx run docs output --languages de fr es ja
```

#### How do I change the translation model?

```bash
mdx run docs output --languages de --model gpt-4o
```

#### How do I force re-translation of all files?

```bash
mdx run docs output --languages de --force
```

#### Can I use mdxlate in Python scripts?

Yes! See [Programmatic Usage](programmatic.md):

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

start_translation(
    docs_src=Path("docs"),
    out_dir=Path("output"),
    base_language="en",
    languages=["de", "fr"],
)
```

#### How do I customize the translation style?

Edit the prompt file:

```bash
mdx init  # Create prompt file
nano ~/.mdxlate/translation_instruction.txt  # Edit
mdx run docs output --languages de  # Use customized prompt
```

See [Custom Prompt](custom-prompt.md) for details.

### Caching Questions

#### How does the cache work?

mdxlate caches translations based on:
- File content (hash)
- Translation prompt (hash)
- Model name
- Target language

If any of these change, the file is re-translated. See [Caching System](caching.md).

#### Where is the cache file stored?

Default: `<source_dir>/.mdxlate.hashes.json`

Custom location:
```bash
mdx run docs output --languages de --cache-dir /tmp/cache
```

#### How do I clear the cache?

```bash
rm <source_dir>/.mdxlate.hashes.json
```

Or use `--force` to bypass cache:
```bash
mdx run docs output --languages de --force
```

#### Should I commit the cache file to Git?

Usually no. Add to `.gitignore`:

```gitignore
.mdxlate.hashes.json
```

Exception: If you want to share translation state across team members.

### Error Handling

#### What happens if translation fails?

mdxlate:
1. Continues processing other files
2. Saves successful translations to cache
3. Generates a failure report: `.mdxlate.failures.json`

Simply re-run to retry failed files (cache ensures successful ones are skipped).

#### How do I check for failed translations?

```bash
# Check if failure report exists
if [ -f "docs/.mdxlate.failures.json" ]; then
  cat docs/.mdxlate.failures.json
fi
```

See [Error Handling](error-handling.md) for details.

## Troubleshooting

### Installation Issues

#### `pip install mdxlate` fails

**Solutions:**

1. **Upgrade pip:**
   ```bash
   pip install --upgrade pip
   ```

2. **Use Python 3.10+:**
   ```bash
   python3 --version  # Should be 3.10 or higher
   ```

3. **Install from source:**
   ```bash
   git clone https://github.com/Softoft-Orga/markdown-automatic-translation.git
   cd markdown-automatic-translation
   pip install -e .
   ```

#### `mdx` command not found

**Cause:** CLI not in PATH

**Solutions:**

1. **Verify installation:**
   ```bash
   pip show mdxlate
   ```

2. **Use Python module:**
   ```bash
   python -m mdxlate.cli run docs output --languages de
   ```

3. **Add to PATH:**
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

### API Issues

#### Authentication error: Invalid API key

**Cause:** Missing, expired, or incorrect API key

**Solutions:**

1. **Check environment variable:**
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **Set API key:**
   ```bash
   export OPENAI_API_KEY=sk-your-actual-key
   ```

3. **Pass key explicitly:**
   ```bash
   mdx run docs output --languages de --api-key sk-your-key
   ```

#### Rate limit exceeded

**Cause:** Too many API requests in short time

**Solutions:**

1. **Wait and retry:**
   ```bash
   # Wait a few minutes
   mdx run docs output --languages de
   # Failed files will be retried (thanks to cache!)
   ```

2. **Switch to different model:**
   ```bash
   mdx run docs output --languages de --model gpt-4o-mini
   ```

3. **Use OpenRouter:**
   ```bash
   export OPEN_ROUTER_API_KEY=sk-or-v1-...
   mdx run docs output --languages de --provider openrouter
   ```

#### Connection timeout

**Cause:** Network issues or API unreachable

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping api.openai.com
   ```

2. **Retry:**
   ```bash
   mdx run docs output --languages de
   ```

3. **Use custom base URL:**
   ```bash
   mdx run docs output --languages de --base-url https://api.openai.com/v1
   ```

### Translation Issues

#### Translations are low quality

**Solutions:**

1. **Use better model:**
   ```bash
   mdx run docs output --languages de --model gpt-4o
   ```

2. **Customize prompt:**
   ```bash
   mdx init
   nano ~/.mdxlate/translation_instruction.txt
   # Add specific instructions for your domain
   ```

3. **Add examples to prompt:**
   ```text
   Example:
   Input: "Getting Started with Docker"
   Output: "Erste Schritte mit Docker"
   ```

#### Code blocks are being translated

**Cause:** Prompt doesn't explicitly preserve code

**Solution:** Update prompt to explicitly exclude code:

```text
NEVER translate:
- Code blocks (```)
- Inline code (`)
- Function names
- Variable names
```

#### YAML frontmatter structure changed

**Cause:** Prompt doesn't preserve frontmatter properly

**Solution:** Update prompt:

```text
YAML frontmatter rules:
- Keep structure identical
- Translate only values, not keys
- Preserve dates, categories, tags

Example:
Input:
---
title: "Hello"
date: 2024-01-01
---

Output:
---
title: "Hallo"
date: 2024-01-01
---
```

#### Translations seem inconsistent

**Cause:** Using temperature > 0 (randomness)

**Note:** mdxlate uses `temperature=0.2` by default for consistency. This is hardcoded for deterministic results.

**Solution:** For even more consistency, modify `translator.py` to use `temperature=0.0`.

#### Some files not being translated

**Cause:** Cache hit (files already translated)

**Solutions:**

1. **Check cache:**
   ```bash
   cat .mdxlate.hashes.json
   ```

2. **Force re-translation:**
   ```bash
   mdx run docs output --languages de --force
   ```

3. **Clear cache:**
   ```bash
   rm .mdxlate.hashes.json
   mdx run docs output --languages de
   ```

### File System Issues

#### Permission denied error

**Cause:** No write permission for output directory

**Solutions:**

1. **Check permissions:**
   ```bash
   ls -ld output/
   ```

2. **Fix permissions:**
   ```bash
   chmod 755 output/
   ```

3. **Use different directory:**
   ```bash
   mdx run docs ~/translations --languages de
   ```

#### Cannot write to source directory (read-only)

**Cause:** Source directory is read-only (cache can't be written)

**Solution:** Use custom cache directory:

```bash
mdx run /readonly/docs output --languages de --cache-dir /tmp/cache
```

#### Source inside output error

**Cause:** Source directory is inside output directory

**Solution:** Use separate directories:

```bash
# Wrong
mdx run output/source output --languages de

# Correct
mdx run source output --languages de
```

### Performance Issues

#### Translation is very slow

**Possible causes & solutions:**

1. **Large files:** Break into smaller files
2. **Many files:** Normal, use cache for subsequent runs
3. **Network latency:** Use different API endpoint or provider
4. **Rate limiting:** Wait between runs

#### High API costs

**Solutions:**

1. **Use cheaper model:**
   ```bash
   mdx run docs output --languages de --model gpt-4o-mini
   ```

2. **Use cache effectively:**
   ```bash
   # Only new/changed files are translated
   mdx run docs output --languages de
   ```

3. **Translate fewer languages:**
   ```bash
   mdx run docs output --languages de  # Instead of de fr es ja
   ```

### Platform-Specific Issues

#### Windows: Path issues

**Cause:** Windows uses backslashes, but cache uses forward slashes

**Solution:** This is handled automatically. If issues persist:

```bash
# Use PowerShell or Git Bash
mdx run docs output --languages de
```

#### macOS: SSL certificate errors

**Cause:** Python SSL certificates not installed

**Solution:**

```bash
# Install certificates
/Applications/Python\ 3.10/Install\ Certificates.command
```

#### Linux: Permission errors

**Cause:** Installed to system Python without sudo

**Solution:**

```bash
# Install for user only
pip install --user mdxlate

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install mdxlate
```

## Advanced Troubleshooting

### Debug Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from mdxlate.start_translation import start_translation
# ... run translation
```

### Test API Connection

```python
from mdxlate.client import make_client
import asyncio

async def test_api():
    client = make_client(provider="openai", api_key="sk-...")
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}]
    )
    
    print("API works!")
    print(response.choices[0].message.content)

asyncio.run(test_api())
```

### Isolate Problem Files

```bash
# Test single file
mdx run problem-file/ output --languages de --force

# If successful, issue is with concurrent processing
# If fails, issue is with the file or prompt
```

### Check Cache Integrity

```bash
# Validate JSON
cat .mdxlate.hashes.json | jq .

# If invalid, delete and rebuild
rm .mdxlate.hashes.json
mdx run docs output --languages de
```

## Best Practices

### 1. Start Small

```bash
# Test with one language first
mdx run docs output --languages de

# Then scale to multiple languages
mdx run docs output --languages de fr es
```

### 2. Use Version Control

```gitignore
# .gitignore
.mdxlate.hashes.json
.mdxlate.failures.json
output/
```

### 3. Monitor Costs

- Start with `gpt-4o-mini` for cost-effective translation
- Upgrade to `gpt-4o` for better quality when needed
- Use cache to avoid re-translating unchanged files

### 4. Customize Prompts

- Edit `~/.mdxlate/translation_instruction.txt` for your domain
- Add specific terminology and examples
- Test with sample files before large batches

### 5. Handle Errors Gracefully

- Check `.mdxlate.failures.json` after each run
- Re-run to retry failed files (cache helps!)
- Set up alerts in CI/CD pipelines

### 6. Test Translations

- Review translated content for accuracy
- Use native speakers for quality checks
- Iterate on prompt based on feedback

## Getting Help

### Community Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Softoft-Orga/markdown-automatic-translation/issues)
- **GitHub Discussions**: [Ask questions and share ideas](https://github.com/Softoft-Orga/markdown-automatic-translation/discussions)

### Documentation

- [Getting Started](index.md)
- [CLI Reference](cli.md)
- [Programmatic Usage](programmatic.md)
- [Caching System](caching.md)
- [Custom Prompt](custom-prompt.md)
- [Error Handling](error-handling.md)
- [Development Guide](development.md)

### Report an Issue

When reporting an issue, include:

1. **mdxlate version**: `pip show mdxlate`
2. **Python version**: `python --version`
3. **Operating system**: `uname -a` (Linux/macOS) or `systeminfo` (Windows)
4. **Command used**: Full command with options (mask API keys!)
5. **Error message**: Complete error output
6. **Minimal example**: Sample files that reproduce the issue

### Contributing

Want to improve mdxlate? See the [Development Guide](development.md)!

---

**Still having issues?** Open an issue on [GitHub](https://github.com/Softoft-Orga/markdown-automatic-translation/issues) with details, and we'll help!
