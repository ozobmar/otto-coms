"""Wake word detection using openwakeword."""

from __future__ import annotations

import logging

import numpy as np

from otto_coms.config import WakeWordConfig

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Detects wake words in audio using openwakeword."""

    def __init__(self, config: WakeWordConfig) -> None:
        self.config = config
        self._model = None
        self._available = False

    def load(self) -> bool:
        """Load the wake word model. Returns True if successful."""
        try:
            from openwakeword.model import Model
            self._model = Model(
                wakeword_models=[self.config.model],
                inference_framework="onnx",
            )
            self._available = True
            logger.info("Wake word model loaded: %s (threshold=%.2f)",
                        self.config.model, self.config.threshold)
            return True
        except ImportError:
            logger.warning("openwakeword not installed — wake word disabled. "
                           "Install with: pip install openwakeword")
            return False
        except Exception as e:
            logger.error("Wake word model load failed: %s", e)
            return False

    @property
    def available(self) -> bool:
        return self._available

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """Check if a wake word was detected in the audio chunk.

        Expects float32 audio at 16kHz. Chunk should be ~80ms (1280 samples).
        Returns True if wake word detected above threshold.
        """
        if not self._available or self._model is None:
            return False

        # openwakeword expects int16 audio
        audio_int16 = (audio_chunk * 32767).astype(np.int16)

        prediction = self._model.predict(audio_int16)

        for model_name, score in prediction.items():
            if score >= self.config.threshold:
                logger.info("Wake word detected: %s (score=%.3f)", model_name, score)
                self._model.reset()
                return True

        return False

    def reset(self) -> None:
        """Reset the wake word model state."""
        if self._model is not None:
            self._model.reset()
