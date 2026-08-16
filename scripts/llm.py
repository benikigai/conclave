"""LLM provider selection shared by the Conclave query paths."""

import os
from typing import Any

import anthropic

SUPPORTED_PROVIDERS = ("ollama", "anthropic")


def _provider_from_env() -> str:
    provider = os.environ.get("CONCLAVE_PROVIDER", "ollama").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(f"Unsupported CONCLAVE_PROVIDER={provider!r}; use {supported}")
    return provider


DEFAULT_PROVIDER = _provider_from_env()
OLLAMA_BASE_URL = os.environ.get(
    "CONCLAVE_OLLAMA_URL",
    "http://100.121.115.33:11434",
).rstrip("/")


def model_for_provider(provider: str) -> str:
    """Return an operator override or the provider's tested default model."""
    override = os.environ.get("CONCLAVE_MODEL", "").strip()
    if override:
        return override
    if provider == "ollama":
        return "qwen3.8:27b-q8-64k"
    if provider == "anthropic":
        return "claude-sonnet-4-6"
    raise ValueError(f"Unsupported provider: {provider}")


DEFAULT_MODEL = model_for_provider(DEFAULT_PROVIDER)


def create_client(provider: str = DEFAULT_PROVIDER) -> anthropic.Anthropic:
    if provider == "ollama":
        return anthropic.Anthropic(base_url=OLLAMA_BASE_URL, api_key="ollama")
    if provider == "anthropic":
        return anthropic.Anthropic()
    raise ValueError(f"Unsupported provider: {provider}")


def create_async_client(
    provider: str = DEFAULT_PROVIDER,
) -> anthropic.AsyncAnthropic:
    if provider == "ollama":
        return anthropic.AsyncAnthropic(base_url=OLLAMA_BASE_URL, api_key="ollama")
    if provider == "anthropic":
        return anthropic.AsyncAnthropic()
    raise ValueError(f"Unsupported provider: {provider}")


def response_text(response: Any) -> str:
    """Extract final text while ignoring Ollama/Anthropic thinking blocks."""
    texts = [
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text" and getattr(block, "text", "")
    ]
    if not texts:
        raise RuntimeError("LLM response did not contain a text block")
    return "\n".join(texts)
