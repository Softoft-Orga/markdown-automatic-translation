def start_translation(
        docs_src: Path,
        out_dir: Path,
        base_language: str,
        languages: list[str],
        model: str = "gpt-4o-mini",
        provider: Provider = "openai",
        api_key: str | None = None,
        base_url: str | None = None,
        prompt_path: Path | None = None,
):
    client = make_client(provider=provider, api_key=api_key, base_url=base_url)
    translator = Translator(
        client=client,
        base_language=base_language,
        languages=languages,
        model=model,
        prompt_path=prompt_path or DEFAULT_PROMPT_PATH,
    )
    asyncio.run(translator.translate_directory(docs_src, out_dir))
