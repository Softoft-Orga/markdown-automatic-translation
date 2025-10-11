from __future__ import annotations

import os
from typing import Literal

from openai import AsyncOpenAI

Provider = Literal["openai", "openrouter"]


def make_client(
    provider: Provider = "openai",
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncOpenAI:
    if provider == "openrouter":
        api_key = api_key or os.getenv("OPEN_ROUTER_API_KEY")
        base_url = base_url or "https://openrouter.ai/api/v1"
        return AsyncOpenAI(api_key=api_key, base_url=base_url)
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    return AsyncOpenAI(api_key=api_key, base_url=base_url)
