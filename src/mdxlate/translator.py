from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import tenacity
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from tenacity import stop_after_attempt, wait_exponential

from mdxlate.cache import TranslationCache

logger = logging.getLogger(__name__)


def read_default_translation_instruction() -> str:
    return """
    You are a world-class technical translator with deep expertise in both Python software and VitePress Markdown documentation. Your task is to translate the provided Markdown file into the target language with extreme precision.

Your translations will be read by other developers, so technical accuracy and the use of standard, idiomatic terminology are paramount.

---

### PRIMARY DIRECTIVE
Return **ONLY** the fully translated Markdown file content. Do not add any commentary, explanations, or notes before or after the content. Your output must be the raw, translated text, ready to be saved directly into a `.md` file.

---

### CATEGORY 1: UNTOUCHABLE ELEMENTS (DO NOT TRANSLATE OR ALTER)
These elements MUST remain 100% identical to the source.

1.  **Code Blocks & Inline Code:**
    * All fenced code blocks (```...```) and indented code blocks must be preserved exactly.
    * All inline code snippets (`like_this`) are not to be translated.
    * Programming language keywords, variable names, function names, parameters, and class names are a universal language for developers and **must never be translated**.

2.  **URLs, File Paths, and Placeholders:**
    * Absolute and relative URLs (`/guides/getting-started.html`).
    * File paths (`./src/components/MyComponent.vue`).
    * Template placeholders or component slots like `{{ variable }}`, `{% raw %}{% endraw %}`, or `{content}`.

3.  **HTML/Vue Components:**
    * All HTML tags (`<div>`, `<p>`, `<img>`) and custom Vue components (`<CustomCard>`, `<CodeGroup>`).
    * All attributes and their values (`class="custom-class"`, `src="..."`, `:dark="true"`).

---

### CATEGORY 2: STRUCTURAL ELEMENTS (PRESERVE STRUCTURE, TRANSLATE TEXT)
For these elements, you must translate the visible text content while keeping the surrounding syntax intact.

1.  **YAML Frontmatter:**
    * Preserve the `---` delimiters.
    * **Do not** translate the keys (e.g., `layout`, `title`, `description`, `hero`).
    * Translate **only** the string values associated with the keys (e.g., `tagline: "Translate this text."`).

2.  **Markdown Syntax:**
    * Heading levels (`#`, `##`) must be preserved. Translate only the heading text.
    * Lists, blockquotes, and tables must maintain their structure. Translate only the text within them.

---

### CATEGORY 3: CONTENT TRANSLATION RULES
These rules apply to all general text content that is eligible for translation.

1.  **Reserved Technical Keywords (Keep in English):**
    * The following terms must remain in English, even when they appear in regular sentences, to maintain technical consistency.
    * **Glossary:** `class`, `def`, `async`, `await`, `client`, `model`, `import`, `script setup`, `layout`, `VitePress`, `YAML`, `Markdown`, `Docker`, `API`, `REST`, `JSON`, `HTML`, `CSS`, `JavaScript`, `TypeScript`, `Vue`, `Python`, `FastAPI`, `Flask`.
    * *Example*: "This Python `class` is part of the API." → "Diese Python-`class` ist Teil der API."

2.  **Style and Tone:**
    * Maintain a clear, concise, and professional tone suitable for technical documentation.
    * Use industry-standard terminology for the target language (e.g., for German, "Repository" is better than "Ablage").
    * Follow the capitalization rules of the target language, but preserve original capitalization for acronyms (e.g., `JSON`, `REST`) and the keywords in the glossary.

---

### FINAL CHECK
Before finalizing your response, ensure you have followed the **Primary Directive**. The output must be free of any extra text or Markdown code fences.
"""


