import asyncio
import json
import sys
from pathlib import Path

# Ensure local src/ is importable before any mdxlate imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from mdxlate.translator import Translator


def test_start_translation_is_in_correct_module():
    """Verify start_translation is only in start_translation module, not in cli."""
    from mdxlate import cli
    from mdxlate import start_translation
    
    # Should exist in start_translation module
    assert hasattr(start_translation, 'start_translation')
    
    # Should NOT exist in cli module
    assert not hasattr(cli, 'start_translation')


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
        translation_instruction_text="SYSTEM PROMPT",
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


def test_translate_directory_rejects_source_inside_output(tmp_path: Path):
    """Test that translation fails when source directory is inside output directory."""
    out = tmp_path / "translations"
    src = out / "en"
    src.mkdir(parents=True)
    (src / "test.md").write_text("# Test", encoding="utf-8")
    
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )
    
    with pytest.raises(ValueError, match="source directory .* is inside output directory"):
        asyncio.run(translator.translate_directory(src, out))


def test_cache_dir_writes_to_custom_location(sample_docs, tmp_path):
    src, out = sample_docs
    cache_location = tmp_path / "custom_cache"
    cache_location.mkdir()

    translator = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
        max_concurrency=1,
        force_translation=False,
        cache_dir=cache_location,
    )
    
    async def fake_translate(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] {content}"
    
    translator.translate_text = fake_translate.__get__(translator, Translator)
    asyncio.run(translator.translate_directory(src, out))

    from mdxlate.cache import STATE_FILE_NAME

    # Cache should be in custom location, not source
    assert (cache_location / STATE_FILE_NAME).exists()
    assert not (src / STATE_FILE_NAME).exists()


def test_translate_directory_rejects_output_inside_source(tmp_path: Path):
    """Test that translation fails when output directory is inside source directory."""
    src = tmp_path / "docs"
    out = src / "translations"
    src.mkdir()
    (src / "test.md").write_text("# Test", encoding="utf-8")
    
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )
    
    with pytest.raises(ValueError, match="output directory .* is inside source directory"):
        asyncio.run(translator.translate_directory(src, out))


def test_translate_directory_allows_sibling_directories(tmp_path: Path):
    """Test that translation works when source and output are sibling directories."""
    src = tmp_path / "docs"
    out = tmp_path / "translations"
    src.mkdir()
    (src / "test.md").write_text("# Test", encoding="utf-8")
    
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )

    async def fake_translate(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] {content}"

    translator.translate_text = fake_translate.__get__(translator, Translator)
    asyncio.run(translator.translate_directory(src, out))

    # Should not raise an error and should create output
    assert (out / "de" / "test.md").exists()


def test_cache_dir_defaults_to_source_dir(sample_docs):
    src, out = sample_docs
    
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )
    
    async def fake(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] {content}"
    
    translator.translate_text = fake.__get__(translator, Translator)
    
    # Should not raise an error
    asyncio.run(translator.translate_directory(src, out))
    
    assert (out / "de" / "a.md").exists()
    
    from mdxlate.cache import STATE_FILE_NAME
    
    # Cache should default to source directory
    assert (src / STATE_FILE_NAME).exists()


def test_translate_directory_rejects_same_directory(tmp_path: Path):
    """Test that translation fails when source and output are the same directory."""
    src = tmp_path / "docs"
    src.mkdir()
    (src / "test.md").write_text("# Test", encoding="utf-8")
    
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )
    
    # Using the same directory for both source and output should fail
    with pytest.raises(ValueError, match="source and output directories are the same"):
        asyncio.run(translator.translate_directory(src, src))


def test_translate_directory_handles_translation_failures(sample_docs):
    """Test that translation continues when some files fail and generates a failure report."""
    src, out = sample_docs
    
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de", "fr"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )
    
    # Make translation fail for one specific file
    async def fake_translate_with_failure(self, content: str, target_lang: str) -> str:
        if "Sub page" in content:
            raise RuntimeError("Simulated translation failure")
        return f"[{target_lang}] {content}"
    
    translator.translate_text = fake_translate_with_failure.__get__(translator, Translator)
    
    # Should not raise an exception even though one file fails
    asyncio.run(translator.translate_directory(src, out))
    
    # Successful file should be translated
    assert (out / "de" / "a.md").exists()
    assert (out / "fr" / "a.md").exists()
    
    # Failed file should not exist (or be incomplete)
    # The file might exist but won't be complete - the important thing is the process continues
    
    # Failure report should exist
    from mdxlate.cache import STATE_FILE_NAME
    failure_report = src / ".mdxlate.failures.json"
    assert failure_report.exists()
    
    # Check failure report content
    failures_data = json.loads(failure_report.read_text(encoding="utf-8"))
    assert "failures" in failures_data
    assert len(failures_data["failures"]) > 0
    
    # Check that the failed file is in the report
    failed_files = [f["file"] for f in failures_data["failures"]]
    assert any("b.md" in f for f in failed_files)


def test_translate_directory_removes_failure_report_on_success(sample_docs):
    """Test that failure report is removed when all translations succeed."""
    src, out = sample_docs
    
    # First, create a failure report
    failure_report = src / ".mdxlate.failures.json"
    failure_report.write_text('{"failures": [{"file": "test.md", "error": "test"}]}', encoding="utf-8")
    
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )
    
    async def fake_translate(self, content: str, target_lang: str) -> str:
        return f"[{target_lang}] {content}"
    
    translator.translate_text = fake_translate.__get__(translator, Translator)
    
    # Run translation successfully
    asyncio.run(translator.translate_directory(src, out))
    
    # Failure report should be removed
    assert not failure_report.exists()


def test_translate_directory_saves_cache_despite_failures(sample_docs):
    """Test that cache is saved even when some files fail."""
    src, out = sample_docs
    
    translator = Translator(
        client=None,
        base_language="en",
        languages=["de"],
        model="test-model",
        translation_instruction_text="SYSTEM PROMPT",
    )
    
    # Make translation fail for one file but succeed for another
    async def fake_translate_with_partial_failure(self, content: str, target_lang: str) -> str:
        if "Sub page" in content:
            raise RuntimeError("Simulated translation failure")
        return f"[{target_lang}] {content}"
    
    translator.translate_text = fake_translate_with_partial_failure.__get__(translator, Translator)
    
    # Run translation
    asyncio.run(translator.translate_directory(src, out))
    
    # Cache should still be saved
    from mdxlate.cache import STATE_FILE_NAME
    cache_file = src / STATE_FILE_NAME
    assert cache_file.exists()
    
    # Cache should contain entry for successful translation
    cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert "de" in cache_data
    assert any("a.md" in key for key in cache_data["de"].keys())

