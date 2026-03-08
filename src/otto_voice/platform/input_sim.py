"""Cross-platform keyboard/paste simulation."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def press_enter() -> None:
    """Simulate Enter key press."""
    from pynput.keyboard import Controller, Key
    kb = Controller()
    kb.press(Key.enter)
    kb.release(Key.enter)


def simulate_paste() -> None:
    """Simulate Ctrl+V (or Cmd+V on macOS) to paste at cursor position."""
    from otto_voice.platform import IS_MACOS

    try:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        modifier = Key.cmd if IS_MACOS else Key.ctrl
        kb.press(modifier)
        kb.press("v")
        kb.release("v")
        kb.release(modifier)
    except Exception as e:
        logger.warning("pynput paste failed (%s), trying pyautogui", e)
        try:
            import pyautogui
            mod = "command" if IS_MACOS else "ctrl"
            pyautogui.hotkey(mod, "v")
        except Exception as e2:
            logger.error("Paste simulation failed: %s", e2)
