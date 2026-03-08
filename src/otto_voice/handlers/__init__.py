"""Output handler base class and registry."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from otto_voice.config import Config


class OutputHandler(abc.ABC):
    """Base class for output handlers."""

    @abc.abstractmethod
    async def start(self) -> None:
        """Initialise the output handler."""

    @abc.abstractmethod
    async def emit(self, text: str, metadata: dict | None = None) -> None:
        """Emit transcribed text."""

    @abc.abstractmethod
    async def stop(self) -> None:
        """Clean up resources."""


def create_outputs(config: Config) -> list[OutputHandler]:
    """Create output handlers based on config."""
    from otto_voice.handlers.clipboard import ClipboardOutput
    from otto_voice.handlers.console import ConsoleOutput
    from otto_voice.handlers.file import FileOutput
    from otto_voice.handlers.websocket import WebSocketOutput
    from otto_voice.handlers.otto_api import OttoApiOutput

    registry: dict[str, type[OutputHandler]] = {
        "console": ConsoleOutput,
        "file": FileOutput,
        "clipboard": ClipboardOutput,
        "websocket": WebSocketOutput,
        "otto-api": OttoApiOutput,
    }

    handlers = []
    for name in config.outputs:
        cls = registry.get(name)
        if cls is None:
            raise ValueError(f"Unknown output handler: {name}")
        handlers.append(cls(config))

    return handlers
