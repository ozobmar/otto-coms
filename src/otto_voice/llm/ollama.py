"""Ollama REST client for LLM text cleanup."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from otto_voice.llm import SYSTEM_PROMPT

if TYPE_CHECKING:
    from otto_voice.config import OllamaConfig

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, config: OllamaConfig) -> None:
        self._base_url = config.base_url.rstrip("/")
        self._model = config.model

    async def cleanup(self, raw_text: str) -> str:
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
            "system": SYSTEM_PROMPT,
            "prompt": raw_text,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                result = data.get("response", "").strip()
                return result if result else raw_text
        except Exception as e:
            logger.warning("Ollama cleanup failed, using raw text: %s", e)
            return raw_text
