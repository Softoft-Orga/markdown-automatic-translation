import os
from pathlib import Path

from mdxlate.start_translation import start_translation

if __name__ == '__main__':
    start_translation(
        docs_src=Path("../data/test-markdown/en"),
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
        out_dir=Path("../data/test-markdown"),
        base_language="en",
        languages=["de", "fr"],
        provider="openrouter",
        model="google/gemini-2.5-pro",
    )
