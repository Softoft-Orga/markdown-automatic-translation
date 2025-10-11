import os
import sys
from pathlib import Path

# Ensure local src/ is importable before any mdxlate imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mdxlate.client import make_client


def test_make_client_openai_default():
    """Test make_client with default openai provider."""
    client = make_client(provider="openai", api_key="test-key")
    
    assert client is not None
    assert client.api_key == "test-key"


def test_make_client_openai_with_base_url():
    """Test make_client with custom base URL for openai."""
    client = make_client(
        provider="openai",
        api_key="test-key",
        base_url="https://custom.openai.com/v1"
    )
    
    assert client is not None
    assert client.api_key == "test-key"
    assert client.base_url == "https://custom.openai.com/v1"


def test_make_client_openai_from_env(monkeypatch):
    """Test make_client reads OPENAI_API_KEY from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key-123")
    
    client = make_client(provider="openai")
    
    assert client is not None
    assert client.api_key == "env-key-123"


def test_make_client_openrouter():
    """Test make_client with openrouter provider."""
    client = make_client(provider="openrouter", api_key="or-key")
    
    assert client is not None
    assert client.api_key == "or-key"
    assert client.base_url == "https://openrouter.ai/api/v1"


def test_make_client_openrouter_custom_base_url():
    """Test make_client with custom base URL for openrouter."""
    client = make_client(
        provider="openrouter",
        api_key="or-key",
        base_url="https://custom.openrouter.com/v1"
    )
    
    assert client is not None
    assert client.api_key == "or-key"
    assert client.base_url == "https://custom.openrouter.com/v1"


def test_make_client_openrouter_from_env(monkeypatch):
    """Test make_client reads OPEN_ROUTER_API_KEY from environment."""
    monkeypatch.setenv("OPEN_ROUTER_API_KEY", "or-env-key-456")
    
    client = make_client(provider="openrouter")
    
    assert client is not None
    assert client.api_key == "or-env-key-456"
    assert client.base_url == "https://openrouter.ai/api/v1"
