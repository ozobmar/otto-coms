"""Clipboard + paste output handler with optional auto-send."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from otto_coms.handlers import OutputHandler
from otto_coms.platform.input_sim import press_enter, simulate_paste

if TYPE_CHECKING:
    from otto_coms.config import Config

logger = logging.getLogger(__name__)


class ClipboardOutput(OutputHandler):
    def __init__(self, config: Config) -> None:
        self._paste = config.output_settings.clipboard.paste
        self._paste_delay = config.output_settings.clipboard.paste_delay_ms / 1000.0
        self._auto_send = config.output_settings.clipboard.auto_send
        self._auto_send_delay = config.output_settings.clipboard.auto_send_delay_ms / 1000.0
        self._send_task: asyncio.Task | None = None

    async def start(self) -> None:
        import pyperclip
        pyperclip.copy("")
        logger.info(
            "Clipboard output ready (paste=%s, auto_send=%s, delay=%.1fs)",
            self._paste, self._auto_send, self._auto_send_delay,
        )

    async def emit(self, text: str, metadata: dict | None = None) -> None:
        import pyperclip

        self._cancel_auto_send()
        pyperclip.copy(text)

        if self._paste:
            await asyncio.sleep(self._paste_delay)
            simulate_paste()

        if self._auto_send:
            self._send_task = asyncio.create_task(self._auto_send_after_delay())

    def _cancel_auto_send(self) -> None:
        if self._send_task is not None and not self._send_task.done():
            self._send_task.cancel()
            self._send_task = None

    async def _auto_send_after_delay(self) -> None:
        try:
            await asyncio.sleep(self._auto_send_delay)
            logger.debug("Auto-send: sending Enter after %.1fs delay", self._auto_send_delay)
            press_enter()
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        self._cancel_auto_send()
