"""TTS audio playback — plays responses from Otto."""

from __future__ import annotations

import asyncio
import logging

from otto_coms.audio.playback import AudioPlayback

logger = logging.getLogger(__name__)


class TTSPlayer:
    """Manages TTS audio playback in a non-blocking way."""

    def __init__(self, output_device: int | None = None) -> None:
        self._playback = AudioPlayback(device=output_device)
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the playback consumer loop."""
        self._task = asyncio.create_task(self._playback_loop())
        logger.info("TTS player started")

    async def _playback_loop(self) -> None:
        """Consume and play queued audio."""
        loop = asyncio.get_running_loop()
        while True:
            try:
                wav_data = await self._queue.get()
                await loop.run_in_executor(None, self._playback.play_wav, wav_data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("TTS playback error: %s", e)

    def enqueue(self, wav_data: bytes) -> None:
        """Add audio to the playback queue."""
        try:
            self._queue.put_nowait(wav_data)
        except asyncio.QueueFull:
            logger.warning("TTS playback queue full, dropping audio")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
