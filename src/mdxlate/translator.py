from __future__ import annotations

import asyncio
from pathlib import Path

import tenacity
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, \
    ChatCompletionUserMessageParam
from tenacity import stop_after_attempt, wait_exponential

from mdxlate.cache import TranslationCache


def default_translation_instruction_path() -> Path:
    return Path(__file__).parent / "translation_instruction.txt"


def read_default_translation_instruction() -> str:
    p = default_translation_instruction_path()
    return p.read_text(encoding="utf-8")


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
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=self.translation_instruction),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=f"Translate the following markdown to {target_language}:\n\n{content}")],
            temperature=0.2
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

    async def process_file(self, file_path: Path, source_root: Path, output_dir: Path, cache: TranslationCache) -> None:
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
            await asyncio.gather(*tasks)

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
        cache_root = self.cache_dir if self.cache_dir is not None else source_dir
        cache = TranslationCache(cache_root)
        cache.load()
        tasks: list[asyncio.Task] = []
        for md_file in source_dir.rglob("*.md"):
            tasks.append(asyncio.create_task(self.process_file(md_file, source_dir, output_dir, cache)))
        if tasks:
            await asyncio.gather(*tasks)
        cache.save()
        self.clean_up_unused_files(output_dir)
