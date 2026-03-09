"""File output handler."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import IO, TYPE_CHECKING

from otto_coms.handlers import OutputHandler

if TYPE_CHECKING:
    from otto_coms.config import Config

logger = logging.getLogger(__name__)


class FileOutput(OutputHandler):
    def __init__(self, config: Config) -> None:
        self._path = config.output_settings.file.path
        self._mode = "a" if config.output_settings.file.mode == "append" else "w"
        self._file: IO[str] | None = None

    async def start(self) -> None:
        self._file = open(self._path, self._mode, encoding="utf-8")
        logger.info("Writing transcriptions to %s", self._path)

    async def emit(self, text: str, metadata: dict | None = None) -> None:
        if self._file is None:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._file.write(f"[{timestamp}] {text}\n")
        self._file.flush()

    async def stop(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
