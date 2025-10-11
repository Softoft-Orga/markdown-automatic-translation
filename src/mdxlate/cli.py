from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer

from .client import make_client, Provider
from .translator import Translator

app = typer.Typer(add_completion=False)


@app.command()
def init(
    prompt_path: Path = typer.Option(
        Path.home() / ".mdxlate" / "translation_instruction.txt",
        help="Path for editable prompt template"
    )
) -> None:
    """Initialize editable translation prompt file."""
    from .translator import write_default_translation_instruction
    result = write_default_translation_instruction(prompt_path)
    typer.echo(f"✓ Created prompt template at: {result}")
    typer.echo(f"\nEdit this file to customize translations.")
    typer.echo(f"Use: mdx run ... --prompt-path {result}")


@app.command()
def run(
        docs_src: Path = typer.Argument(),
        out_dir: Path = typer.Argument(),
        base_language: str = typer.Option("en"),
        languages: list[str] = typer.Option(["de"]),
        model: str = typer.Option("gpt-4o-mini"),
        provider: Provider = typer.Option("openai"),
        api_key: str | None = typer.Option(None),
        api_env_key: str = typer.Option("OPENAI_API_KEY"),
        base_url: str | None = typer.Option(None),
        cache_dir: Path | None = typer.Option(None, help="Directory for cache file (defaults to source directory)"),
) -> None:
    api_key = api_key or os.getenv(api_env_key)
    client = make_client(provider=provider, api_key=api_key, base_url=base_url)
    translator = Translator(
        client=client,
        base_language=base_language,
        languages=languages,
        model=model,
        cache_dir=cache_dir,
    )
    asyncio.run(translator.translate_directory(docs_src, out_dir))
