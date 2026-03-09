"""Space management — list, create, open, close conversation spaces on Otto."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class SpaceManager:
    """Manages conversation spaces via Otto's API."""

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._active_space: str | None = None

    @property
    def active_space(self) -> str | None:
        return self._active_space

    async def list_spaces(self) -> list[dict] | None:
        """List all conversation spaces."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base_url}/sessions")
                resp.raise_for_status()
                data = resp.json()
                spaces = data.get("sessions", [])
                return spaces
        except Exception as e:
            logger.error("Failed to list spaces: %s", e)
            return None

    async def create_space(self, name: str, space_type: str = "default") -> bool:
        """Create a new conversation space."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/sessions/create",
                    json={"name": name, "type": space_type},
                )
                resp.raise_for_status()
                self._active_space = name
                logger.info("Created space: %s", name)
                return True
        except Exception as e:
            logger.error("Failed to create space: %s", e)
            return False

    async def open_space(self, name: str) -> bool:
        """Open an existing conversation space."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/sessions/open",
                    json={"name": name},
                )
                resp.raise_for_status()
                self._active_space = name
                logger.info("Opened space: %s", name)
                return True
        except Exception as e:
            logger.error("Failed to open space: %s", e)
            return False

    async def close_space(self) -> bool:
        """Close the current conversation space."""
        if self._active_space is None:
            logger.info("No active space to close")
            return False

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/sessions/close",
                    json={"name": self._active_space},
                )
                resp.raise_for_status()
                logger.info("Closed space: %s", self._active_space)
                self._active_space = None
                return True
        except Exception as e:
            logger.error("Failed to close space: %s", e)
            return False
