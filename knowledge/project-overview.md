# Project Overview — Crystal Companion

**Crystal Companion** is a native Python + PySide6 desktop AI companion application, version **0.2.0**. It is a local-first, transparent-orb desktop assistant — not a website wrapped in a browser frame. It runs entirely on the user's machine with Ollama handling text generation locally, and an optional local Hugging Face Phonon model for spoken answers.

## Core facts

- **Name:** Crystal Companion
- **Package name:** `crystal-companion`
- **Version:** `0.2.0`
- **Status:** Development prototype / v0.2.0
- **Primary target OS:** Windows 10 / Windows 11
- **Entry point:** `python -m crystal_agent` (or `.\run.ps1`)
- **Python requirement:** >=3.11
- **Git branch:** `main`
- **Git user:** `maal0lan`

## What it is (and isn't)

| Is | Is not |
|---|---|
| Native desktop Qt app | Browser wrapper / Electron |
| Transparent, frameless, always-on-top orb | Full-screen web application |
| Local Ollama inference | Cloud LLM API (default endpoint is loopback) |
| Optional local Phonon TTS | SaaS text-to-speech |
| Read-only, allowlisted local file tools | Autonomous shell / arbitrary computer control |
| Persistent local SQLite history | Remote-synced chat history |
| Tray-icon background operation | Installer / signed executable |

## Key differentiators from the browser reference

A browser-version backend was used as reference material, but this is a clean native desktop foundation. Capabilities advertised by the browser prototype — streaming, microphone input, MCP, GPU shader refraction — are **not** yet complete here. See [[roadmap-and-future-work]] and [[security-and-privacy]].

## Related notes

- [[architecture]] — system architecture, threading, state, trust boundaries
- [[module-map]] — every module and its responsibility
- [[ui-system]] — orb, chat, settings, tray, diagnostics, glass rendering
- [[agent-and-inference]] — Ollama agent, prompt construction, model selection
- [[tools-and-permissions]] — FolderTools, read-only file access, security model
- [[tts-system]] — Phonon text-to-speech, audio playback
- [[history-and-persistence]] — SQLite history, JSON settings
- [[configuration-reference]] — all settings and defaults
- [[setup-and-deployment]] — installation, setup.ps1, run.ps1
- [[security-and-privacy]] — security checklist, trust boundaries
- [[roadmap-and-future-work]] — roadmap, known limitations
- [[development-guide]] — testing, development recommendations