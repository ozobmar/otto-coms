"""Voice Activity Detection using Silero VAD."""

from __future__ import annotations

import enum
import logging
import time
from collections import deque

import numpy as np
import torch

from otto_coms.config import VADConfig

logger = logging.getLogger(__name__)


class VADState(enum.Enum):
    SILENCE = "silence"
    SPEAKING = "speaking"
    TRAILING_SILENCE = "trailing_silence"


class VADProcessor:
    """Silero VAD wrapper with a speech state machine.

    Feeds audio chunks through VAD. When speech is detected, buffers audio.
    After trailing silence, emits the complete speech segment as a single
    float32 numpy array.
    """

    def __init__(self, config: VADConfig, sample_rate: int = 16000) -> None:
        self.config = config
        self.sample_rate = sample_rate
        self._state = VADState.SILENCE
        self._buffer: list[np.ndarray] = []
        self._silence_start: float = 0.0
        self._speech_start: float = 0.0
        self._model = None
        self._last_prob: float = 0.0

        chunk_ms = 32
        pad_chunks = max(1, int(config.speech_pad_ms / chunk_ms))
        self._pre_buffer: deque[np.ndarray] = deque(maxlen=pad_chunks)
        logger.debug("Speech pad: %dms (%d chunks)", config.speech_pad_ms, pad_chunks)

    @property
    def state(self) -> VADState:
        return self._state

    @property
    def last_probability(self) -> float:
        return self._last_prob

    def _load_model(self) -> None:
        if self._model is not None:
            return
        from silero_vad import load_silero_vad
        self._model = load_silero_vad(onnx=True)
        logger.info("Silero VAD loaded")

    def _get_speech_prob(self, audio: np.ndarray) -> float:
        self._load_model()
        audio_tensor = torch.from_numpy(audio)
        prob = self._model(audio_tensor, self.sample_rate).item()
        self._last_prob = prob
        return prob

    def process_chunk(self, chunk: np.ndarray) -> np.ndarray | None:
        """Process one audio chunk through the VAD state machine.

        Returns the complete speech segment when speech ends, or None.
        """
        prob = self._get_speech_prob(chunk)
        now = time.monotonic()
        is_speech = prob >= self.config.threshold

        if self._state == VADState.SILENCE:
            if is_speech:
                self._state = VADState.SPEAKING
                self._speech_start = now
                self._buffer = list(self._pre_buffer) + [chunk]
                self._pre_buffer.clear()
                logger.debug("Speech started (prob=%.2f, prepended %d chunks)", prob, len(self._buffer) - 1)
            else:
                self._pre_buffer.append(chunk)

        elif self._state == VADState.SPEAKING:
            self._buffer.append(chunk)
            if not is_speech:
                self._state = VADState.TRAILING_SILENCE
                self._silence_start = now

        elif self._state == VADState.TRAILING_SILENCE:
            self._buffer.append(chunk)
            if is_speech:
                self._state = VADState.SPEAKING
            else:
                elapsed_ms = (now - self._silence_start) * 1000
                if elapsed_ms >= self.config.silence_duration_ms:
                    speech_duration_ms = (now - self._speech_start) * 1000
                    if speech_duration_ms >= self.config.min_speech_duration_ms:
                        segment = np.concatenate(self._buffer)
                        self._buffer = []
                        self._state = VADState.SILENCE
                        self._reset_vad_state()
                        logger.debug("Speech segment: %.1fs", len(segment) / self.sample_rate)
                        return segment
                    else:
                        logger.debug("Discarded short speech (%.0fms)", speech_duration_ms)
                        self._buffer = []
                        self._state = VADState.SILENCE
                        self._reset_vad_state()

        return None

    def _reset_vad_state(self) -> None:
        if self._model is not None:
            self._model.reset_states()

    def reset(self) -> None:
        """Full reset — clear buffers and state."""
        self._buffer = []
        self._pre_buffer.clear()
        self._state = VADState.SILENCE
        self._reset_vad_state()
