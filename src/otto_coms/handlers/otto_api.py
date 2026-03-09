"""Otto API output handler — sends transcriptions to Otto server."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from otto_coms.handlers import OutputHandler

if TYPE_CHECKING:
    from otto_coms.config import Config

logger = logging.getLogger(__name__)


class OttoApiOutput(OutputHandler):
    """Sends transcribed text to Otto's /text-prompt endpoint.

    Supports sync mode (wait for response) and async mode (fire and forget
    with callback — requires server support).
    """

    def __init__(self, config: Config) -> None:
        self._url = config.output_settings.otto_api.url.rstrip("/")
        self._timeout = config.output_settings.otto_api.timeout
        self._return_audio = config.output_settings.otto_api.return_audio
        self._voice = config.output_settings.otto_api.voice
        self._provider = config.output_settings.otto_api.provider
        self._tx_mode = config.transmission.mode
        self._callback_host = config.transmission.async_callback_host
        self._callback_port = config.transmission.async_callback_port
        self._client: httpx.AsyncClient | None = None
        self._on_response: callable | None = None

    def set_response_callback(self, callback: callable) -> None:
        """Set a callback for handling responses (used by pipeline for TTS)."""
        self._on_response = callback

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=self._timeout)

        # Health check
        try:
            resp = await self._client.get(f"{self._url}/health")
            resp.raise_for_status()
            logger.info("Connected to Otto at %s", self._url)
        except Exception as e:
            logger.warning("Otto health check failed: %s (will retry on send)", e)

    async def emit(self, text: str, metadata: dict | None = None) -> None:
        if self._client is None:
            logger.error("Otto API client not initialised")
            return

        try:
            payload = {
                "prompt": text,
                "provider": self._provider,
            }

            resp = await self._client.post(
                f"{self._url}/text-prompt",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            response_text = data.get("response", "")
            if response_text:
                print(f"<< {response_text}")
                if self._on_response is not None:
                    self._on_response(data)

        except httpx.TimeoutException:
            logger.error("Otto API timeout after %ds", self._timeout)
        except httpx.HTTPStatusError as e:
            logger.error("Otto API error: %s", e.response.status_code)
        except Exception as e:
            logger.error("Otto API error: %s", e)

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
