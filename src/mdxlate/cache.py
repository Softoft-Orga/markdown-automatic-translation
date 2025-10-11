from __future__ import annotations

import hashlib
import json
from pathlib import Path

STATE_FILE_NAME = ".mdxlate.hashes.json"


class TranslationCache:
    def __init__(self, root: Path, state_file_name: str = STATE_FILE_NAME) -> None:
        self.root = root
        self.state_file_name = state_file_name
        self.state: dict[str, dict[str, str]] = {}

    def state_path(self) -> Path:
        return self.root / self.state_file_name

    def load(self) -> None:
        if self.state_path().exists():
            self.state = json.loads(self.state_path().read_text(encoding="utf-8"))
        else:
            self.state = {}

    def save(self) -> None:
        self.state_path().write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

    def _sha_str(self, s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()

    def _sha_bytes(self, b: bytes) -> str:
        return hashlib.sha256(b).hexdigest()

    def _normalize_path(self, rel: Path) -> str:
        """Normalize to POSIX format for cross-platform cache keys."""
        return str(rel).replace("\\", "/")

    def calc_key(self, rel: Path, lang: str, file_bytes: bytes, prompt: str, model: str) -> str:
        file_hash = self._sha_bytes(file_bytes)
        cfg_hash = self._sha_str("|".join([prompt, model, lang]))
        return self._sha_str("|".join([self._normalize_path(rel), file_hash, cfg_hash]))

    def is_up_to_date(self, rel: Path, lang: str, key: str) -> bool:
        return self.state.get(lang, {}).get(self._normalize_path(rel)) == key

    def mark(self, rel: Path, lang: str, key: str) -> None:
        self.state.setdefault(lang, {})[self._normalize_path(rel)] = key
