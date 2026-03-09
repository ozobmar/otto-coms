"""Global hotkey listener for controlling the pipeline."""

from __future__ import annotations

import logging
from typing import Callable

from pynput import keyboard

logger = logging.getLogger(__name__)


class HotkeyManager:
    """Listens for global hotkeys and dispatches actions."""

    def __init__(self) -> None:
        self._bindings: list[tuple[frozenset[str], Callable[[], None], str]] = []
        self._pressed: set[str] = set()
        self._listener: keyboard.Listener | None = None

    def bind(self, keys: set[str], action: Callable[[], None], description: str) -> None:
        """Register a hotkey binding.

        Keys should be lowercase strings: 'shift', 'ctrl', 'alt', or single chars.
        """
        self._bindings.append((frozenset(keys), action, description))
        logger.info("Hotkey registered: %s -> %s", "+".join(sorted(keys)), description)

    def start(self) -> None:
        """Start the global hotkey listener in a background thread."""
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()
        logger.info("Hotkey listener started")

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _normalise_key(self, key: keyboard.Key | keyboard.KeyCode) -> str | None:
        if isinstance(key, keyboard.Key):
            mapping = {
                keyboard.Key.shift: "shift",
                keyboard.Key.shift_l: "shift",
                keyboard.Key.shift_r: "shift",
                keyboard.Key.ctrl: "ctrl",
                keyboard.Key.ctrl_l: "ctrl",
                keyboard.Key.ctrl_r: "ctrl",
                keyboard.Key.alt: "alt",
                keyboard.Key.alt_l: "alt",
                keyboard.Key.alt_r: "alt",
                keyboard.Key.enter: "enter",
                keyboard.Key.space: "space",
                keyboard.Key.esc: "esc",
                keyboard.Key.tab: "tab",
            }
            return mapping.get(key)
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char.lower()
        return None

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        normalised = self._normalise_key(key)
        if normalised is None:
            return
        self._pressed.add(normalised)
        self._check_bindings()

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        normalised = self._normalise_key(key)
        if normalised is None:
            return
        self._pressed.discard(normalised)

    def _check_bindings(self) -> None:
        for keys, action, description in self._bindings:
            if keys == self._pressed:
                logger.info("Hotkey triggered: %s", description)
                action()
