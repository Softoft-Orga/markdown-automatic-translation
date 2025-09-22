import asyncio
import hashlib
import json
from pathlib import Path

import tenacity
from openai import AsyncOpenAI
from tenacity import stop_after_attempt, wait_exponential

DEFAULT_HOME_DIR = Path.home() / ".mdxlate"
DEFAULT_PROMPT_PATH = DEFAULT_HOME_DIR / "translation_instruction.txt"
STATE_FILE_NAME = ".mdxlate.hashes.json"


def ensure_user_prompt() -> Path:
    DEFAULT_HOME_DIR.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_PROMPT_PATH.exists():
        pkg_prompt = Path(__file__).parent / "translation_instruction.txt"
        DEFAULT_PROMPT_PATH.write_text(pkg_prompt.read_text(encoding="utf-8"), encoding="utf-8")
    return DEFAULT_PROMPT_PATH


def _sha_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _state_path(root: Path) -> Path:
    return root / STATE_FILE_NAME


def _load_state(root: Path) -> dict:
    p = _state_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _save_state(root: Path, state: dict) -> None:
    _state_path(root).write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


class Translator:
    def __init__(self, client: AsyncOpenAI, base_language: str, languages: list[str], model: str,
                 prompt_path: Path | None = None, max_concurrency: int = 8, force_translation: bool = False) -> None:
        self.client = client
        self.base_language = base_language
        self.languages = languages
        self.model = model
        self.translation_instruction = (prompt_path or ensure_user_prompt()).read_text(encoding="utf-8").strip()
        self.used_file_paths: set[str] = set()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.force_translation = force_translation

    def _calc_key(self, rel: Path, lang: str, file_bytes: bytes) -> str:
        file_hash = _sha_bytes(file_bytes)
        cfg_hash = _sha_str("|".join([self.translation_instruction, self.model, lang]))
        return _sha_str("|".join([str(rel).replace("\\", "/"), file_hash, cfg_hash]))

    @tenacity.retry(wait=wait_exponential(multiplier=2, min=2, max=60), stop=stop_after_attempt(6))
    async def translate_text(self, content: str, target_lang: str) -> str:
        r = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.translation_instruction},
                {"role": "user", "content": f"Translate the following markdown to {target_lang}:\n\n{content}"},
            ],
            temperature=0.2,
        )
        return r.choices[0].message.content or ""

    def _mark_used(self, out_dir: Path, rel: Path) -> None:
        for lang in self.languages:
            self.used_file_paths.add(str(out_dir / lang / rel))

    async def _write_one(self, lang: str, text: str, rel: Path, out_dir: Path) -> None:
        async with self.semaphore:
            t = text if lang == self.base_language else await self.translate_text(text, lang)
            out_file = out_dir / lang / rel
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(t, encoding="utf-8")
            print(out_file)

    async def process_file(self, path: Path, root: Path, out_dir: Path, state: dict) -> None:
        rel = path.relative_to(root)
        self._mark_used(out_dir, rel)
        b = path.read_bytes()
        text = b.decode()
        tasks: list[asyncio.Task] = []
        for lang in self.languages:
            key = self._calc_key(rel, lang, b)
            if not self.force_translation and state.get(lang, {}).get(str(rel)) == key:
                continue
            tasks.append(asyncio.create_task(self._write_one(lang, text, rel, out_dir)))
            state.setdefault(lang, {})[str(rel)] = key
        if tasks:
            await asyncio.gather(*tasks)

    def clean_up_unused_files(self, out_dir: Path) -> None:
        for lang in self.languages:
            p = out_dir / lang
            if not p.exists():
                continue
            for f in p.rglob("*.md"):
                if str(f) not in self.used_file_paths and f.is_file():
                    f.unlink()
            for d in reversed(list(p.rglob("*"))):
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()

    async def translate_directory(self, docs_src: Path, out_dir: Path) -> None:
        state = _load_state(docs_src)
        tasks: list[asyncio.Task] = []
        for md_file in docs_src.rglob("*.md"):
            tasks.append(asyncio.create_task(self.process_file(md_file, docs_src, out_dir, state)))
        if tasks:
            await asyncio.gather(*tasks)
        _save_state(docs_src, state)
        self.clean_up_unused_files(out_dir)
