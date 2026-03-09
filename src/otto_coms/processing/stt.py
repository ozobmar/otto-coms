"""Speech-to-text using faster-whisper."""

from __future__ import annotations

import logging
import os
import time

import numpy as np

from otto_coms.config import STTConfig

logger = logging.getLogger(__name__)


class STTEngine:
    """Wrapper around faster-whisper for transcription."""

    def __init__(self, config: STTConfig) -> None:
        self.config = config
        self._model = None

    def load(self) -> None:
        """Load the Whisper model. Call once at startup."""
        from otto_coms.platform import register_cudnn_dlls
        register_cudnn_dlls()

        from faster_whisper import WhisperModel

        logger.info(
            "Loading Whisper model '%s' on %s (%s)...",
            self.config.model, self.config.device, self.config.compute_type,
        )
        t0 = time.monotonic()

        cpu_threads = self.config.cpu_threads or os.cpu_count() or 4
        logger.info("Using %d CPU threads", cpu_threads)

        try:
            self._model = WhisperModel(
                self.config.model,
                device=self.config.device,
                compute_type=self.config.compute_type,
                cpu_threads=cpu_threads,
            )
        except Exception as e:
            if self.config.device == "cuda":
                logger.warning("CUDA load failed (%s), falling back to CPU", e)
                self.config.device = "cpu"
                self._model = WhisperModel(
                    self.config.model,
                    device="cpu",
                    compute_type="int8",
                )
            else:
                raise

        elapsed = time.monotonic() - t0
        logger.info("Model loaded in %.1fs", elapsed)

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str | None:
        """Transcribe a float32 audio segment. Returns text or None."""
        if self._model is None:
            raise RuntimeError("STT model not loaded. Call load() first.")

        t0 = time.monotonic()
        segments, info = self._model.transcribe(
            audio,
            beam_size=self.config.beam_size,
            language=self.config.language,
            vad_filter=False,
        )

        texts = []
        for seg in segments:
            texts.append(seg.text.strip())

        text = " ".join(texts).strip()
        elapsed = time.monotonic() - t0

        if text:
            audio_dur = len(audio) / sample_rate
            ratio = elapsed / audio_dur if audio_dur > 0 else 0
            logger.info(
                "STT: %.1fs audio -> %.1fs (%.1fx) | %s",
                audio_dur, elapsed, ratio, text[:80],
            )
            return text

        return None
