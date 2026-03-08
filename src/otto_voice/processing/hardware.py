"""GPU/CUDA detection and model recommendation."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from otto_voice.platform import get_system_ram_gb

logger = logging.getLogger(__name__)


@dataclass
class HardwareInfo:
    has_cuda: bool = False
    gpu_name: str = ""
    vram_gb: float = 0.0
    compute_capability: tuple[int, int] = (0, 0)
    ram_gb: float = 0.0
    cuda_validated: bool = False

    def __str__(self) -> str:
        if self.has_cuda:
            cc = f"{self.compute_capability[0]}.{self.compute_capability[1]}"
            return (f"GPU: {self.gpu_name}, VRAM: {self.vram_gb:.1f}GB, "
                    f"CC: {cc}, CUDA validated: {self.cuda_validated}")
        return f"CPU only, RAM: {self.ram_gb:.1f}GB"


def detect_hardware() -> HardwareInfo:
    """Detect GPU and system capabilities."""
    info = HardwareInfo(ram_gb=get_system_ram_gb())

    try:
        import torch
        if torch.cuda.is_available():
            info.has_cuda = True
            info.gpu_name = torch.cuda.get_device_name(0)
            info.vram_gb = torch.cuda.get_device_properties(0).total_mem / (1024 ** 3)
            info.compute_capability = torch.cuda.get_device_capability(0)
    except ImportError:
        try:
            import ctranslate2
            if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
                info.has_cuda = True
                info.gpu_name = "NVIDIA GPU (details unavailable without torch)"
        except Exception:
            pass
    except Exception as e:
        logger.debug("CUDA detection failed: %s", e)

    if info.has_cuda:
        info.cuda_validated = validate_cuda_runtime()

    return info


def validate_cuda_runtime() -> bool:
    """Test that CUDA actually works with CTranslate2."""
    try:
        import ctranslate2
        supported = ctranslate2.get_supported_compute_types("cuda")
        if not supported:
            return False
        logger.debug("CTranslate2 CUDA compute types: %s", supported)
        return True
    except Exception as e:
        logger.warning("CUDA validation failed: %s. Falling back to CPU.", e)
        return False


def recommend_settings(hw: HardwareInfo) -> dict[str, str]:
    """Recommend model, device, and compute_type based on hardware."""
    if hw.has_cuda and hw.cuda_validated:
        if hw.vram_gb >= 10:
            return {"model": "medium", "device": "cuda", "compute_type": "float16"}
        if hw.vram_gb >= 6:
            return {"model": "small", "device": "cuda", "compute_type": "float16"}
        if hw.vram_gb >= 3:
            return {"model": "small", "device": "cuda", "compute_type": "int8"}
        return {"model": "base", "device": "cuda", "compute_type": "int8"}

    if hw.ram_gb >= 8:
        return {"model": "small", "device": "cpu", "compute_type": "int8"}
    return {"model": "base", "device": "cpu", "compute_type": "int8"}
