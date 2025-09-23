import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mdxlate.translator import Translator


@pytest.fixture
def sample_docs(tmp_path: Path):
    src = tmp_path / "docs"
    out = tmp_path / "out"
    src.mkdir()
    (src / "a.md").write_text("# A\n\nHello world", encoding="utf-8")
    (src / "sub").mkdir()
    (src / "sub" / "b.md").write_text("Sub page", encoding="utf-8")
    return src, out


@pytest.mark.parametrize("languages", [["en", "de"], ["en", "de", "fr"]])
def test_translate_directory_writes_expected_files(sample_docs, languages):
    src, out = sample_docs
    translator = Translator(
        client=None,
        base_language="en",
        languages=languages,
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
        max_concurrency=4,
        force_translation=False,
    )

    calls: list[str] = []

    async def fake_translate(self, content: str, target_lang: str) -> str:
        calls.append(target_lang)
        return f"[{target_lang}] {content}"

    translator.translate_text = fake_translate.__get__(translator, Translator)

    asyncio.run(translator.translate_directory(src, out))

    for lang in languages:
        assert (out / lang / "a.md").exists()
        assert (out / lang / "sub" / "b.md").exists()

    base_content = (out / "en" / "a.md").read_text(encoding="utf-8")
    assert base_content.startswith("# A")

    assert set(calls) == {lang for lang in languages if lang != "en"}


def test_translate_directory_uses_cache(sample_docs):
    src, out = sample_docs
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de", "fr"],
        model="m1",
        translation_instruction_path=prompt,
        max_concurrency=2,
        force_translation=False,
    )

    call_count = {"n": 0}

    async def fake_translate(self, content: str, target_lang: str) -> str:
        call_count["n"] += 1
        return f"[{target_lang}] {content}"

    translator.translate_text = fake_translate.__get__(translator, Translator)

    asyncio.run(translator.translate_directory(src, out))
    first_run_calls = call_count["n"]

    asyncio.run(translator.translate_directory(src, out))
    second_run_calls = call_count["n"] - first_run_calls

    assert first_run_calls > 0
    assert second_run_calls == 0


def test_force_translation_bypasses_cache(sample_docs):
    src, out = sample_docs
    translator = Translator(
        client=None,
        base_language="en",
        languages=["en", "de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
        max_concurrency=1,
        force_translation=False,
    )

    async def fake_v1(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] v1 {content}"

    translator.translate_text = fake_v1.__get__(translator, Translator)
    asyncio.run(translator.translate_directory(src, out))

    first_output = (out / "de" / "a.md").read_text(encoding="utf-8")

    translator_force = Translator(
        client=None,
        base_language="en",
        languages=["en", "de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
        max_concurrency=1,
        force_translation=True,
    )

    async def fake_v2(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] v2 {content}"

    translator_force.translate_text = fake_v2.__get__(translator_force, Translator)
    asyncio.run(translator_force.translate_directory(src, out))

    second_output = (out / "de" / "a.md").read_text(encoding="utf-8")
    assert first_output != second_output


def test_cleanup_removes_stale_outputs(sample_docs):
    src, out = sample_docs
    translator = Translator(
        client=None,
        base_language="en",
        languages=["en", "de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
        max_concurrency=1,
        force_translation=False,
    )

    async def fake(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] {content}"

    translator.translate_text = fake.__get__(translator, Translator)
    asyncio.run(translator.translate_directory(src, out))

    (src / "sub" / "b.md").unlink()

    translator_cleanup = Translator(
        client=None,
        base_language="en",
        languages=["en", "de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
        max_concurrency=1,
        force_translation=False,
    )

    translator_cleanup.translate_text = fake.__get__(translator_cleanup, Translator)
    asyncio.run(translator_cleanup.translate_directory(src, out))

    assert not (out / "en" / "sub" / "b.md").exists()
    assert not (out / "de" / "sub" / "b.md").exists()
    assert not (out / "en" / "sub").exists()
    assert not (out / "de" / "sub").exists()


def test_state_file_contains_language_entries(sample_docs):
    src, out = sample_docs
    translator = Translator(
        client=None,
        base_language="en",
        languages=["en", "de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
        max_concurrency=1,
        force_translation=False,
    )

    async def fake(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] {content}"

    translator.translate_text = fake.__get__(translator, Translator)
    asyncio.run(translator.translate_directory(src, out))

    state_path = src / ".mdxlate.hashes.json"
    assert state_path.exists()
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert "en" in data and "de" in data
    assert "a.md" in "".join(data["en"].keys())
