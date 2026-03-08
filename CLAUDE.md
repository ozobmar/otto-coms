# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

otto-voice is a real-time voice client for the Otto ecosystem. It captures audio, detects speech (Silero VAD), transcribes (faster-whisper), and routes text through configurable output handlers. Supports TTS responses (edge-tts) with barge-in, wake word detection (OpenWakeWord), and compose mode for buffering multi-utterance inputs.

Deployed to **otto-coms-01** (192.168.86.210) at `/opt/otto/otto-voice/`.

## Commands

```bash
# Install
python -m venv .venv && source .venv/Scripts/activate  # Windows
pip install -e ".[all]"

# Run
./run.sh --outputs console clipboard
./run.sh --outputs otto-api --compose
otto-voice --list-devices          # show audio input devices
otto-voice -v --outputs console    # verbose/debug mode

# Test
pytest -v
pytest tests/test_foo.py::test_name  # single test

# Echo server (local API testing)
python tools/echo_server.py --port 8080
```

## Architecture

**Pipeline flow**: `AudioCapture -> VAD -> STT -> [VoiceCommands] -> [ComposeBuffer] -> OutputHandlers`

The pipeline (`pipeline.py`) is a single async loop that pulls audio chunks from a queue and processes them through each stage. `PipelineState` tracks pause/resume, listening mode (continuous vs wake word), and TTS barge-in state.

### Key modules

- **`cli.py`** — Entry point. Parses args, detects hardware, applies auto-config for STT model/device/compute type, then launches the pipeline.
- **`config.py`** — Nested dataclasses mirroring `config.default.yaml`. Config loads from YAML with CLI overrides applied on top via `apply_cli_overrides()`.
- **`pipeline.py`** — Async orchestrator. Wires up all components and runs the main audio processing loop. Handles barge-in logic, wake word state transitions, and compose mode routing.
- **`handlers/`** — Output handlers implement `OutputHandler` ABC (`start`, `emit`, `stop`). Registry in `handlers/__init__.py` maps string names to classes. Each handler receives the full `Config` in its constructor.
- **`processing/`** — VAD (`silero-vad`), STT (`faster-whisper`), wake word (`openwakeword`), and hardware detection.
- **`buffer/compose.py`** — Compose mode: buffers utterances, supports undo/redo, optional LLM cleanup before sending.
- **`tts/engine.py`** — edge-tts with sentence-level streaming. Queued speak calls, interrupt support for barge-in.
- **`llm/`** — LLM clients (Ollama, Claude) used by compose mode for text cleanup. Created via `create_llm_client()` factory.
- **`commands/`** — Voice command detection and hotkey bindings (Shift+L toggle).
- **`platform/`** — Platform-specific utilities: audio feedback beeps, input simulation.

### Configuration precedence

`config.default.yaml` -> `config.yaml` (user override, gitignored) -> CLI arguments

### Dependencies

- **`otto-common`** — Shared Otto library (service discovery via mDNS), installed from git.
- STT uses `ctranslate2<=4.4.0` pin due to compatibility constraints.
- GPU support (`torch`) and wake word (`openwakeword`) are optional extras.

## Conventions

- Python 3.11+, async/await throughout the pipeline
- Australian English in documentation
- Float32 audio pipeline end-to-end (16kHz, mono)
- `auto` values in STT config trigger hardware-based auto-detection at startup
