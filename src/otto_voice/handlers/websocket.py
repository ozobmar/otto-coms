"""WebSocket server output handler."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import websockets

from otto_voice.handlers import OutputHandler

if TYPE_CHECKING:
    from otto_voice.config import Config

logger = logging.getLogger(__name__)


class WebSocketOutput(OutputHandler):
    def __init__(self, config: Config) -> None:
        self._host = config.output_settings.websocket.host
        self._port = config.output_settings.websocket.port
        self._clients: set[websockets.WebSocketServerProtocol] = set()
        self._server: websockets.WebSocketServer | None = None

    async def start(self) -> None:
        self._server = await websockets.serve(
            self._handler, self._host, self._port,
        )
        logger.info("WebSocket server listening on ws://%s:%d", self._host, self._port)

    async def _handler(self, ws: websockets.WebSocketServerProtocol) -> None:
        self._clients.add(ws)
        logger.info("WebSocket client connected (%d total)", len(self._clients))
        try:
            async for _ in ws:
                pass
        finally:
            self._clients.discard(ws)
            logger.info("WebSocket client disconnected (%d total)", len(self._clients))

    async def emit(self, text: str, metadata: dict | None = None) -> None:
        if not self._clients:
            return

        msg = json.dumps({
            "text": text,
            "language": (metadata or {}).get("language"),
            "duration": (metadata or {}).get("duration"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        tasks = [client.send(msg) for client in self._clients.copy()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.debug("WebSocket send error: %s", r)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
