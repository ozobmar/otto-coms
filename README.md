# otto-coms

Unified cross-platform voice client for Otto — STT, TTS, wake word, compose mode.

## Overview

Real-time speech-to-text pipeline with voice activity detection (Silero VAD), transcription (faster-whisper), text-to-speech (edge-tts), and integration with otto-core for LLM responses.

## Features

- **Audio capture** — sounddevice with configurable device/gain/sample rate
- **VAD** — Silero VAD for speech detection with configurable thresholds
- **STT** — faster-whisper (CPU int8 or GPU float16)
- **TTS** — edge-tts with sentence-level streaming and barge-in
- **Wake word** — OpenWakeWord ONNX models
- **Compose mode** — Buffer multiple utterances before sending
- **Output handlers** — Console, clipboard, file, WebSocket, Otto API
- **Service discovery** — Finds otto-core via mDNS (otto-common)

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Linux
# or: source .venv/Scripts/activate  # Windows
pip install -e ".[all]"
```

## Run

```bash
./run.sh --outputs console clipboard
./run.sh --outputs otto-api --compose
```

## Echo Server (testing)

```bash
./tools/run_echo_server.sh
# Then in another terminal:
./run.sh --outputs otto-api --otto-url http://localhost:8080
```

## Configuration

Copy `config.default.yaml` to `config.yaml` and edit. CLI args override config values.

## API Contract

otto-coms communicates with otto-core via HTTP:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Server health status |
| `/text-prompt` | POST | Send text, receive LLM response |
| `/modules` | GET | List loaded modules |

## Deployment

Deployed to **otto-coms-01** (192.168.86.210) at `/opt/otto/otto-coms/`.
