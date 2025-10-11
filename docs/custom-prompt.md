---
title: Custom Prompt
---

# Custom Prompt

The translation prompt is the heart of mdxlate's translation quality. It instructs the LLM on how to translate content, what to preserve, and what style to use. mdxlate makes the prompt fully customizable to fit your needs.

## Default Prompt

### Location

The default prompt template is stored at:
```
~/.mdxlate/translation_instruction.txt
```

### Creating the Default Prompt

Initialize the prompt file:

```bash
mdx init
```

Output:
```
✓ Created prompt template at: /home/user/.mdxlate/translation_instruction.txt

Edit this file to customize translations.
Use: mdx run ... --prompt-path /home/user/.mdxlate/translation_instruction.txt
```

### Viewing the Default Prompt

```bash
cat ~/.mdxlate/translation_instruction.txt
```

The default prompt includes:
- Professional translation guidelines
- Instructions to preserve markdown formatting
- YAML frontmatter handling (for Jekyll, Hugo, etc.)
- Code block preservation
- Link and image preservation
- Special character handling

## Customizing the Prompt

### Edit the Default Prompt

```bash
# Open in your editor
nano ~/.mdxlate/translation_instruction.txt
# or
code ~/.mdxlate/translation_instruction.txt
```

### Use Custom Prompt File

Create and use a custom prompt file:

```bash
# Create custom prompt
cat > ./my-prompt.txt << 'EOF'
You are a professional technical translator.

Translate the following markdown content accurately.

Rules:
- Preserve all markdown formatting
- Keep code blocks unchanged
- Translate technical terms consistently
- Maintain professional tone
EOF

# Use custom prompt
mdx run docs output --languages de fr --prompt-path ./my-prompt.txt
```

## Prompt Structure

### Basic Structure

```
[Role/Persona Definition]

[Translation Instructions]

[Formatting Rules]

[Preservation Rules]

[Special Cases]
```

### Example Custom Prompt

```text
You are a world-class technical translator specializing in software documentation.

Your task is to translate markdown content while maintaining:
1. Professional technical tone
2. Accuracy of technical terminology
3. Cultural appropriateness for the target audience

TRANSLATION RULES:
- Translate all prose content to the target language
- Use industry-standard technical terms
- Keep brand names unchanged
- Preserve markdown formatting exactly

PRESERVE UNCHANGED:
- Code blocks and inline code
- URLs and file paths
- YAML frontmatter structure (translate only values)
- HTML tags and attributes
- Mathematical formulas
- API endpoints and function names

FORMATTING:
- Maintain heading levels
- Keep list structures intact
- Preserve emphasis (bold, italic)
- Retain table structure

OUTPUT:
- Return ONLY the translated markdown
- No explanations or comments
- Match the input structure exactly
```

## Prompt Customization Examples

### 1. Casual Tone

For blog posts or informal documentation:

```text
You are a friendly, approachable translator.

Translate the content into casual, conversational language while keeping it accurate.

- Use friendly, everyday language
- Translate idioms to culturally appropriate equivalents
- Keep technical terms in English if commonly used
- Maintain an engaging, warm tone
```

### 2. Academic/Formal Tone

For research papers or formal documentation:

```text
You are an academic translator specializing in technical research.

Translate with formal, precise language suitable for academic publication.

- Use formal academic vocabulary
- Translate technical terms to established academic equivalents
- Maintain scholarly tone and structure
- Preserve citations and references exactly
```

### 3. API Documentation

For API reference documentation:

```text
You are a technical translator specializing in API documentation.

CRITICAL RULES:
- NEVER translate: function names, parameter names, class names
- NEVER translate: JSON keys, API endpoints, HTTP methods
- ALWAYS keep code examples in English
- ONLY translate: descriptions, explanations, comments

Preserve all technical accuracy while making explanations clear in the target language.
```

### 4. Marketing Content

For product documentation with marketing elements:

```text
You are a marketing translator with technical knowledge.

Translate to engage users while maintaining technical accuracy.

- Use persuasive, benefit-focused language
- Adapt marketing messages to cultural context
- Keep product names and features unchanged
- Translate with enthusiasm and clarity
```

### 5. Localization-Focused

For culturally-adapted translations:

```text
You are a localization expert, not just a translator.

Adapt content for the target culture:

- Translate idioms to cultural equivalents
- Adjust examples to local context
- Use region-appropriate terminology
- Adapt measurements and formats (dates, numbers)
- Consider cultural sensitivities

Maintain technical accuracy while making content feel native.
```

