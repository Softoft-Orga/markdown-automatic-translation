import asyncio
import json
import time
from pathlib import Path

import pytest

from mdxlate.translator import Translator


@pytest.fixture
def tmp_docs(tmp_path: Path):
    src = tmp_path / "docs"
    out = tmp_path / "out"
    src.mkdir()
    (src / "a.md").write_text("# A\n\nHello world", encoding="utf-8")
    (src / "sub").mkdir()
    (src / "sub" / "b.md").write_text("B text", encoding="utf-8")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("SYSTEM PROMPT", encoding="utf-8")
    return src, out, prompt


@pytest.mark.parametrize("langs", [["de"], ["de", "fr"]])
def test_translate_directory_creates_outputs(tmp_docs, langs):
    src, out, prompt = tmp_docs
    t = Translator(
        client=None,
        base_language="en",
        languages=langs,
        model="test-model",
        prompt_path=prompt,
        max_concurrency=4,
        force_translation=False,
    )

    calls = []

    async def fake_translate(self, content: str, target_lang: str) -> str:
        calls.append(target_lang)
        return f"[{target_lang}] {content}"

    t.translate_text = fake_translate.__get__(t, Translator)

    asyncio.run(t.translate_directory(src, out))

    for lang in langs:
        assert (out / lang / "a.md").exists()
        assert (out / lang / "sub" / "b.md").exists()
        if lang == "en":
            assert (out / "en" / "a.md").read_text(encoding="utf-8").startswith("# A")
        else:
            assert (out / lang / "a.md").read_text(encoding="utf-8").startswith("[")
    assert set(calls) == set([l for l in langs if l != "en"])


def test_hash_skips_when_unchanged(tmp_docs):
    src, out, prompt = tmp_docs
    t = Translator(
        client=None,
        base_language="en",
        languages=["de", "fr"],
        model="m1",
        prompt_path=prompt,
        max_concurrency=2,
        force_translation=False,
    )

    calls = {"n": 0}

    async def fake_translate(self, content: str, target_lang: str) -> str:
        calls["n"] += 1
        return f"[{target_lang}] {content}"

    t.translate_text = fake_translate.__get__(t, Translator)

    asyncio.run(t.translate_directory(src, out))
    first_n = calls["n"]

    time.sleep(0.01)
    asyncio.run(t.translate_directory(src, out))
    second_n = calls["n"] - first_n
    assert first_n > 0
    assert second_n == 0


def test_force_retranslates(tmp_docs):
    src, out, prompt = tmp_docs
    t1 = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="m1",
        prompt_path=prompt,
        max_concurrency=1,
        force_translation=False,
    )

    async def fake1(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] v1 {content}"

    t1.translate_text = fake1.__get__(t1, Translator)
    asyncio.run(t1.translate_directory(src, out))
    v1 = (out / "de" / "a.md").read_text(encoding="utf-8")

    t2 = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="m1",
        prompt_path=prompt,
        max_concurrency=1,
        force_translation=True,
    )

    async def fake2(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] v2 {content}"

    t2.translate_text = fake2.__get__(t2, Translator)
    asyncio.run(t2.translate_directory(src, out))
    v2 = (out / "de" / "a.md").read_text(encoding="utf-8")
    assert v1 != v2


def test_state_file_structure(tmp_docs):
    src, out, prompt = tmp_docs
    t = Translator(
        client=None,
        base_language="en",
        languages=["de", "fr"],
        model="m1",
        prompt_path=prompt,
        max_concurrency=1,
        force_translation=False,
    )

    async def fake(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] {content}"

    t.translate_text = fake.__get__(t, Translator)
    asyncio.run(t.translate_directory(src, out))

    state_path = src / ".mdxlate.hashes.json"
    assert state_path.exists()
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert "de" in data and "fr" in data
    assert "a.md" in "".join(data["de"].keys())
