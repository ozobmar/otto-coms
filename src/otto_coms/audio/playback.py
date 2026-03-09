"""Audio playback for TTS responses."""

from __future__ import annotations

import io
import logging
import wave

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioPlayback:
    """Plays WAV audio data through speakers."""

    def __init__(self, device: int | None = None) -> None:
        self._device = device

    def play_wav(self, wav_data: bytes) -> None:
        """Play WAV audio data. Blocking call."""
        try:
            with wave.open(io.BytesIO(wav_data), "rb") as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frames = wf.readframes(wf.getnframes())

            if sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            else:
                dtype = np.int16

            audio = np.frombuffer(frames, dtype=dtype)

            if channels > 1:
                audio = audio.reshape(-1, channels)
                audio = audio.mean(axis=1).astype(dtype)

            audio_float = audio.astype(np.float32) / np.iinfo(dtype).max

            try:
                sd.play(audio_float, samplerate=sample_rate, device=self._device, blocking=True)
            except sd.PortAudioError:
                logger.warning("Playback failed at %d Hz, retrying at 44100 Hz", sample_rate)
                sd.play(audio_float, samplerate=44100, device=self._device, blocking=True)

        except Exception as e:
            logger.error("Audio playback error: %s", e)

    def play_numpy(self, audio: np.ndarray, sample_rate: int = 16000) -> None:
        """Play a numpy float32 array."""
        try:
            sd.play(audio, samplerate=sample_rate, device=self._device, blocking=True)
        except Exception as e:
            logger.error("Audio playback error: %s", e)
