# Live Transcription Demo (fasthtml + Whisper)

This repository contains a small demo app that uses OpenAI Whisper to transcribe short audio chunks sent from a browser. The project is containerized and includes a `docker-compose.yml` to build and run the app as a service named `voice-app` bound to port `5001`.

## What’s in this repo

- `app.py` — the FastHTML app that records from the browser, uploads short audio chunks, converts them with `ffmpeg`, and transcribes with Whisper.
- `Dockerfile` — builds a Python 3.11 image, installs system deps (`git`, `ffmpeg`), Python deps, and exposes port 5001.
- `docker-compose.yml` — defines one service `voice-app` that builds the image and maps host port `5001` to container port `5001`.
- `requirements.txt` — Python dependencies (including `fasthtml`, `whisper`, `torch`, and `httpx`).

## Prerequisites

- Docker Desktop installed and running on Windows. Ensure you can run Docker commands from PowerShell.
- Docker Compose (comes bundled with modern Docker Desktop as the `docker compose` v2 subcommand).
- An OpenAI API key if you plan to use any OpenAI services; this demo reads `OPENAI_API_KEY` from the environment and passes it into the container.

Note: The container uses Whisper (the open-source model) and `ffmpeg`. The Dockerfile installs `ffmpeg` so you don't need it on the host for basic runs.

## Environment variable

The compose file expects an environment variable named `OPENAI_API_KEY` to be available when you run `docker compose up` so it can be injected into the container. If you don't have one, you can still run the app but some features that depend on the key may not work.

In PowerShell, export the variable for the current session like this:

```powershell
$env:OPENAI_API_KEY = "your_api_key_here"
```

Or, to run just for a single command (recommended when testing), prefix the `docker` command like this:

```powershell
$env:OPENAI_API_KEY = "your_api_key_here"; docker compose up --build
```

## Basic Docker Compose commands (PowerShell)

All commands below assume your current working directory is the project root (the directory that contains `docker-compose.yml`).

- Build and start the service (foreground):

```powershell
docker compose up --build
```

This builds the image (if needed) and starts the `voice-app` service. The container listens on port `5001`. After startup you can open [http://localhost:5001](http://localhost:5001) in your browser.

- Start in detached/background mode:

```powershell
docker compose up -d --build
```

- Stop services started by compose:

```powershell
docker compose down
```

- View logs (live):

```powershell
docker compose logs -f
```

- View logs for the `voice-app` service only:

```powershell
docker compose logs -f voice-app
```

- Rebuild the image and restart (when you change `requirements.txt`, `Dockerfile`, or `app.py`):

```powershell
docker compose up -d --build --force-recreate
```

- Remove containers and images produced by compose (cleanup):

```powershell
docker compose down --rmi local --volumes --remove-orphans
```

## How to use the app

1. Start the compose stack (see commands above).
2. Open your browser to: [http://localhost:5001](http://localhost:5001)
3. Click "Start Recording" and allow microphone access in the browser.
4. The page will record short chunks (~2s), upload them to the `/stream` endpoint, and append transcribed text to the transcript area.

The app uses `ffmpeg` inside the container to convert browser audio to a WAV file before passing it to Whisper. The Docker image already includes `ffmpeg`.

## Troubleshooting

- Permission / Microphone denied in browser: Ensure the page ([http://localhost:5001](http://localhost:5001)) is allowed to use your microphone and that you’re using a secure context (localhost is treated as secure).
- Port in use: If port `5001` is already in use on your machine, either stop the process using it or edit `docker-compose.yml` to change the mapping (e.g. `5002:5001`).
- Slow startup or large wheel downloads: The first Docker build may take time because `torch` / Whisper dependencies can be large. Be patient on the first run.
- Model download: Whisper (and PyTorch) may download model weights at first run when `whisper.load_model(...)` is called. If you need smaller memory/space usage, edit `app.py` to use a smaller model (e.g., `tiny`) or modify the Dockerfile to cache models externally.
- Missing OPENAI_API_KEY: If you see issues related to `OPENAI_API_KEY`, set it in PowerShell as shown above before `docker compose up`.

## Development tips

- Iterating on Python code: After code changes, rebuild the image and restart the service:

```powershell
docker compose up -d --build
```

- Workaround for faster Python development: Instead of rebuilding the image every time, you can run the service with a bind mount to the host source directory. Example (not in the current compose file):

```yaml
services:
  voice-app:
    build: .
    volumes:
      - ./:/app
    ports:
      - "5001:5001"
```

Then you can edit `app.py` locally and restart just the container without re-building the image.

## Files changed/added

- `README.md` — this file (project overview and Docker Compose instructions).

## Final notes

If you want, I can also:

- Add a `docker-compose.override.yml` for development with a bind mount.
- Add a small healthcheck to `docker-compose.yml`.
- Add a one-line PowerShell script to set the env var and launch compose.

If you'd like any of those, tell me which and I’ll add them.
