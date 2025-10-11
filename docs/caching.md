---
title: Caching System
---

# Caching System

mdxlate includes an intelligent caching system that prevents unnecessary re-translations, saving time and API costs. The cache tracks file content, translation settings, and target languages to determine when re-translation is needed.

## How It Works

### Cache Key Calculation

For each file and target language, mdxlate generates a unique cache key based on:

1. **File path** (relative to source directory)
2. **File content** (SHA-256 hash of bytes)
3. **Translation prompt** (SHA-256 hash)
4. **Model name** (e.g., "gpt-4o-mini")
5. **Target language** (e.g., "de", "fr")

If any of these factors change, the file is re-translated.

### Cache Storage

The cache is stored as a JSON file in the source directory:

**Default location:** `<source_dir>/.mdxlate.hashes.json`

**Example structure:**
```json
{
  "de": {
    "docs/guide.md": "a1b2c3d4e5f6...",
    "docs/api/reference.md": "f6e5d4c3b2a1..."
  },
  "fr": {
    "docs/guide.md": "b2c3d4e5f6a1...",
    "docs/api/reference.md": "e5d4c3b2a1f6..."
  }
}
```

### Translation Decision Flow

```
For each file and target language:
  1. Calculate current cache key
  2. Check if key exists in cache
  3. If key matches → Skip translation
  4. If key differs or missing → Translate file
  5. Update cache with new key
```

## Configuration

### Default Cache Location

By default, the cache file is created in the source directory:

```bash
mdx run docs output --languages de fr
# Creates: docs/.mdxlate.hashes.json
```

### Custom Cache Directory

Use `--cache-dir` to specify a different cache location:

```bash
mdx run docs output --languages de fr --cache-dir /tmp/cache
# Creates: /tmp/cache/.mdxlate.hashes.json
```

**When to use custom cache directory:**
- Source directory is read-only
- CI/CD pipelines with temporary workspaces
- Shared cache across multiple runs
- Version control exclusion

### Programmatic Configuration

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

start_translation(
    docs_src=Path("docs"),
    out_dir=Path("output"),
    base_language="en",
    languages=["de", "fr"],
    cache_dir=Path("/tmp/mdxlate-cache"),  # Custom cache location
)
```

## Cache Behavior

### When Files Are Re-translated

A file is re-translated when **any** of these change:

#### 1. File Content Changes

```bash
# First run
mdx run docs output --languages de
# ✓ Translates docs/guide.md

# Edit docs/guide.md
echo "New content" >> docs/guide.md

# Second run
mdx run docs output --languages de
# ✓ Re-translates docs/guide.md (content changed)
```

#### 2. Translation Prompt Changes

```bash
# First run
mdx run docs output --languages de
# ✓ Translates all files

# Edit ~/.mdxlate/translation_instruction.txt
# (change translation style or terminology)

# Second run
mdx run docs output --languages de
# ✓ Re-translates all files (prompt changed)
```

#### 3. Model Changes

```bash
# First run with gpt-4o-mini
mdx run docs output --languages de --model gpt-4o-mini
# ✓ Translates all files

# Second run with gpt-4o
mdx run docs output --languages de --model gpt-4o
# ✓ Re-translates all files (model changed)
```

#### 4. New Target Language

```bash
# First run
mdx run docs output --languages de fr
# ✓ Translates to de and fr

# Second run with additional language
mdx run docs output --languages de fr es
# ✓ Skips de and fr (cached)
# ✓ Translates to es (new language)
```

### When Files Are Skipped

Files are skipped when **all** of these are unchanged:

- File content (byte-identical)
- Translation prompt
- Model name
- Target language

```bash
# First run
mdx run docs output --languages de fr
# ✓ Translates all files

# Second run (no changes)
mdx run docs output --languages de fr
# ✓ Skips all files (cache hit)
```

## Force Re-translation

### Using --force Flag

Bypass the cache and re-translate everything:

```bash
mdx run docs output --languages de --force
```

**Use cases:**
- Testing translation quality
- Recovering from corrupted output
- Forcing fresh translations after prompt tweaks

### Programmatic Force

```python
from mdxlate.translator import Translator
from mdxlate.client import make_client
import asyncio
from pathlib import Path

client = make_client(provider="openai", api_key="sk-...")

translator = Translator(
    client=client,
    base_language="en",
    languages=["de"],
    model="gpt-4o-mini",
    force_translation=True,  # Bypass cache
)

