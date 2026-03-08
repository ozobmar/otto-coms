"""Microphone audio capture via sounddevice."""

from __future__ import annotations

import asyncio
import logging

import numpy as np
import sounddevice as sd

from otto_voice.config import AudioConfig

logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures audio from microphone and pushes float32 chunks to an async queue."""

    def __init__(self, config: AudioConfig, queue: asyncio.Queue[np.ndarray]) -> None:
        self.config = config
        self.queue = queue
        self._stream: sd.InputStream | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            logger.debug("Audio status: %s", status)
        chunk = indata[:, 0].copy()
        if self.config.gain != 1.0:
            chunk *= self.config.gain
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self.queue.put_nowait, chunk)

    async def start(self) -> None:
        """Open the audio stream."""
        self._loop = asyncio.get_running_loop()
        self._stream = sd.InputStream(
            device=self.config.device,
            samplerate=self.config.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.config.block_size,
            latency="high",
            callback=self._callback,
        )
        self._stream.start()
        device_info = sd.query_devices(self.config.device or sd.default.device[0])
        logger.info("Listening on: %s", device_info["name"])

    async def stop(self) -> None:
        """Close the audio stream."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