## Special Use Cases

### Jekyll/Hugo Frontmatter

Customize prompt to handle specific frontmatter fields:

```text
When translating YAML frontmatter:

TRANSLATE these fields:
- title
- description
- excerpt
- content
- summary

KEEP UNCHANGED:
- layout
- date
- categories
- tags
- permalink
- author
- image (URLs)

Example:
Input:
---
title: "Hello World"
date: 2024-01-01
---

Output:
---
title: "Hallo Welt"
date: 2024-01-01
---
```

### Preserve Technical Terms

Maintain specific terminology:

```text
TERMINOLOGY TO PRESERVE:
- "Docker" → always keep as "Docker"
- "Kubernetes" → always keep as "Kubernetes"
- "API" → always keep as "API"
- "REST" → always keep as "REST"
- "GraphQL" → always keep as "GraphQL"

TRANSLATE BUT ADAPT:
- "container" → translate to target language
- "deployment" → translate to target language
- "configuration" → translate to target language
```

### Brand Consistency

Ensure brand names and products remain consistent:

```text
BRAND NAMES (never translate):
- MyProduct™
- CompanyName®
- FeatureName
- ProductSuite

PRODUCT FEATURES (translate description only):
- "Advanced Analytics" → translate "Advanced" but context matters
- Keep product-specific capitalization
```

## Using Custom Prompts

### CLI Usage

```bash
# Use custom prompt file
mdx run docs output \
  --languages de fr \
  --prompt-path ./custom-prompts/technical.txt
```

### Programmatic Usage

```python
from pathlib import Path
from mdxlate.start_translation import start_translation

# Using custom prompt from file
custom_prompt = Path("./my-prompt.txt").read_text(encoding="utf-8")

# Method 1: Via translation_instruction_text (advanced)
from mdxlate.translator import Translator
from mdxlate.client import make_client
import asyncio

client = make_client(provider="openai", api_key="sk-...")

translator = Translator(
    client=client,
    base_language="en",
    languages=["de", "fr"],
    model="gpt-4o-mini",
    translation_instruction_text=custom_prompt,
)

asyncio.run(translator.translate_directory(
    source_dir=Path("docs"),
    output_dir=Path("output")
))

# Method 2: Via prompt_path (when available)
# Note: start_translation currently doesn't support prompt_path parameter
# Use CLI or Translator class directly
```

## Prompt Best Practices

### 1. Be Specific

❌ Bad:
```text
Translate this markdown.
```

✅ Good:
```text
You are a technical translator.

Translate the markdown content to {target_language}.

Rules:
- Preserve all code blocks
- Keep markdown formatting
- Translate prose only
```

### 2. Use Examples

Show the LLM what you want:

```text
Example Translation:

Input:
---
title: "Getting Started"
---
# Getting Started
Learn the basics.

Output:
---
title: "Erste Schritte"
---
# Erste Schritte
Lernen Sie die Grundlagen.
```

### 3. List Exceptions

Be explicit about what not to translate:

```text
DO NOT TRANSLATE:
- Code in backticks: `code here`
- Function names: myFunction()
- File paths: /path/to/file
- URLs: https://example.com
- Environment variables: $ENV_VAR
```

### 4. Specify Output Format

Tell the LLM exactly what to return:

```text
OUTPUT REQUIREMENTS:
- Return ONLY the translated markdown
- No explanations, no notes, no comments
- Keep exact same structure as input
- Preserve all whitespace and line breaks
```

### 5. Handle Edge Cases

Address specific scenarios:

```text
SPECIAL CASES:

1. Empty lines: preserve as-is
2. HTML comments: keep unchanged
3. Math formulas: preserve LaTeX syntax
4. Tables: translate cell content, keep structure
5. Links: translate link text, keep URL unchanged
```

## Testing Your Prompt

### Quick Test

```bash
# Test with a single file
echo "# Hello World" > test.md
mdx run . output --languages de --prompt-path ./my-prompt.txt
cat output/de/test.md
```

### A/B Testing

Compare different prompts:

```bash
# Test prompt A
mdx run docs output-a --languages de --prompt-path ./prompt-a.txt

# Test prompt B  
mdx run docs output-b --languages de --prompt-path ./prompt-b.txt

# Compare results
diff -r output-a/de output-b/de
```

### Quality Validation

Create a reference translation:

