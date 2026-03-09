"""Audio level calibration — measure noise floor and speech levels."""

from __future__ import annotations

import asyncio
import logging
import time

import numpy as np

logger = logging.getLogger(__name__)


class CalibrationResult:
    """Results from a calibration run."""

    def __init__(
        self,
        noise_floor_db: float,
        speech_level_db: float,
        recommended_vad_threshold: float,
        recommended_gain: float,
        device_name: str = "",
    ) -> None:
        self.noise_floor_db = noise_floor_db
        self.speech_level_db = speech_level_db
        self.snr_db = speech_level_db - noise_floor_db
        self.recommended_vad_threshold = recommended_vad_threshold
        self.recommended_gain = recommended_gain
        self.device_name = device_name

    def __repr__(self) -> str:
        return (
            f"CalibrationResult(noise={self.noise_floor_db:.1f}dB, "
            f"speech={self.speech_level_db:.1f}dB, SNR={self.snr_db:.1f}dB, "
            f"vad_threshold={self.recommended_vad_threshold:.2f}, "
            f"gain={self.recommended_gain:.2f})"
        )


def rms_db(audio: np.ndarray) -> float:
    """Calculate RMS level in dB."""
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 1e-10:
        return -100.0
    return 20.0 * np.log10(rms)


async def measure_noise_floor(
    queue: asyncio.Queue[np.ndarray],
    duration_seconds: float = 5.0,
    sample_rate: int = 16000,
    block_size: int = 512,
) -> float:
    """Measure ambient noise floor from audio queue. Returns dB level."""
    samples_needed = int(duration_seconds * sample_rate)
    collected = []
    total_samples = 0

    while total_samples < samples_needed:
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
            collected.append(chunk)
            total_samples += len(chunk)
        except asyncio.TimeoutError:
            break

    if not collected:
        return -60.0

    audio = np.concatenate(collected)
    return rms_db(audio)


async def measure_speech_level(
    queue: asyncio.Queue[np.ndarray],
    duration_seconds: float = 5.0,
    sample_rate: int = 16000,
) -> float:
    """Measure speech level from audio queue. Returns dB level."""
    samples_needed = int(duration_seconds * sample_rate)
    collected = []
    total_samples = 0

    while total_samples < samples_needed:
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
            collected.append(chunk)
            total_samples += len(chunk)
        except asyncio.TimeoutError:
            break

    if not collected:
        return -20.0

    audio = np.concatenate(collected)
    return rms_db(audio)


def compute_recommendations(noise_db: float, speech_db: float) -> tuple[float, float]:
    """Compute recommended VAD threshold and gain from measurements.

    Returns (vad_threshold, gain).
    """
    snr = speech_db - noise_db

    # VAD threshold: lower if SNR is poor, higher if excellent
    if snr > 30:
        vad_threshold = 0.55
    elif snr > 20:
        vad_threshold = 0.50
    elif snr > 10:
        vad_threshold = 0.40
    else:
        vad_threshold = 0.35

    # Gain: boost if speech level is low
    if speech_db < -30:
        gain = 2.5
    elif speech_db < -24:
        gain = 1.8
    elif speech_db < -18:
        gain = 1.2
    else:
        gain = 1.0

    return vad_threshold, gain
