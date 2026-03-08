"""LLM client protocol and factory."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from otto_voice.config import LLMConfig

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a text cleanup assistant. The user dictated text using speech-to-text. "
    "Your job is to produce the FINAL intended message by:\n"
    "1. When the user corrects themselves (e.g. 'make it 10, no 20, actually 25'), "
    "keep ONLY the final value (25). Earlier values are mistakes — discard them entirely.\n"
    "2. Remove filler words, false starts, and repetitions.\n"
    "3. Fix grammar and punctuation.\n"
    "4. Preserve the user's intent and tone — do not add, reword, or embellish.\n"
    "Return ONLY the cleaned final text. No explanations, no preamble."
)


@runtime_checkable
class LLMClient(Protocol):
    async def cleanup(self, raw_text: str) -> str:
        """Clean up raw speech buffer into coherent prompt."""
        ...


def create_llm_client(config: LLMConfig) -> LLMClient | None:
    """Create an LLM client based on config, or None if disabled."""
    if not config.enabled:
        return None

    if config.provider == "ollama":
        from otto_voice.llm.ollama import OllamaClient
        client = OllamaClient(config.ollama)
        logger.info("LLM: Ollama at %s (model=%s)", config.ollama.base_url, config.ollama.model)
        return client
    elif config.provider == "claude":
        from otto_voice.llm.claude import ClaudeClient
        client = ClaudeClient(config.claude)
        logger.info("LLM: Claude at %s (model=%s)", config.claude.base_url, config.claude.model)
        return client
    else:
        logger.warning("Unknown LLM provider: %s", config.provider)
        return None