```bash
# Use your custom prompt
mdx run docs output --languages de --prompt-path ./my-prompt.txt

# Review specific files
cat output/de/important.md

# Check technical terms preserved
grep -r "Docker\|Kubernetes" output/de/
```

## Troubleshooting

### Issue: Terms Being Translated Incorrectly

**Solution:** Add explicit preservation rules:

```text
NEVER TRANSLATE:
- Docker → keep as "Docker"
- API → keep as "API"  
- REST → keep as "REST"

List all terms that should remain in English.
```

### Issue: Formatting Lost

**Solution:** Emphasize formatting preservation:

```text
CRITICAL: Preserve markdown formatting exactly.

Examples:
- **bold** stays **bold**
- _italic_ stays _italic_
- # Heading stays # Heading
- [link](url) stays [translated](url)
```

### Issue: Code Blocks Translated

**Solution:** Explicitly exclude code:

```text
NEVER translate content inside:
- ```code blocks```
- `inline code`
- <code> tags

These must remain EXACTLY as written.
```

### Issue: Frontmatter Structure Changed

**Solution:** Provide clear YAML examples:

```text
YAML frontmatter must keep exact structure:

Input:
---
key: "value"
---

Output:
---
key: "translated value"
---

Keys stay in English, only values translate.
```

## Prompt Templates

### Minimal Prompt

```text
Translate the following markdown to {target_language}.
Preserve all formatting, code blocks, and links.
Return only the translated markdown.
```

### Standard Prompt

```text
You are a professional technical translator.

Translate the markdown to {target_language} while:
- Keeping all markdown formatting intact
- Preserving code blocks and inline code unchanged  
- Maintaining YAML frontmatter structure (translate values only)
- Keeping URLs, file paths, and technical terms unchanged

Return only the translated markdown, no explanations.
```

### Comprehensive Prompt

```text
You are a world-class technical translator specializing in software documentation.

GOAL: Translate markdown content to {target_language} with perfect accuracy and cultural appropriateness.

TRANSLATION RULES:
1. Translate all prose content to natural, fluent {target_language}
2. Use industry-standard technical terminology
3. Maintain professional, clear tone
4. Adapt idioms to cultural equivalents

PRESERVE EXACTLY:
- Code blocks (```) and inline code (`)
- URLs and hyperlinks
- File paths and directory structures
- YAML/TOML frontmatter structure
- HTML tags and attributes
- API endpoints and function names
- Environment variables
- Mathematical formulas
- Product and brand names

FORMATTING:
- Keep all markdown syntax identical
- Preserve heading levels (#, ##, ###)
- Maintain list structures (-, *, 1.)
- Keep table structure intact
- Preserve emphasis (**bold**, *italic*)
- Maintain line breaks and spacing

OUTPUT:
- Return ONLY the translated markdown
- No preamble, explanations, or comments
- Match input structure exactly
- Keep encoding as UTF-8

QUALITY:
- Double-check technical accuracy
- Ensure cultural appropriateness
- Verify all formatting preserved
```

## Advanced Customization

### Multi-Language Specific Prompts

Different prompts for different languages:

```bash
# German - formal tone
mdx run docs output --languages de --prompt-path ./prompts/formal-de.txt

# French - casual tone
mdx run docs output --languages fr --prompt-path ./prompts/casual-fr.txt
```

### Dynamic Prompt Generation

Generate prompts programmatically:

```python
from pathlib import Path
from mdxlate.translator import Translator
from mdxlate.client import make_client
import asyncio

def create_prompt(target_lang: str, tone: str = "professional") -> str:
    base = "You are a technical translator.\n\n"
    
    if tone == "professional":
        base += "Use formal, professional language.\n"
    elif tone == "casual":
        base += "Use friendly, conversational language.\n"
    
    base += f"\nTranslate to {target_lang} while preserving markdown formatting."
    return base

client = make_client(provider="openai", api_key="sk-...")

translator = Translator(
    client=client,
    base_language="en",
    languages=["de"],
    model="gpt-4o-mini",
    translation_instruction_text=create_prompt("German", "professional"),
)

asyncio.run(translator.translate_directory(
    source_dir=Path("docs"),
    output_dir=Path("output")
))
```

## See Also

- [CLI Reference](cli.md) - Using `--prompt-path` option
- [Programmatic Usage](programmatic.md) - Custom prompts in Python
- [Jekyll Integration](integrations/jekyll.md) - Frontmatter-specific prompts