asyncio.run(translator.translate_directory(
    source_dir=Path("docs"),
    output_dir=Path("output")
))
```

## Cache File Management

### Location

The cache file is always named `.mdxlate.hashes.json` and located in:

- **Default:** Source directory (`docs_src/.mdxlate.hashes.json`)
- **Custom:** Cache directory (`<cache_dir>/.mdxlate.hashes.json`)

### Version Control

**Recommended:** Add to `.gitignore`

```gitignore
# mdxlate cache
.mdxlate.hashes.json
```

**Why exclude:**
- Cache keys are environment-specific
- Reduces merge conflicts
- Not needed for version history

**Exception:** Include cache if you want to share translation state across team members.

### Manual Cache Management

#### View Cache Contents

```bash
cat .mdxlate.hashes.json | jq .
```

#### Clear Cache

```bash
rm .mdxlate.hashes.json
# Next run will translate all files
```

#### Clear Cache for Specific Language

```bash
# Using jq
jq 'del(.de)' .mdxlate.hashes.json > temp.json && mv temp.json .mdxlate.hashes.json
```

#### Clear Cache for Specific File

```bash
# Using jq
jq 'del(.de["docs/guide.md"])' .mdxlate.hashes.json > temp.json && mv temp.json .mdxlate.hashes.json
```

## Troubleshooting

### Issue: Files Not Being Re-translated

**Symptom:** Modified files are not translated on subsequent runs.

**Cause:** Cache key hasn't changed (file appears identical).

**Solutions:**

1. **Check file content:**
   ```bash
   cat docs/guide.md  # Verify changes are saved
   ```

2. **Force re-translation:**
   ```bash
   mdx run docs output --languages de --force
   ```

3. **Clear cache:**
   ```bash
   rm docs/.mdxlate.hashes.json
   mdx run docs output --languages de
   ```

### Issue: All Files Re-translated Unexpectedly

**Symptom:** Every run translates all files, even without changes.

**Possible causes:**

1. **Prompt file modification time changed** (even without content change)
2. **Cache file deleted or not found**
3. **Cache directory changed**

**Solutions:**

1. **Check cache existence:**
   ```bash
   ls -la docs/.mdxlate.hashes.json
   ```

2. **Verify cache directory:**
   ```bash
   # If using --cache-dir, ensure it's consistent
   mdx run docs output --languages de --cache-dir /tmp/cache
   ```

3. **Check file modifications:**
   ```bash
   git status  # See what changed
   ```

### Issue: Cache File Conflicts in Git

**Symptom:** Merge conflicts in `.mdxlate.hashes.json`.

**Solution:** Add to `.gitignore`:

```gitignore
.mdxlate.hashes.json
```

If you need to keep cache in version control, resolve conflicts by:

```bash
# Take remote version
git checkout --theirs .mdxlate.hashes.json

# Or take local version
git checkout --ours .mdxlate.hashes.json

# Or delete and rebuild
rm .mdxlate.hashes.json
git add .mdxlate.hashes.json
```

### Issue: Read-Only Source Directory

**Symptom:** Cannot write cache to source directory.

**Solution:** Use custom cache directory:

```bash
mdx run /readonly/docs output --languages de --cache-dir /tmp/cache
```

## Performance Optimization

### Cache Hit Rate

Monitor cache effectiveness:

```python
import json
from pathlib import Path

cache_file = Path("docs/.mdxlate.hashes.json")
if cache_file.exists():
    cache = json.loads(cache_file.read_text())
    total_entries = sum(len(files) for files in cache.values())
    print(f"Cache contains {total_entries} entries across {len(cache)} languages")
```

### Cache on Fast Storage

For large documentation projects, place cache on SSD:

```bash
mdx run docs output --languages de --cache-dir /fast/ssd/cache
```

### Shared Cache in CI/CD

Use persistent cache directories in CI/CD pipelines:

**GitHub Actions:**
```yaml
- name: Cache translations
  uses: actions/cache@v3
  with:
    path: /tmp/mdxlate-cache
    key: mdxlate-${{ hashFiles('docs/**/*.md') }}

- name: Translate docs
  run: mdx run docs output --languages de fr --cache-dir /tmp/mdxlate-cache
```

**GitLab CI:**
```yaml
translate:
  cache:
    paths:
      - .mdxlate-cache/
  script:
    - mdx run docs output --languages de fr --cache-dir .mdxlate-cache
```

## Advanced Usage

### Per-Language Cache Analysis

```python
import json
from pathlib import Path

cache_file = Path("docs/.mdxlate.hashes.json")
cache = json.loads(cache_file.read_text())

for lang, files in cache.items():
    print(f"{lang}: {len(files)} files cached")
    for file_path in sorted(files.keys()):
        print(f"  - {file_path}")
```

### Cache Migration

When changing cache structure or location:

```bash
# Old location
OLD_CACHE="docs/.mdxlate.hashes.json"

# New location
NEW_CACHE="/tmp/cache/.mdxlate.hashes.json"

# Copy cache
mkdir -p $(dirname "$NEW_CACHE")
cp "$OLD_CACHE" "$NEW_CACHE"

# Use new location
mdx run docs output --languages de --cache-dir /tmp/cache
```

### Cross-Platform Cache

The cache uses POSIX path format for cross-platform compatibility:

```python
# Windows path: docs\guide.md
# Stored in cache as: docs/guide.md
```

This ensures cache files work across Windows, macOS, and Linux.

## Best Practices

1. **Add cache to .gitignore** unless sharing translation state is required
2. **Use custom cache directory** for read-only source directories
3. **Clear cache** when troubleshooting translation issues
4. **Monitor cache size** for large projects (thousands of files)
5. **Use --force sparingly** to avoid unnecessary API costs
6. **Keep cache on fast storage** for better performance
7. **Use persistent cache in CI/CD** to speed up builds

## See Also

- [CLI Reference](cli.md) - Using `--cache-dir` and `--force` options
- [Error Handling](error-handling.md) - Handling cache-related errors
- [Development Guide](development.md) - Understanding cache implementation
