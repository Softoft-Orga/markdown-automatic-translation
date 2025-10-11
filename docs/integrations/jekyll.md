# Jekyll Integration Guide

This guide explains how to use `mdxlate` to translate Jekyll sites into multiple languages.

## Overview

Jekyll is a static site generator that uses Markdown files with YAML frontmatter. The `mdxlate` tool is designed to preserve Jekyll's frontmatter structure while translating the content, making it ideal for creating multilingual Jekyll sites.

## Quick Start

### 1. Install mdxlate

```bash
pip install mdxlate
```

Or for development from source:
```bash
pip install -e .
```

### 2. Initialize the Translation Prompt

```bash
mdx init
```

This creates `~/.mdxlate/translation_instruction.txt` which is already configured to handle Jekyll frontmatter correctly.

### 3. Translate Your Jekyll Site

```bash
export OPENAI_API_KEY=sk-...
mdx run _posts output --languages de fr --model gpt-4o-mini
```

This will create translated versions of your posts in `output/de/_posts/` and `output/fr/_posts/`.

## Jekyll-Specific Features

### YAML Frontmatter Handling

The translation tool automatically preserves Jekyll's YAML frontmatter structure. For example:

**Input (`_posts/2024-01-01-hello-world.md`):**
```markdown
---
layout: post
title: "Hello World"
date: 2024-01-01
categories: [tutorial, jekyll]
tags: [getting-started]
author: "John Doe"
description: "Learn how to get started with Jekyll"
---

# Hello World

This is my first Jekyll post. Let's learn how to create amazing websites!
```

**Output (`output/de/_posts/2024-01-01-hello-world.md`):**
```markdown
---
layout: post
title: "Hallo Welt"
date: 2024-01-01
categories: [tutorial, jekyll]
tags: [getting-started]
author: "John Doe"
description: "Erfahren Sie, wie Sie mit Jekyll beginnen"
---

# Hallo Welt

Dies ist mein erster Jekyll-Beitrag. Lernen wir, wie man fantastische Websites erstellt!
```

**What gets translated:**
- Title values
- Description values
- Content body

**What stays the same:**
- YAML keys (`layout`, `title`, `date`, etc.)
- Dates and timestamps
- Category/tag identifiers (unless you want them translated)
- Author names
- Code blocks and inline code

## Recommended Workflow

### Option 1: Separate Language Directories

Organize your Jekyll site with language-specific directories:

```
my-jekyll-site/
  _config.yml
  en/
    _posts/
    _pages/
    index.md
  de/
    _posts/
    _pages/
    index.md
  fr/
    _posts/
    _pages/
    index.md
```

**Translation command:**
```bash
mdx run en/ . --languages de fr --model gpt-4o-mini
```

### Option 2: Language-Specific Sites

Maintain separate Jekyll sites for each language:

```
sites/
  en/
    _config.yml
    _posts/
    index.md
  de/
    _config.yml
    _posts/
    index.md
```

**Translation workflow:**
```bash
# Translate posts
mdx run sites/en/_posts sites/de/_posts --languages de --model gpt-4o-mini

# Translate pages
mdx run sites/en/_pages sites/de/_pages --languages de --model gpt-4o-mini
```

### Option 3: GitHub Pages with Multiple Repos

Host different language versions in separate repositories:

```bash
# Clone your main site
git clone https://github.com/user/mysite.git
git clone https://github.com/user/mysite-de.git

# Translate
mdx run mysite/_posts mysite-de/_posts --languages de --model gpt-4o-mini

# Commit and push to German site
cd mysite-de
git add .
git commit -m "Update German translations"
git push
```

## Jekyll Plugins Compatibility

### Jekyll Polyglot

If you're using [Jekyll Polyglot](https://github.com/untra/polyglot) for multilingual sites, `mdxlate` works great with it:

```bash
# Translate to language-specific directories
mdx run _posts output --languages de fr es --model gpt-4o-mini

# Then copy to your polyglot structure
cp -r output/de/_posts de/_posts/
cp -r output/fr/_posts fr/_posts/
cp -r output/es/_posts es/_posts/
```

### Jekyll Sitemap

The sitemap plugin will automatically pick up your translated pages. No special configuration needed.

## Configuration Examples

### Using Custom Prompts for Jekyll

If you need special handling for Jekyll-specific features, customize the prompt:

```bash
# Edit the prompt
mdx init --prompt-path ./jekyll_translation_prompt.txt

# Run with custom prompt
mdx run _posts output --languages de --prompt-path ./jekyll_translation_prompt.txt
```

### Handling Liquid Templates

Jekyll uses Liquid for templating. The default translation instruction already preserves Liquid syntax:

**Input:**
```markdown
---
layout: post
title: "My Post"
---

Welcome {{ site.name }}! Today is {{ page.date | date: "%Y-%m-%d" }}.
```

**Output (German):**
```markdown
---
layout: post
title: "Mein Beitrag"
---

Willkommen {{ site.name }}! Heute ist {{ page.date | date: "%Y-%m-%d" }}.
```

The Liquid tags `{{ site.name }}` and `{{ page.date | date: "%Y-%m-%d" }}` remain unchanged.

## CI/CD Integration

### GitHub Actions Example

Automatically translate your Jekyll site on push:

```yaml
name: Translate Jekyll Site

on:
  push:
    branches: [main]
    paths:
      - 'en/_posts/**'
      - 'en/_pages/**'

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install mdxlate
        run: pip install mdxlate
      
      - name: Initialize translation prompt
        run: mdx init
      
      - name: Translate content
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          mdx run en/_posts . --languages de fr --model gpt-4o-mini --cache-dir /tmp
          mdx run en/_pages . --languages de fr --model gpt-4o-mini --cache-dir /tmp
      
      - name: Commit translations
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add de/ fr/
          git diff --quiet && git diff --staged --quiet || git commit -m "Auto-translate content"
          git push
```

### GitLab CI Example

```yaml
translate:
  image: python:3.10
  script:
    - pip install mdxlate
    - mdx init
    - mdx run en/_posts . --languages de fr --model gpt-4o-mini --cache-dir /tmp
  artifacts:
    paths:
      - de/
      - fr/
  only:
    changes:
      - en/_posts/**
      - en/_pages/**
```

## Best Practices

### 1. Use Cache for Efficiency

Cache translations to avoid re-translating unchanged files:

```bash
# Cache is automatic - just run again
mdx run _posts output --languages de --model gpt-4o-mini

# For CI/CD with read-only source, use custom cache dir
mdx run _posts output --languages de --cache-dir /tmp
```

### 2. Translate Incrementally

Start with a few posts to test:

```bash
# Test with a single post
mdx run _posts/2024-01-01-hello-world.md output --languages de --model gpt-4o-mini

# Then scale up
mdx run _posts output --languages de fr es --model gpt-4o-mini
```

### 3. Review Translations

Always review automated translations, especially for:
- Technical terms specific to your domain
- Brand names and product names
- Cultural references
- Date/time formats

### 4. Handle File Names

Jekyll often uses date-prefixed filenames (`2024-01-01-post-title.md`). Keep the same naming:

```bash
# The tool preserves the directory structure and filenames
mdx run _posts output --languages de

# Result:
# output/de/_posts/2024-01-01-post-title.md (German version)
```

### 5. Manage Permalinks

If using custom permalinks in frontmatter, consider your strategy:

```markdown
---
layout: post
title: "My Post"
permalink: /posts/my-post/  # Should this be translated?
---
```

To translate permalinks, you'll need to manually adjust the frontmatter after translation or customize the translation prompt.

## Troubleshooting

### Issue: YAML Frontmatter Keys Are Translated

**Problem:** Keys like `layout` or `title` are getting translated.

**Solution:** The default prompt already handles this. If you've customized the prompt, ensure it includes:
```
**Do not** translate the keys (e.g., layout, title, description, hero).
```

### Issue: Liquid Tags Are Broken

**Problem:** Liquid syntax like `{{ variable }}` is getting translated.

**Solution:** The default instruction preserves these. Check that you haven't modified the template placeholders section:
```
Template placeholders or component slots like {{ variable }}, {% raw %}{% endraw %}, or {content}.
```

### Issue: Date Formats Change

**Problem:** Dates are being translated (e.g., "January" → "Januar").

**Solution:** This is actually correct for localization! If you want to keep dates in the original format, add them to the frontmatter and use Liquid for display:

```markdown
---
date: 2024-01-01
date_display: "January 1, 2024"
---

Published on: {{ page.date | date: "%B %d, %Y" }}
```

### Issue: Categories/Tags Are Translated

**Problem:** Categories like `[tutorial, jekyll]` are being translated to `[Tutorial, Jekyll]`.

**Solution:** This preserves the array structure. If you want to keep them in English, add them to your custom glossary in the translation prompt.

## Advanced Topics

### Multi-Site Management

For large organizations with multiple Jekyll sites:

```bash
#!/bin/bash
# translate-all-sites.sh

SITES=("blog" "docs" "marketing")
LANGUAGES=("de" "fr" "es" "ja")

for site in "${SITES[@]}"; do
  for lang in "${LANGUAGES[@]}"; do
    echo "Translating $site to $lang..."
    mdx run sites/$site/en sites/$site/$lang --languages $lang --model gpt-4o-mini
  done
done
```

### Custom Domain Setup

When using GitHub Pages with custom domains per language:

```
en.example.com → GitHub Pages from main repo
de.example.com → GitHub Pages from mysite-de repo
fr.example.com → GitHub Pages from mysite-fr repo
```

Use `mdxlate` to keep all versions synchronized.

## Examples

### Blog Post Translation

```bash
# Translate a single blog post
mdx run _posts/2024-01-15-my-article.md output --languages de fr

# Translate all posts from 2024
mdx run _posts/2024-* output --languages de fr

# Translate entire posts directory
mdx run _posts output --languages de fr es
```

### Documentation Site

```bash
# Translate docs
mdx run docs/en docs --languages de fr --model gpt-4o-mini

# Result structure:
# docs/
#   en/
#     getting-started.md
#   de/
#     getting-started.md
#   fr/
#     getting-started.md
```

### Multilingual Landing Page

```bash
# Translate main pages
mdx run pages/en pages --languages de fr es --model gpt-4o-mini

# Pages structure:
# pages/
#   en/
#     index.md
#     about.md
#     contact.md
#   de/
#     index.md
#     about.md
#     contact.md
```

## Resources

- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Jekyll Polyglot Plugin](https://github.com/untra/polyglot)
- [GitHub Pages Custom Domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
- [Liquid Template Language](https://shopify.github.io/liquid/)

## Support

For issues specific to Jekyll integration:
1. Check that your YAML frontmatter is valid
2. Review the translation prompt at `~/.mdxlate/translation_instruction.txt`
3. Test with a single file first
4. Open an issue on GitHub with a minimal reproducible example
