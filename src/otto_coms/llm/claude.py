"""Claude API client for LLM text cleanup."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from otto_coms.llm import SYSTEM_PROMPT

if TYPE_CHECKING:
    from otto_coms.config import ClaudeConfig

logger = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(self, config: ClaudeConfig) -> None:
        self._base_url = config.base_url.rstrip("/")
        self._model = config.model

    async def cleanup(self, raw_text: str) -> str:
        url = f"{self._base_url}/v1/messages"
        payload = {
            "model": self._model,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": raw_text},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data.get("content", [])
                if content and isinstance(content, list):
                    result = content[0].get("text", "").strip()
                    return result if result else raw_text
                return raw_text
        except Exception as e:
            logger.warning("Claude cleanup failed, using raw text: %s", e)
            return raw_text
