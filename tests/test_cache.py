import json
from pathlib import Path

from mdxlate.cache import STATE_FILE_NAME, TranslationCache


def test_state_path_uses_custom_name(tmp_path):
    cache = TranslationCache(tmp_path, "custom.json")

    assert cache.state_path() == tmp_path / "custom.json"


def test_load_existing_file_overwrites_state(tmp_path):
    data = {"de": {"doc.md": "hash"}}
    state_file = tmp_path / STATE_FILE_NAME
    state_file.write_text(json.dumps(data), encoding="utf-8")

    cache = TranslationCache(tmp_path)
    cache.state = {"other": {"file": "old"}}

    cache.load()

    assert cache.state == data


def test_load_missing_file_resets_state(tmp_path):
    cache = TranslationCache(tmp_path)
    cache.state = {"de": {"doc.md": "hash"}}

    cache.load()

    assert cache.state == {}


def test_save_persists_state_to_json(tmp_path):
    cache = TranslationCache(tmp_path)
    cache.state = {"de": {"doc.md": "hash"}, "fr": {}}

    cache.save()

    saved = json.loads((tmp_path / STATE_FILE_NAME).read_text(encoding="utf-8"))
    assert saved == cache.state


def test_calc_key_normalizes_paths_and_depends_on_inputs(tmp_path):
    cache = TranslationCache(tmp_path)
    file_bytes = b"content"
    prompt = "prompt"
    model = "model"

    key_posix = cache.calc_key(Path("dir/file.md"), "de", file_bytes, prompt, model)
    key_windows = cache.calc_key(Path("dir\\file.md"), "de", file_bytes, prompt, model)

    assert key_posix == key_windows

    key_different_bytes = cache.calc_key(Path("dir/file.md"), "de", b"other", prompt, model)
    key_different_prompt = cache.calc_key(Path("dir/file.md"), "de", file_bytes, "different", model)

    assert key_different_bytes != key_posix
    assert key_different_prompt != key_posix


def test_mark_and_is_up_to_date(tmp_path):
    cache = TranslationCache(tmp_path)
    rel = Path("sub") / "doc.md"
    key = "abc123"

    cache.mark(rel, "de", key)

    assert "de" in cache.state
    # State should use normalized (forward slash) paths
    cached_hash = cache.state["de"].get(str(rel).replace("\\", "/"))
    assert cached_hash == key
    assert cache.is_up_to_date(rel, "de", key)
    assert not cache.is_up_to_date(rel, "fr", key)
    assert not cache.is_up_to_date(Path("other.md"), "de", key)


def test_mark_and_is_up_to_date_with_different_path_styles(tmp_path):
    """Test that path normalization works consistently across different path styles."""
    cache = TranslationCache(tmp_path)
    file_bytes = b"content"
    prompt = "prompt"
    model = "model"

    # Use Windows-style path
    rel_windows = Path(r"dir\file.md")

    # Calculate key and mark with Windows-style path
    key = cache.calc_key(rel_windows, "de", file_bytes, prompt, model)
    cache.mark(rel_windows, "de", key)

    # Should find the cache entry with POSIX-style path
    rel_posix = Path("dir/file.md")
    key_posix = cache.calc_key(rel_posix, "de", file_bytes, prompt, model)

    # Keys should be the same (already tested in test_calc_key_normalizes_paths_and_depends_on_inputs)
    assert key == key_posix

    # CRITICAL: is_up_to_date should return True regardless of path style used
    assert cache.is_up_to_date(rel_posix, "de", key_posix), \
        "Cache should find entry marked with Windows path when checking with POSIX path"
    assert cache.is_up_to_date(rel_windows, "de", key), \
        "Cache should find entry marked with Windows path when checking with Windows path"
