"""TTS voice listing and selection via Otto API."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


async def list_voices(base_url: str, timeout: int = 10) -> list[str]:
    """Query available TTS voices from Otto."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{base_url.rstrip('/')}/voices")
            resp.raise_for_status()
            data = resp.json()
            return data.get("voices", [])
    except Exception as e:
        logger.error("Failed to list voices: %s", e)
        return []
