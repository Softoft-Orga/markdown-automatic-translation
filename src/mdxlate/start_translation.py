import asyncio
from pathlib import Path

from mdxlate.client import Provider, make_client
from mdxlate.translator import Translator


def start_translation(
        docs_src: Path,
        out_dir: Path,
        base_language: str,
        languages: list[str],
        model: str = "gpt-4o-mini",
        provider: Provider = "openai",
        api_key: str | None = None,
        base_url: str | None = None,
):
    client = make_client(provider=provider, api_key=api_key, base_url=base_url)
    translator = Translator(
        client=client,
        base_language=base_language,
        languages=languages,
        model=model,
    )
    asyncio.run(translator.translate_directory(docs_src, out_dir))
