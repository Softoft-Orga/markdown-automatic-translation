import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _retry_stub(*args, **kwargs):
    def decorator(func):
        return func

    return decorator


tenacity_stub = ModuleType("tenacity")
tenacity_stub.retry = _retry_stub
tenacity_stub.wait_exponential = lambda *args, **kwargs: None
tenacity_stub.stop_after_attempt = lambda *args, **kwargs: None

sys.modules.setdefault("tenacity", tenacity_stub)


openai_stub = ModuleType("openai")


class _AsyncOpenAI:
    def __init__(self, api_key=None, base_url=None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        for key, value in kwargs.items():
            setattr(self, key, value)


openai_stub.AsyncOpenAI = _AsyncOpenAI

openai_types_stub = ModuleType("openai.types")
openai_types_chat_stub = ModuleType("openai.types.chat")


class _ChatMessageParam:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


openai_types_chat_stub.ChatCompletionSystemMessageParam = _ChatMessageParam
openai_types_chat_stub.ChatCompletionUserMessageParam = _ChatMessageParam
openai_types_stub.chat = openai_types_chat_stub
openai_stub.types = openai_types_stub

sys.modules.setdefault("openai", openai_stub)
sys.modules.setdefault("openai.types", openai_types_stub)
sys.modules.setdefault("openai.types.chat", openai_types_chat_stub)