def write_default_translation_instruction(dest: Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(read_default_translation_instruction(), encoding="utf-8")
    return dest


class Translator:
    def __init__(
            self,
            client: AsyncOpenAI,
            base_language: str,
            languages: list[str],
            model: str,
            translation_instruction_text: str | None = None,
            translation_instruction_path: Path | None = None,
            max_concurrency: int = 8,
            force_translation: bool = False,
            cache_dir: Path | None = None,
    ) -> None:
        self.client = client
        self.base_language = base_language
        self.languages = languages
        self.model = model
        if translation_instruction_text is not None:
            self.translation_instruction = translation_instruction_text.strip()
        elif translation_instruction_path is not None:
            self.translation_instruction = Path(translation_instruction_path).read_text(encoding="utf-8").strip()
        else:
            self.translation_instruction = read_default_translation_instruction().strip()
        self.used_output_paths: set[str] = set()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.force_translation = force_translation
        self.cache_dir = cache_dir

    @tenacity.retry(wait=wait_exponential(multiplier=2, min=2, max=60), stop=stop_after_attempt(6))
    async def translate_text(self, content: str, target_language: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                ChatCompletionSystemMessageParam(role="system", content=self.translation_instruction),
                ChatCompletionUserMessageParam(
                    role="user", content=f"Translate the following markdown to {target_language}:\n\n{content}"
                ),
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content or ""

    def _mark_used(self, output_dir: Path, relative_path: Path) -> None:
        for lang in self.languages:
            p = (output_dir / lang / relative_path).resolve()
            self.used_output_paths.add(p.as_posix())

    async def _write_one(self, lang: str, text: str, relative_path: Path, output_dir: Path) -> None:
        async with self.semaphore:
            translated = text if lang == self.base_language else await self.translate_text(text, lang)
            out_file = output_dir / lang / relative_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(translated, encoding="utf-8")
            print(out_file)

    async def process_file(self, file_path: Path, source_root: Path, output_dir: Path,
                           cache: TranslationCache) -> None | Exception:
        """
        Process a single file, translating it to all configured languages.
        
        Returns None on success, or an Exception if the file processing failed.
        """
        try:
            relative_path = file_path.relative_to(source_root)
            self._mark_used(output_dir, relative_path)
            file_bytes = file_path.read_bytes()
            text = file_bytes.decode()
            tasks: list[asyncio.Task] = []
            for lang in self.languages:
                key = cache.calc_key(
                    rel=relative_path,
                    lang=lang,
                    file_bytes=file_bytes,
                    prompt=self.translation_instruction,
                    model=self.model,
                )
                if not self.force_translation and cache.is_up_to_date(rel=relative_path, lang=lang, key=key):
                    continue
                tasks.append(asyncio.create_task(self._write_one(lang, text, relative_path, output_dir)))
                cache.mark(rel=relative_path, lang=lang, key=key)
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Check if any translation failed
                for result in results:
                    if isinstance(result, Exception):
                        raise result
            return None
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return e

    def clean_up_unused_files(self, output_dir: Path) -> None:
        for lang in self.languages:
            lang_dir = output_dir / lang
            if not lang_dir.exists():
                continue
            for f in lang_dir.rglob("*.md"):
                if f.as_posix() not in self.used_output_paths and f.is_file():
                    f.unlink()
            for d in reversed(list(lang_dir.rglob("*"))):
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()

    async def translate_directory(self, source_dir: Path, output_dir: Path) -> None:
        """
        Translate all markdown files from source_dir to output_dir for configured languages.

        Validates that source and output directories don't overlap to prevent recursive translation.
        Uses robust error handling to process all files even if some fail.
        

        Args:
            source_dir: Directory containing source markdown files
            output_dir: Directory where translated files will be written

        Raises:
            ValueError: If source and output directories overlap (same, parent-child relationship)
        """
        # Validate that source and output directories don't overlap
        source_resolved = source_dir.resolve()
        output_resolved = output_dir.resolve()

        # Check if directories are the same
        if source_resolved == output_resolved:
            raise ValueError(
                f"Invalid directory configuration: source and output directories are the same ('{source_dir}'). "
                f"This would cause recursive translation. Please use non-overlapping directories."
            )

        # Check if source is inside output
        try:
            source_resolved.relative_to(output_resolved)
            # If relative_to succeeds, source is inside output
            raise ValueError(
                f"Invalid directory configuration: source directory '{source_dir}' is inside output directory '{output_dir}'. "
                f"This would cause recursive translation. Please use non-overlapping directories."
            )
        except ValueError as e:
            # If the error message contains our custom message, re-raise it
            if "Invalid directory configuration" in str(e):
                raise
            # Otherwise, it's from relative_to failing, which is expected - continue

        # Check if output is inside source
        try:
            output_resolved.relative_to(source_resolved)
            # If relative_to succeeds, output is inside source
            raise ValueError(
                f"Invalid directory configuration: output directory '{output_dir}' is inside source directory '{source_dir}'. "
                f"This would cause recursive translation. Please use non-overlapping directories."
            )
        except ValueError as e:
            # If the error message contains our custom message, re-raise it
            if "Invalid directory configuration" in str(e):
                raise
            # Otherwise, it's from relative_to failing, which is expected - continue

        cache_root = self.cache_dir if self.cache_dir is not None else source_dir
        cache = TranslationCache(cache_root)
        cache.load()

        # Collect all markdown files
        md_files = list(source_dir.rglob("*.md"))
        tasks: list[asyncio.Task] = []
        for md_file in md_files:
            tasks.append(asyncio.create_task(self.process_file(md_file, source_dir, output_dir, cache)))

        # Process all files, collecting exceptions instead of failing
        failures = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    md_file = md_files[i]
                    relative_path = md_file.relative_to(source_dir)
                    failures.append({
                        "file": str(relative_path),
                        "error": str(result),
                        "error_type": type(result).__name__
                    })
                    logger.error(f"Translation failed for {relative_path}: {result}")

        # Save cache even if some files failed
        cache.save()

        # Generate failure report if there were any failures
        if failures:
            failure_report_path = cache_root / ".mdxlate.failures.json"
            failure_report_path.write_text(
                json.dumps({"failures": failures}, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            logger.warning(f"Translation completed with {len(failures)} failure(s). See {failure_report_path}")
        else:
            # Remove failure report if it exists from previous runs
            failure_report_path = cache_root / ".mdxlate.failures.json"
            if failure_report_path.exists():
                failure_report_path.unlink()

        self.clean_up_unused_files(output_dir)
