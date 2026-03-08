"""Console output handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from otto_voice.handlers import OutputHandler

if TYPE_CHECKING:
    from otto_voice.config import Config


class ConsoleOutput(OutputHandler):
    def __init__(self, config: Config) -> None:
        pass

    async def start(self) -> None:
        pass

    async def emit(self, text: str, metadata: dict | None = None) -> None:
        print(f">> {text}")

    async def stop(self) -> None:
        pass
