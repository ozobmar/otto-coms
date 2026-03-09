"""Cross-platform audio feedback — beeps and tones."""

from __future__ import annotations

import logging
import math
import struct

import numpy as np

from otto_coms.platform import IS_WINDOWS

logger = logging.getLogger(__name__)


def _generate_tone(frequency: float, duration_ms: int, volume: float = 0.3) -> np.ndarray:
    """Generate a sine wave tone as float32 numpy array at 16kHz."""
    sample_rate = 16000
    n_samples = int(sample_rate * duration_ms / 1000)
    t = np.arange(n_samples, dtype=np.float32) / sample_rate
    tone = (volume * np.sin(2.0 * math.pi * frequency * t)).astype(np.float32)
    return tone


def _play_tone(frequency: float, duration_ms: int) -> None:
    """Play a simple tone, cross-platform."""
    if IS_WINDOWS:
        try:
            import winsound
            winsound.Beep(int(frequency), duration_ms)
            return
        except Exception:
            pass

    # Cross-platform fallback: use sounddevice
    try:
        import sounddevice as sd
        tone = _generate_tone(frequency, duration_ms)
        sd.play(tone, samplerate=16000, blocking=True)
    except Exception as e:
        logger.debug("Could not play tone: %s", e)


def beep_start() -> None:
    """Low blip — transcription starting."""
    _play_tone(500, 50)


def beep_done() -> None:
    """Mid beep — transcription complete."""
    _play_tone(800, 80)


def beep_sent() -> None:
    """High chirp — text sent."""
    _play_tone(1200, 40)


def beep_wake_word() -> None:
    """Rising two-tone — wake word detected."""
    _play_tone(440, 100)
    _play_tone(880, 100)


def beep_error() -> None:
    """Falling tone — error occurred."""
    _play_tone(400, 150)
    _play_tone(200, 200)
